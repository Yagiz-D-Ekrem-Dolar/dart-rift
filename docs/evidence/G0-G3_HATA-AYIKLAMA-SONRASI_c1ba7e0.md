# Dört kapı — hata ayıklama turu sonrası yeniden kanıt

- **Commit:** `c1ba7e0`
- **İş:** SLURM 1448947 · TRUBA kolyoz12 · NVIDIA H100 80GB HBM3
- **Süre:** 01:30:55 · **Durum:** COMPLETED · **Çıkış kodu:** 0:0
- **İlgili:** ADR-0029, KAYIT-016, `docs/EKSIKLER.md` §0

---

## Neden bu koşu var

FAZ 3 daha önce "0 hata" diye sunulmuştu. O iddia yanlıştı. Aktif bir hata
ayıklama turu **altı kusur** buldu (ADR-0029); ikisi bilimsel sonucu birinci
mertebede bozuyordu. Bu belge, altı düzeltmenin **hepsi uygulandıktan sonra**
dört kapının yeniden geçtiğinin kaydıdır.

## Sonuç tablosu

| aşama | sonuç |
|---|---|
| Hasar durum ölçümü (`dbg_damage2.py`) | ✅ `DUZELDI` (rc=0) |
| Düzeltilen Y0 testi (tek başına) | ✅ 13 geçti (rc=0) |
| Turda eklenen tüm testler | ✅ 114 geçti (rc=0) |
| **Tam test takımı** | ✅ **639 geçti / 0 kaldı** (14:51) |
| **Kırmızı takım** | ✅ **14/14 TEMİZ** |
| **G0** | ✅ **GEÇTİ** (rc=0) |
| **G1** | ✅ **GEÇTİ** (rc=0) |
| **G2** | ✅ **GEÇTİ** (rc=0) |
| **G3** | ✅ **GEÇTİ 7/7** (rc=0) |
| Kapsam | **%96,5** (eşik %85, tüm paket, GPU dahil) |

**28 kriterin tamamı geçti.** Açık kusur, `xfail` ve kanıtlanamayan kriter yok.

## Düzeltmelerin kanıtı

### 1. Hasar artık durumu bozmuyor

Aynı ölçüm, düzeltme öncesi ve sonrası (`D = 0.5` sabit, hiçbir fiziksel
evrim yok — yani `S` sabit kalmalı):

| | önce (iş 1446269) | sonra (iş 1448947) |
|---|---|---|
| başlangıç | 1,000000e+07 | 1,000000e+07 |
| 1./2./3./4. `_eval()` | 5,0e+06 / 2,5e+06 / 1,25e+06 / 6,25e+05 | **1,000000e+07** (sabit) |
| 5 adım sonra | **4,88e+03** | **1,000000e+07** |
| `S_eff` (taşınan) | — | **5,000000e+06** (her seferinde) |

1000 katlık sapma kapandı. `S` artık durum, `S_eff` taşınan gerilme.

### 2. Krater çıkarıcı düzensiz cisimde doğru (RT9)

> *"düzensiz cisim (88×87×65 m): küresel referans kratersiz cisimde 9.12 m
> HAYALİ krater ve bilinen 8 m çukuru 17.63 m gösteriyor; çarpma öncesi
> referansla hayali 0.00e+00 m ve gerçek ölçüm 8.69 m (hata %8.7)"*

### 3. β duyarlılığı iki eksende de gerçekten ölçülüyor (RT10)

> *"yarıçap ekseni 0.2189, hız ekseni (1. senaryoda) 0.0000 — hız eşiği orada
> ÖLÜ olduğu için ayrı senaryoyla kanıtlandı: yayılım 0.3209, beta
> [1.735, 1.633, 1.414] eşikle monoton azalıyor (True)"*

### 4. Parçacık başına Y0 sonucu değiştiriyor (iş 1448928 ile ölçüldü)

| kol | Y0_ort | plastik iş |
|---|---|---|
| hepsi-zayıf | 1,0000e+04 | 1,459238e+07 J |
| heterojen | 2,3565e+06 | **1,890912e+09 J** |
| hepsi-güçlü | 1,0000e+07 | 1,264309e+10 J |

Heterojen değer iki homojen sınırın **tam arasında** — çekirdek herhangi bir
skaler kullansaydı sınırlardan birine otururdu.

## Yapısal önlemler (kusur *sınıfını* kapatır)

- `tests/test_solver_idempotence.py` — `_eval()` durumu değiştirmez (saflık
  değişmezi; hasar kapalı / açık / hepsi açık, üç yol).
- `cpu_reference/solid_ref.py` artık hasar **döngüsünü** içeriyor;
  `TestDamageCross` GPU↔CPU'yu 10 adım karşılaştırıyor — **CPU ve CUDA'da
  ayrı ayrı geçti.** Bu referans daha önce **yoktu**; kusurun yaşadığı boşluk
  tam olarak buydu.
- G3 C5 ve RT9/RT10 artık *neyin iş gördüğünü* ayrı ayrı şart koşuyor:
  `radius_axis_active`, `speed_axis_active`, `reference_is_spherical`,
  `target_radius_estimated`.

## Determinizm

Sahne karması `6d6f1d10eaff64e2…` — iki bağımsız ortamda birebir aynı
(Linux/CPython 3.10.15/numpy 1.26.4 ve Windows/CPython 3.12.10/numpy 2.5.1).
Altın hash dosyaları her iki platformu da kayıtlı tutuyor (RT1, RT13).

## Ne iddia ediliyor, ne edilmiyor

**İddia edilen:** `c1ba7e0` commit'inde, TRUBA H100'de, 28 kapı kriterinin
tamamı ve 14 kırmızı-takım maddesinin tamamı geçti; 639 test, 0 başarısız.

**İddia EDİLMEYEN:** "kusursuz". Bu turun kendisi, aynı tabloya (627 test, G3
7/7, kırmızı takım 14/14, kapsam %97) bakıp "0 hata" demenin yanlış olduğunu
gösterdi. Altı kusurun hepsi **kapsanan satırlardaydı** — ne testler ne de
kapsama onları bulabilirdi. Kapı geçmek, kusursuzluğun değil, **o kriterlerin**
kanıtıdır.

Bilerek açık bırakılanlar `docs/EKSIKLER.md` "Açık kalanlar" bölümünde:
mermi çözünürlüğü (ADR-0026), gereken simüle süre, krater çıkarıcıda
`x_reference`'ın isteğe bağlı olması, ve hasar modelinde Weibull
parametrelerinin global olması.
