```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 007
============================================================

**Tarih**       : 28.07.2026
**Saat**        : 06:10 – 18:00 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: TRUBA/ARF-ACC (kolyoz9, kolyoz23 — H100)

## BUGÜNKÜ HEDEF

FAZ 1 ve FAZ 2 kapı kanıtlarını TRUBA'da üretmek.

## SONUÇ — HER İKİ KAPI DA GEÇİLDİ

| Kapı | Koşu | Düğüm | Commit | Sonuç |
|---|---|---|---|---|
| G1 | 1426162 | kolyoz9 | `4dfd83c` | **GEÇTİ** (8/8) |
| G1 | 1426596 | kolyoz23 | `a3ecd2e` | **GEÇTİ** (8/8, yeniden üretim) |
| G2 | 1426596 | kolyoz23 | `a3ecd2e` | **GEÇTİ** (7/7) |

pytest: 360 geçti / 0 kaldı (14:02). İş çıkış kodu 0:0, süre 41:22.

G1'in iki farklı düğümde koşulup sekiz ölçütün kanıt sayılarının **birebir
aynı** çıkması, sonucun düğüme bağlı bir tesadüf olmadığını gösteriyor.

### G2 kanıt sayıları

| Ölçüt | Kanıt | Eşik |
|---|---|---|
| C1 objektiflik | S eş-dönme hatası %1,66 (Jaumann kapalıyken %200) | — |
| C2 elastik dalga | 4458 m/s vs teorik 4593 → %2,96, hata azalıyor | %3 |
| C2 Taylor | L/L0 = 0,731; Y0 2× → 0,824; **enerji %0,083** | bant 0,60–0,80; %1,5 |
| C3 crush | P_tepe gözenekli/katı = 0,28; alpha_min = 1,207 | — |
| C4 yerçekimi | 20 yörünge: E hatası 2,4e-07, yarıçap drifti 1,3e-08 | — |
| C5 korunum | soğuk çöküş enerji %0,36; momentum 1,2e-17 | %1; 1e-6 |
| C6 ablasyon | beş modülün tamamı açılıp kapanıyor | — |

## BULGU — 41 dakikalık geçerli hesap, raporlama hatası yüzünden kaybedildi

İlk koşu (1426162) G1'i geçti ama G2'de çöktü:

```
TypeError: Object of type bool_ is not JSON serializable
scripts/run_g2_gate.py:198
```

Fiziğin tamamı doğru koşmuştu; düşen şey metrik dosyasının yazımıydı.
Doğrulama fonksiyonları NumPy dizileri üzerinde çalıştığı için `a > b` gibi
karşılaştırmalar Python `bool` yerine `np.bool_` üretiyor ve bu tip JSON'a
serileştirilemiyor. Kapı arızası gibi görünen şey aslında bir raporlama
kusuruydu.

`dartrift.reporting.write_metrics` yazıldı. Dönüştürücü bilinçli olarak
**dar** tutuldu: yalnızca NumPy skaler/dizilerini çevirir, tanımadığı tipte
`TypeError` fırlatır. Her şeyi `str()`'e çeviren geniş bir yakalayıcı, gerçek
bir tip hatasını kapı kanıtına sessizce gömerdi — kanıt dosyasında bu kabul
edilemez. `tests/test_reporting.py` altı testle sabitliyor; biri düz
`json.dumps`'ın aynı girdide gerçekten düştüğünü gösteriyor, yani test boş
değil.

## DEĞERLENDİRME

Üç günlük döngünün özeti: FAZ 0 → G0, FAZ 1 → G1, FAZ 2 → G2 kanıtla geçildi.
Kapı mekanizması bu süreçte üç kez işe yaradı ve her seferinde **yerelde
görünmeyen** bir kusuru yakaladı:

1. NumPy sürüm farkı (yerel 2.x, TRUBA 1.26.4) — iki kernel testi.
2. Düğüm arızası (kolyoz13: `nvidia-smi` GPU'yu görüyor, Warp göremiyor).
3. NumPy `bool_` serileştirme — 41 dakikalık koşuyu düşürdü.

Hiçbiri fizik hatası değildi, ama üçü de "geçti" denmesini engelledi. Kanıtın
hedef ortamda üretilmesinin nedeni tam olarak bu.

## SIRADA

- FAZ 3 başlayabilir (G2 raporu: "FAZ 3 baslayabilir").
