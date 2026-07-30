```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 012
============================================================

**Tarih**       : 29.07.2026
**Saat**        : 11:00 – 20:00 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Yerel makine (RTX 3050) + TRUBA/ARF-ACC (H100/H200)

## BUGÜNKÜ HEDEF

FAZ 3'e geçmeden önce **ölçülmemiş her şeyi ölçmek**: uzun koşu kararlılığı,
ölçekte determinizm, tam fizik ölçeklemesi. Ve her şeyi hem yerelde hem
TRUBA'da koşmak.

## SONUÇ 1 — Uzun koşu kararlılığı: iyi (30 000 adım)

En büyük bilinmeyen buydu. Tam fizikli gerçek bir çarpma 30 000 adım koşuldu:

| adım | enerji hatası | momentum | kütle |
|---|---|---|---|
| 2 000 | %44,81548 | 7,3e-12 | 0,00e+00 |
| 10 000 | %44,80285 | 2,9e-10 | 0,00e+00 |
| 30 000 | %44,80285 | 1,7e-09 | 0,00e+00 |

**Drift oranı 15 kat adımda 1,00×** — enerji hatası hiç birikmiyor. Kütle bit
düzeyinde korunuyor. Zaman integrasyonu uzun koşuda kararlı; ADR-0020'nin
`O(dt)` tespiti bu ölçekte de geçerli.

## SONUÇ 2 — Determinizm ölçekte doğrulandı

G0'ın bit-eşit determinizm iddiası yalnızca küçük N'de sınanmıştı. Tam fizikle
(Barnes-Hut yerçekimi dahil) aynı koşu iki kez yapıldı: 19 416 ve 65 840
parçacıkta hash'ler **birebir aynı**. Bu, ensemble çıkarımının ön koşuludur.

## BULGU 1 — GPU Barnes-Hut hiç çalıştırılmamıştı

`mode="barnes_hut"` bugüne kadar hiçbir testte ya da kapıda çözücüye
verilmemişti. Üç yerden doğrulandı: config testi yalnızca alanın taşındığına
bakıyordu, katı çapraz testi `mode="direct"` kullanıyordu, ve
`validation/gravity.py` içinde GPU'ya hiç dokunulmuyordu. Yani G2 C4'ün
"yerçekimi doğrulandı" ifadesi **yalnızca CPU referansını** kapsıyordu.

Kod doğru çıktı (GPU↔CPU sapması 3,2e-16), ama sınanmayan yol bozulduğunda
kimse görmezdi. FAZ 3 için kritik: milyonlarca parçacıkta doğrudan N²
imkânsızdır, Barnes-Hut tek yoldur. Çapraz kontrol eklendi ve G2 C4'e şart
olarak bağlandı.

## BULGU 2 — Süreklilik + gözeneklilik tutarsız başlangıç kuruyordu

Uzun koşu testi %44,8 enerji hatası gösterdi. Modül ablasyonu kaynağı buldu:
gözeneklilik kapatılınca %0,56.

Kök neden: süreklilik modunda başlangıç yoğunluğu `rho0_katı` veriliyordu,
**alpha0'dan bağımsız**. P-α'da `P = P_katı(rho·alpha, u)/alpha` olduğundan
gerilmesiz başlangıç `rho = rho0_katı/alpha0` gerektirir. alpha0=1,5 için eski
kod malzemeyi **13,35 GPa** basınç altında başlatıyordu.

Görülmemesinin sebebi: bu **kombinasyon** hiçbir testte koşulmuyordu — çapraz
test gözenekliliği açıyor ama toplama yoğunluğu kullanıyor, Taylor süreklilik
kullanıyor ama gözenekliliği kapatıyor. İki modül ayrı ayrı doğruydu.

Düzeltmeden sonra %92,85 → %6,74.

## BULGU 3 (AÇIK KUSUR) — P-α sıkışma enerjisi defterde yok

Kalan hata **çözünürlükle büyüyor**: nside 32 → 44'te %6,74 → %15,81.
Gözenekliksiz durum ise sabit (%0,244 / %0,264). ADR-0020'deki ayırt edici
mantığın tersi: kesme hatası küçülür, bu büyüyor.

İç enerji ezilme sırasında **negatife** düşüyor (−5,97e11 J), ki gözenek
çökmesi malzemeyi ısıtmalıdır.

Şartname sözde-kodunu uygulamak (işi `u`'ya ekle) **denendi ve reddedildi**:
hata %1,88 yerine %20,33 oldu. Yani ADR-0008'in çifte-sayım gerekçesi
geçerli, basit düzeltme yanlış. Kusur P-α termodinamiğinin tam gözden
geçirilmesini gerektiriyor.

Eşik gevşetilmedi; kusur `xfail(strict=True)` ile izleniyor. **FAZ 3'e
gözenekli hedefle geçilmez** — Dimorphos bir moloz yığını ve gözeneklilik
çıkarımın asıl parametresidir.

## BULGU 4 — Yerçekimi ağacı adım içinde gereksiz yeniden kuruluyordu

`step()` içinde `_eval()` iki kez çağrılır ve ikincisinde konumlar
değişmemiştir; yine de ağaç Python'da yeniden kuruluyor ve 9 GPU dizisi
tahsis ediliyordu. Konum sürümü izlenerek önbelleklendi; sonuç **bit-eşit**.

Yerel hızlanma dürüstçe küçük (~1,0×) çünkü bu GPU'da ağaç eval'in %8'i.
H100'de GPU işi ~50 kat hızlı olduğundan ağaç baskın hale gelir.

Ölçüldü ve FAZ 3 için sınır olarak kaydedildi: tam fizikle (yerçekimi açık)
832 K parçacıkta adım **4 837 ms**, yerçekimi kapalı 1 M'de **287 ms** —
**17 kat** fark. Ağaç kurulumu ~O(N^1,2); 2 M parçacıkta tek kurulum ~29 s.

## BULGU 5 — EOS ilk kez DIŞ referansa karşı doğrulandı

Mevcut Tillotson testlerinin tamamı iç tutarlılık sınıyordu; bir birim hatası
hiçbirini düşürmezdi. Bazaltın deneysel Hugoniot'u türetildi:
**Us = 3123 + 1,65·up**, deneysel bant c0 ≈ 2600–3500 m/s, s ≈ 1,3–1,6.
Uyumlu. EOS'un **mutlak ölçeği** artık kanıtlı.

## KAPI DURUMU

Üç kapı da güncel kod üzerinde geçti (iş 1427564 / 1427565 / 1429629 /
1429630, `kolyoz23`, temiz ağaç): G0 8/8, G1 8/8, G2 7/7, kapsam %97,6,
kırmızı takım 6/6.

Yerel: **393 test geçti, 1 xfail** (ADR-0022 açık kusuru).

## DEĞERLENDİRME

Bugünün beş bulgusunun dördü **kombinasyon** ya da **sınanmayan yol**
kaynaklı: GPU Barnes-Hut hiç koşulmamıştı, süreklilik+gözeneklilik hiç
birlikte koşulmamıştı, gradyan düzeltmesi 1B'de sessizce kapalıydı, EOS hiç
dış referansa vurulmamıştı. Hiçbiri "kod yanlış yazılmış" değildi.

Ders: **kapsama modül başına değil kombinasyon başına düşünülmeli.** İki
doğru modül birlikte bozuk olabilir.

## SIRADA

- ADR-0022 açık kusuru: P-α termodinamiğinin gözden geçirilmesi (FAZ 3
  engelleyicisi).
- Yerçekimi ağacının GPU'da kurulması ya da K adımda bir yenilenmesi.
