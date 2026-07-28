```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 011
============================================================

**Tarih**       : 29.07.2026
**Saat**        : 06:30 – 11:00 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Yerel makine (RTX 3050) + TRUBA/ARF-ACC

## BUGÜNKÜ HEDEF

FAZ 0/1/2'yi kapatmak: açık kusuru kök nedenine kadar çözmek, baştan sona
denetim, ve kapıları güncel kod üzerinde yeniden kanıtlamak.

## BULGU 1 — Açık kusur çözüldü: enerji hatası sızıntı değil (ADR-0020)

KAYIT-009'da "enerji bütçesi ~300 adımı aşan koşularda tutmuyor" diye açık
bırakılmıştı. Kök neden bilinmiyordu ve bu önemliydi: şemada bir enerji
sızıntısı olsaydı FAZ 3'ün uzun koşuları anlamsız olurdu.

Ayırt edici ölçüm — sabit `n=32`, sabit `t_end`, yalnızca CFL değişti:

| CFL | adım | enerji hatası | önceki/bu | şok hatası |
|---|---|---|---|---|
| 0,2500 | 162 | %0,29502 | — | %1,14 |
| 0,1250 | 324 | %0,14303 | **2,06** | %1,13 |
| 0,0625 | 647 | %0,06904 | **2,07** | %1,12 |

dt yarılanınca hata **tam yarıya** iniyor → `O(dt¹)` kesme hatası. Sızıntı
olsaydı oran 1'e yakın kalırdı (adım sayısı arttığı için 1'in altına bile
düşerdi). Şok yarıçapı hatası aynı taramada sabit — iki hata kaynağı
birbirinden ayrıldı.

Varsayılan CFL değiştirilmedi; ilişki ölçülmüş olarak belgelendi. G1 kapısı
artık bu oranı her koşuda ölçüp raporluyor, böylece ölçüt "hata < %0,5"ten
keskin: gerçek bir sızıntı girerse oran 2'den 1'e düşer ve eşik hâlâ
geçiliyor olsa bile görünür.

## BULGU 2 — Gradyan düzeltmesi 1B'de HİÇ uygulanmıyordu (ADR-0019)

Denetimde `state.grad_correction_used` alanının **kaydedilip hiçbir yerde
denetlenmediği** görüldü. Ölçünce sebebi çıktı:

| Senaryo | Düzeltme uygulanan |
|---|---|
| 3B küre | %100 |
| 1B çubuk | **%0** |

Randles-Libersky düzeltmesi (ADR-0009) 1B senaryolarında hiç çalışmıyordu.
`_embed3` çift büyüklüklerini 3B'ye gömdüğü için `dim=1`'de y/z satırları
özdeş sıfırdı, `det(B)` her zaman 0 çıkıyordu.

Kritik ayrıntı: anlamlı bileşen **gayet iyi koşulluydu** — `B[0,0]` medyanı
0,9951. Matris tekil değildi; onu tekil gösteren şey boyut gömmesiydi.
Tekillik testi **olmayan bir tekilliği** raporluyordu.

Düzeltme sonrası elastik dalga: %2,9563 → **%2,8281** (marj 1,01× → 1,06×).
Rijit dönme (3B) değişmedi — alt-blok değişikliğinin `dim=3`'te etkisiz
olduğunu doğruluyor.

## BULGU 3 — ADR'nin söz verdiği rapor hiç üretilmiyordu

ADR-0011 §4: "Kinetik enerji oranı raporlanır — enerjinin gerçekten şoka
gidip gitmediğinin bağımsız ikinci göstergesi." İki faz boyunca
**uygulanmamış**: değer hesaplanıyor ama kapı raporuna hiç girmiyordu.

Ayrıca beklenen değer de yanlıştı: bu kurulumda hedef 0,28 değil ~0,19.
Ölçülen (n=32…112): 0,224 / 0,191 / 0,182 / 0,200 / 0,189 / 0,187. Sebep aynı
model-form seçimi — enerji noktasal değil, şok yarıçapının ~%32'si kadar bir
bölgeye ısı olarak konuyor. 0,28 **nokta** patlaması içindir.

## OPTİMİZASYON — GPU tarafında kazanç kalmadı (ölçüldü)

İkinci tur profil, GPU eval'inin tamamen iki komşu-gezinme çekirdeğinden
oluştuğunu gösterdi (Taylor nx=9, N=6348): `velocity_gradient_3d` %39,
`forces_solid_3d` %63.

Akla gelen optimizasyon ikisini tek gezinmede birleştirmekti. **Mümkün
değil**: `forces_solid_3d`, Balsara faktörünü hem `i` hem `j` için okuyor,
yani hiçbir kuvvet hesaplanmadan önce tüm parçacıkların `fbal`'ı hazır
olmalı. Bu küresel bağımlılık iki geçişi zorunlu kılıyor.

Çekirdek zinciri veri bağımlılıklarının izin verdiği en kısa sıra; komşu
sayısı ADR-0013, FP64 ADR-0002 ile kilitli. Yerel yavaşlık donanımsal
(RTX 3050'de FP64 = FP32/32).

## DENETİM — temiz çıkanlar

- Ölü kod yok; tanımlı her public fonksiyon kullanılıyor.
- Yer tutucu/`NotImplementedError` yok.
- Hata yutan `except` blokları yalnızca meşru yerlerde (opsiyonel git
  metadata, kırmızı takımın beklenen istisnaları).
- Public API'nin tamamı testlerde doğrudan ya da dolaylı geçiyor
  (`to_warp`/`from_warp` → `roundtrip_via_warp`, `momentum_wall_closure` →
  `run_sod`, `compute_continuity_rate` → `step_kdk`).
- README/ADR/izlenebilirlik bağlantılarının tamamı çözülüyor.

## DEĞERLENDİRME

Bugünkü üç bulgunun ortak noktası, dünkülerle aynı: **üretilen ama
denetlenmeyen şey bozulur.** `grad_correction_used` doğru hesaplanıyor ve
doğru cevabı (%0) veriyordu — kimse bakmadığı için iki faz boyunca görülmedi.
`kinetic_fraction` da öyle. Enerji kusuru ise "bilinen sınırlama" etiketiyle
kapatılmıştı; adı konmadan kapatılan bir kusurun gerçekte ne olduğu
bilinmiyor demektir.

Denetlenmeyen tanı, olmayan tanıdır.

## SIRADA

- Kapıların güncel HEAD üzerinde yeniden kanıtlanması.
