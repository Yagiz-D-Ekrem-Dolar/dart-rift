# KAYIT-038 — Kota dolunca **kod** yazıldı; ölçüm bekliyor (2026-08-08)

**Kapsam:** FAZ 4.4–4.7 · **Durum:** kod bitti, **ölçüm koşulmadı**
**Öncül:** [KAYIT-037](KAYIT-037_2026-08-08_bosluk3-kapandi.md),
[FAZ4-DURUM.md](../FAZ4-DURUM.md), [G4-OLCUTLERI.md](../G4-OLCUTLERI.md)

---

## 0. Engel — ve **kanıtlanması**

TRUBA hesabının grup CPU-dakika kotası doldu. Bunu *"dolmuş görünüyor"*
diye geçmedim; **sınadım**:

| kontrol | sonuç |
|---|---|
| `GrpTRESMins` (limit) | `cpu=7 200 000` |
| `GrpTRESRaw` (harcanan) | **`cpu=7 200 096`** |
| benim payım | `cpu=133 053` (`%1,8`) |
| erişilebilen hesap | **yalnızca** `egitimg16` / `cuda` / `normal` |
| donanım | **21 idle düğüm** — boş ama tahsis yok |
| **karar sınaması** | 1 dk, 16 çekirdek, 1 GPU, yalnızca `echo` → **`PENDING (AssocGrpCPUMinutesLimit)`** |

> Son satır belirleyici. *"Belki küçük bir iş sığar"* bir varsayımdı;
> ölçtüm, sığmıyor. Etrafından dolaşmadım — başka hesap yok, başka
> bölüm yok.

---

## 1. Ne yapıldı: **doğrulanabilen** işe geçildi

GPU'suz yapılabilecek her şey yapıldı. Yedi modül, 136 test:

| modül | ne yapar | test |
|---|---|---|
| `setup/refine.py` | A′'yı **DART sahnesine** bağlar | 8 |
| `validation/settling_time.py` | `β` durulma ölçütü | 13 |
| `validation/g4_gate.py` | kapıyı **kod** yargılar | 20 |
| `validation/g4_ozet.py` | ölçüm → kapı anahtarları | 13 |
| `inference/` (5 modül) | tasarım → vekil → posterior → G4-C | 35 |

Ve `faz4_zincir.sh`: `4.4 → 4.5 → 4.6 → 4.7`, tek komut.

### Yerelde **ölçülenler** (tahmin değil)

| büyüklük | değer |
|---|---|
| A′ DART sahnesinde tasarruf (`s = 7/3,5`, `r_iç = 25`) | **6,87×** |
| hedef kütle sapması | **2,25e-05** (G4-A3 eşiği `%0,5`) |
| çıkarım hattı kuru kipte: C1 / C2 / C3 | **%100 / 0,142 / 4,81×** |

---

## 2. İki tasarım kararı, ikisi de S9'un dersinden

### 2.1 Doğrulanamayan kod yolu **küçültüldü**

`ileri_kosu(θ) -> y` tek parça yazılabilirdi ama **hiç sınanamazdı**.
Üçe bölündü:

| parça | GPU'suz sınanır mı |
|---|---|
| `sahne_parametreleri` (`θ` → sahne argümanları) | **evet** |
| `gozlenebilirleri_cikar` (durum → üç sayı) | **evet** |
| `ileri_kosu` (ikisini bağlar + çözücü) | hayır |

En sinsi hata ortadaki parçadadır: `Y₀` yanlış alana yazılsa **bütün
tasarım aynı sahneyi** koşturur, vekil sabit bir yüzey öğrenir,
posterior önseli döndürür ve C2 düşer — ama **nedenini** anlamak saatler
alırdı. Şimdi bir test saniyede yakalıyor.

### 2.2 Kuru kip bir **kanıt değildir** — ve kod bunu biliyor

`faz46 --kuru` hattı analitik bir haritayla uçtan uca koşturur ve G4-C
geçer. Bu, çıkarım makinesinin çalıştığının kanıtıdır; **fiziğin**
değil. `g4_gate` çıktıda `kuru: true` görürse G4-C ölçütlerini
`koşulmadı` işaretler ve kapıyı **geçirmez**.

> Makineyi pahalı koşulardan **önce** doğrulamak, kota dolu olmasaydı da
> yapılması gereken şeydi.

---

## 3. Ölçümden **önce** yazılan eşikler

`docs/G4-OLCUTLERI.md` ölçümler koşulmadan yazıldı ve 13 testle koda
bağlandı. ADR-0040'ın gereği: sonradan yazılan eşik, ölçüme uydurulmuş
eşiktir.

Bir eşiğin gerekçesi özellikle önemli — **B1 (`%10`)**:

> ADR-0026 `β`'yı `±0,1` ayırt etmek istiyor; `β ~ 3` için bu `%3,3`.
> Sayısal belirsizlik fizikselin altında kalmalı, ama `%3,3`'ün altına
> inmek bu çözünürlükte gerçekçi değil. `%10` **bilinçli olarak gevşek**
> seçildi.

Bu gevşeklik **yazıldığı için** dürüsttür: G4 `%10` ile geçse bile ana
ürün henüz `±0,1` doğrulukta değildir.

Ve **B3 düşerse ADR-0041 düşer** — A′'nın seçilme gerekçesi tam olarak
buydu.

---

## 4. Yakalanan kusurlar — hepsi **kendi ölçüm düzeneğimde**

Bu oturumda 13 kusur çıktı; **hiçbiri çözücüde değildi**. Dördü bu
kayıtta ayrıca anılmalı:

| # | kusur | ders |
|---|---|---|
| 10 | eski plato ölçütü **"durulmadı" diyemiyordu** | her zaman bir sayı döndüren ölçüt, ölçüt değildir |
| 11 | "yarım-pencere sınavı **bağımsız**" — değil | iki sınav yazdım, birinin **gereksiz** olduğunu ölçtüm |
| 12 | `escape_speed_value` diye parametre **yok** | üç betikte birden; kota olsaydı üçü de düşerdi |
| 13 | koşucunun **kendi** `GOZLENEBILIRLER`'i vardı | ayrışmayı **sınamak** değil, **tek kaynağa indirmek** gerekiyordu |

### 11 neden öğretici

Modül başlığına *"iki bağımsız sınav"* yazmıştım. Altı şekilde ölçtüm;
yarım-pencere sınavı **hiçbirinde** tek başına yakalamıyor. Doğrusal
sürüklenmede oran **tam 2** ve bu cebirsel: pencere `w`, eğim `s` için
kayma `s·w`, yarım-pencere farkı `s·w/2`.

> Sınavı kaldırmadım (ucuz, ve `neden` metninde şekli gösteriyor) ama
> *"bağımsız ikinci güvence"* diye **sunmuyorum**. İki test o iddianın
> geri gelmesini engelliyor.

### 13 neden öğretici

Testim adların iki yerde de geçtiğini sınıyordu — yani **ayrışmayı
ölçmeye** çalışıyordu. 2. turun dersi bunun yanlış olduğunu söylüyor:
*"aynı büyüklük iki yerde yazılıysa er geç ayrışır."* Doğru çözüm
sınamak değil, **kaynağı teke indirmekti**. İndirildi.

### İki süreç hatası

1. Metin değiştiren betiğim eşleşmeyi **doğrulamadan** `"ok"` yazdı; iş
   `NameError` ile düştü. Artık her değiştirmede `assert` var ya da
   `Edit` kullanılıyor (eşleşmezse patlar).
2. Bir testte düzeltilen şeyin bozuk olduğunu **ölçmeden** iddia ettim
   (*"eski ölçüt çok erken bir anı durulma ilan eder"*). Ölçünce yanlış
   çıktı: eğim `0,4` için `0,9574` dönüyor — erken değil. Kusur
   erkenlik değil, **hiç reddedememekti**.

---

## 5. R4 kapandı

`DURUM-DEGERLENDIRMESI` §3'ün R4 riski: *"krater çıkarımı gerçek koşuya
bağlanınca `x_reference` **zorunlu** yapılmalı."*

Yapıldı: `gozlenebilirleri_cikar` `x_reference=None` görürse
`ValueError`. Verilmezse `crater_profile` cismi **küre** varsayar ve
şekli krater diye ölçer — kratersiz bir Dimorphos elipsoidinde
`66,76 m` çap ölçülmüştü.

---

## 6. Durum ve sırada

| # | iş | kod | ölçüm |
|---|---|---|---|
| 4.4 | DART'ta çözünürlük yakınsaması | ✔ | **✘** |
| 4.5 | gereken simüle süre | ✔ | **✘** |
| 4.6 | sentetik kurtarma | ✔ | **✘** (kuru ✔) |
| 4.7 | G4 kapısı | ✔ | **✘** |

Kapı raporu **üretildi** ve `GEÇİLEMEDİ` diyor; on ölçütün onu da
`koşulmadı`. Zincir işi kuyrukta (**1460742**); kota yenilenince
kendiliğinden koşacak.

> **FAZ 4 bitmedi ve FAZ 5'e geçilemez.** Kodu bitti; ölçümü kotaya
> bağlı.

---

## 7. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| bir engel **varsayılmaz**, sınanır | §0 — 1 dakikalık iş |
| doğrulanamayan kod yolu **küçültülür** | §2.1 |
| bir hattın çalışması, fiziğinin doğruluğu **değildir** | §2.2 |
| eşikler ölçümden **önce** yazılır | §3 |
| gevşek seçilen eşik **gevşek olduğu yazılarak** seçilir | §3 |
| ayrışma **sınanmaz**, kaynak **teke indirilir** | §4-13 |
| düzeltilen şeyin bozuk olduğu **ölçülür**, iddia edilmez | §4 (süreç 2) |
