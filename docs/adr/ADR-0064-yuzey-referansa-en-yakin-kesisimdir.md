# ADR-0064 — Yüzey, referansa **en yakın** kesişimdir; ADR-0062'nin kapısı **tek yanlı**

**Tarih:** 2026-11-01 · **Durum:** kabul (yan yana alan; varsayılan **bit-aynı**)
**Öncül:** [ADR-0061](ADR-0061-krater-penceresi-durum-basina-kurulur.md),
[ADR-0062](ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md),
[ADR-0063](ADR-0063-yuzey-icten-disa-taranir.md)
**Ölçüm:** iş `6892196` (TRUBA `debug`, **0 GPU**), commit `a799571`,
`scripts/tani_krater_kesisim_sayisi.py`
**Kayıt:** [KAYIT-094](../defter/KAYIT-094_2026-11-01_kesisim-sayisi-olculdu-ADR-0062-tek-yanli-cikti.md)

> **BU KARAR MÜHÜRLÜ `uretim66`'YA UYGULANMAZ.** Aşağıdaki seçim kuralı
> ve eşik tartışması **ölçüm görüldükten sonra** yazıldı. Kural 6 gereği
> sonuca bakılarak kurulan bir ölçüt, o sonucun ürettiği sayıları
> *düzeltmek* için kullanılamaz. Yeni sayı gerekiyorsa **yeni etiketle**
> (`enyakin7x`) ayrı bir kayıt kurulur; `ONKAYIT_HERA_KRATER_uretim66`
> **değiştirilmez**.

---

## 1. Bağlam — iki tarama yönü de **kör seçim** yapıyordu

KAYIT-091 §7 şunu yazmıştı: *"iki yön de aynı sınıfın hatasını yapıyor:
doğru kesişimi **doğrultuya** bakarak seçmek"*. `distan` yukarıdan inip
ilk kesişimi, `icten` (ADR-0063) içten çıkıp ilkini alıyor. Eksende
birden çok `phi = esik` kesişimi varsa ikisi de doğrultunun dayattığı
kesişimi alır — hangisinin **yüzey** olduğunu sormadan.

`13` nokta bu yüzden savunulamayan sayı veriyordu (idx 87'de `+36,49` m
derinlik; hedefin yarı eksenleri `58 – 88,5` m).

## 2. Ölçüm — kesişimler **sayıldı**, kapı önceden kilitliydi

`scripts/tani_krater_kesisim_sayisi.py`, tahmini ve iki kapısı
**koşudan önce** commit'lendi (`07d7bbb`).

**DENETİM KAPISI GEÇTİ:** referans (çarpılmamış) durumda eksende
kesişim `96/96` noktada **tek**. Yani tanının kendisi sağlam; bu kapı
KAYIT-092'de hipotezi çürüten kapının aynısıdır.

**AYIRT KAPISI GEÇTİ:** `AUC(kesişim sayısı; 13 vs 66) = 0,948`
(eşik `0,70`). Çok kesişim oranı: çapraz doğrulanan `66`'da
**`%4,5`**, tek tanılı `13`'te **`%92,3`**.

Belirleyici nicelik, eksende **referans yüzeye en yakın kesişimin**
ondan uzaklığıdır:

| küme | n | `|en yakın − referans|` ortanca | **maks** |
|---|---:|---:|---:|
| çapraz doğrulanan | 66 | `0,724` m | **`4,951` m** |
| tek tanılı | 13 | `4,438` m | `37,08` m |
| okunamayan | 17 | `18,84` m | `48,24` m |

Okunamayan `17` noktanın **en yakını bile** referanstan `6,05` m uzak.
Çapraz doğrulanan `66`'nın **en kötüsü** `4,951` m. Arada boşluk var ve
boşluk ölçülmüştür, seçilmemiştir.

## 3. Karar

### 3.1 Seçim kuralı — **parametresiz**

`_doluluk_kesisimi`, bir doğru üzerindeki **bütün** aşağı kesişimleri
toplar. `yon = "en_yakin"` kipinde yüzey, **aynı ışın üzerindeki
referans yüzeye en yakın** kesişimdir.

Bu kuralın **yeni bir uzunluk ölçeği yoktur**: karşılaştırma ölçütü
referans yüzeyin kendisidir ve o **nokta başına ölçülmüş** bir
niceliktir, ayarlanmış bir sabit değil. Doğrultuya bakarak seçmenin
yerine, cismin çarpılmamış hâline bakarak seçmek gelir.

### 3.2 **ADR-0062'nin kapısı tek yanlıdır** — bulgu

ADR-0062 şunu reddediyor: *merkezde son yüzey, referans yüzeyin bir
çekirdek desteği (`2h`) **üzerindeyse** derinlik ölçülemez.* Yani
yalnız **yukarı** sapmayı görüyor.

`icten`'in asıl kusuru **aşağı** sapmadır: tarama cismin **içindeki**
bir boşluğa düşerse yüzey referansın onlarca metre **altında** okunur
ve **hiçbir kapı bunu yakalamaz**. Ölçülen iki örnek:

| idx | eksendeki kesişimler (m) | referans | `icten` okuyor | yayımlanan "derinlik" |
|---:|---|---:|---:|---:|
| `87` | `22,5` · `107,0` | `59,63` | **`22,5`** | **`+36,49` m** |
| `6` | `27,2` · `86,7` · `131,8` | `59,57` | **`27,2`** | **`+28,61` m** |

İkisinde de referansa yakın **hiçbir** kesişim yok (`87`: en yakını
`37,08` m uzak; `6`: `27,17` m). Yani bu iki noktada yüzey
**konumlandırılamıyor** — sayı yerine red doğru cevaptır.

### 3.3 Seçim kuralı mevcut kapıyı **yeterli hâle getiriyor**

`en_yakin` seçimi uygulandığında `13` noktanın işaretleri değişiyor ve
**ADR-0062'nin var olan kapısı** çoğunu doğru reddediyor
(`derinlik = referans − seçilen`; negatif = yüzey referansın üstünde):

| idx | `derinlik` (m) | ADR-0062 (`2h = 1,4` m) |
|---:|---:|---|
| `6` | `−27,17` | **reddedilir** (üstte) |
| `49` | `−18,11` | **reddedilir** |
| `24` | `−5,66` | **reddedilir** |
| `0` | `−4,75` | **reddedilir** |
| `84` | `−3,26` | **reddedilir** |
| `85` | `−1,44` | **reddedilir** (sınırda) |
| `52` | `−0,33` | ölçülür |
| `45` | `+0,72` | ölçülür |
| `25` | `−0,79` | ölçülür |
| `14` | `+4,27` | ölçülür |
| `16` | `+4,44` | ölçülür |
| `19` | `+4,93` | ölçülür |
| `87` | **`+37,08`** | **KAÇIYOR** — §3.4 |

Yani seçim kuralı tek başına, **yeni bir eşik koymadan**, altı vakayı
mevcut kapıya düşürüp doğru reddediyor ve altı noktada fiziksel olarak
makul bir derinlik veriyor.

### 3.4 Aşağı yöndeki eşik **KONMUYOR** — ve niçin

Geriye tek nokta kalıyor: `87`, `+37,08` m. Simetrik bir kapı
(`derinlik > 2h` → red) onu yakalardı **ama** `14`/`16`/`19`'u da
(`+4,27`/`+4,44`/`+4,93`) yakalardı. Fizik simetrik değildir: malzeme
**aşağı kazılabilir** (gerçek krater), ama referans yüzeyin **üstüne
çıkıp** krater tabanı olamaz.

Aşağı yöndeki doğru eşik bu ölçümden **türetilemez**: `4,93` ile
`37,08` arasında herhangi bir sayı aynı sınıflamayı verir, ama o sayıyı
**bu veriye bakarak** seçmek tam olarak kural 6'nın yasakladığı şeydir.
Bu yüzden **eşik konmuyor**; `87` çapraz doğrulama gereği
**yayımlanmaz** olarak kalır ve sebebi artık biliniyor: *eksende
referansa yakın hiçbir kesişim yok.*

> Bir eşik uydurup `87`'yi de kurtarmak, kaydı `%7` daha dolu
> gösterirdi. Ölçümden türetilemeyen bir sayıyı koymamak, onu koymaktan
> daha değerlidir.

### 3.5 Varsayılan **değişmez**

`tarama` alanının varsayılanı `"distan"` kalır ve `distan`/`icten`
davranışı **bit-aynıdır**. `"en_yakin"` **yan yana** bir alandır
(ADR-0063'ün kurduğu desen).

## 4. Reddedilen seçenekler

| seçenek | niçin reddedildi |
|---|---|
| Simetrik `2h` kapısı | `14`/`16`/`19`'un gerçek kraterlerini de reddederdi (§3.4) |
| Aşağı eşiği `6` m koymak | boşluktan **seçilmiş** sayı; kural 6 ihlali (§3.4) |
| `tarama="bagli"` (bağlantılılık) | ölçüldü, `icten`'den farklı davranmıyor; **geri alınmıştı** (KAYIT-092 §4) |
| En dış kesişimi almak | `87`'de `107,0` m'yi, `6`'da `131,8` m'yi verirdi — ayrı ejekta yığını |
| `uretim66`'yı yeniden okuyup mührü güncellemek | **kural 6 ihlali.** Mühürün anlamı bu |

## 5. Geri alma koşulu

`en_yakin`, çapraz doğrulanan `66` noktanın **hiçbirinde** `distan`'ın
ölçtüğü sayıyı `1e-9` bağıl farktan fazla değiştirmemelidir — çünkü o
`66` noktada kesişim zaten **tek** (`%95,5`'inde) ve tek kesişimde
"en yakın" ile "ilk" **aynı** şeydir. Değiştirirse kip geri alınır ve
sebep KAYIT'a yazılır.

## 6. Etkilenmeyen yargılar

`krater_derinlik` ADR-0055 ile isteğe bağlıdır ve posteriora girmez.
`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), mühürlü spin ön kaydı (KAYIT-084) ve
mühürlü krater ön kaydı (`uretim66`, KAYIT-092) **etkilenmez**.
