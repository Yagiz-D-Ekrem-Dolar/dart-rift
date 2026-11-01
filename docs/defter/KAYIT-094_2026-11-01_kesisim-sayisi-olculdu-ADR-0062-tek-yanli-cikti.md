# KAYIT-094 — Kesişim sayısı ölçüldü; **ADR-0062'nin kapısı tek yanlı** çıktı

**Tarih:** 2026-11-01 · **Sıfır GPU** (TRUBA `debug`)
**İşler:** `6892196` (kesişim tanısı, **bitti**), `6892243` (96 noktada
`en_yakin`, kapıları önceden kilitli)
**Öncül:** [KAYIT-091](KAYIT-091_2026-10-28_icten-disa-tarama-olculdu-66-nokta-capraz-dogrulandi.md) §7,
[KAYIT-092](KAYIT-092_2026-11-01_doluluk-hipotezi-CURUDU-muhur-atildi-gec-dokum-gonderildi.md)
**Karar:** [ADR-0064](../adr/ADR-0064-yuzey-referansa-en-yakin-kesisimdir.md)

---

## 1. Tek cümle

Projenin asıl açık sorunu (`13` tek tanılı nokta) **çözüldü**: iki tarama
yönü de kesişimi **doğrultuya** bakarak seçiyordu; eksende kaç kesişim
olduğu sayıldı ve `AUC = 0,948` ile ayırt etti. Bulgu bundan büyük —
**ADR-0062'nin kapısı tek yanlıydı** ve `icten`'in cismin içindeki
boşluğa düşmesini hiçbir kapı yakalamıyordu.

## 2. Önce kapı, sonra ölçüm (kural 6)

Tahmin ve iki kapı `07d7bbb`'de, **koşudan önce** commit'lendi.

| kapı | eşik | ölçülen | sonuç |
|---|---|---|---|
| **DENETİM** — referansta kesişim tek mi | `≥ 90/96` | **`96/96`** | **GEÇTİ** |
| **AYIRT** — `AUC(kesişim sayısı; 13 vs 66)` | `≥ 0,70` | **`0,948`** | **GEÇTİ** |

Denetim kapısı burada da işini yaptı: çarpılmamış cisimde eksende
kesişim `96` noktanın **hepsinde** tek. Yani tanı sağlam. KAYIT-092'de
aynı kapı hipotezi **çürütmüştü** (`AUC = 0,203`, ters yön); burada
destekledi. Aynı makine, iki farklı cevap — bu yüzden kapı var.

| küme | n | ortanca kesişim | `>1` kesişim oranı |
|---|---:|---:|---:|
| çapraz doğrulanan | 66 | `1` | **`%4,5`** |
| tek tanılı | 13 | `2` | **`%92,3`** |
| okunamayan | 17 | `2` | `%64,7` |

## 3. Belirleyici nicelik: kesişimin **referanstan** uzaklığı

Kesişim sayısı ayırt ediyor, ama asıl bilgi **nerede** olduğunda:

| küme | n | `|en yakın − referans|` ortanca | **maks** |
|---|---:|---:|---:|
| çapraz doğrulanan | 66 | `0,724` m | **`4,951` m** |
| tek tanılı | 13 | `4,438` m | `37,08` m |
| okunamayan | 17 | `18,84` m | `48,24` m |

Çapraz doğrulanan `66`'nın **en kötüsü** `4,951` m; okunamayan `17`'nin
**en iyisi** `6,05` m. Arada boşluk var ve **ölçüldü, seçilmedi**.

Okunamayan `17`'nin hepsi referansın **üstünde** (`+6,05` … `+48,24`) —
yani ADR-0062'nin "ÖRTÜLÜ KRATER" reddi bağımsız bir yoldan
**doğrulandı**.

## 4. **Bulgu:** ADR-0062 yalnız bir yöne bakıyor

ADR-0062, son yüzey referansın `2h` **üzerindeyse** reddeder. `icten`'in
asıl kusuru ters yöndedir: tarama cismin **içindeki** boşluğa düşerse
yüzey referansın onlarca metre **altında** okunur ve **hiçbir kapı
yakalamaz**.

| idx | eksendeki kesişimler (m) | referans | `icten` okudu | yayımlanan "derinlik" |
|---:|---|---:|---:|---:|
| `87` | `22,5` · `107,0` | `59,63` | **`22,5`** | **`+36,49` m** |
| `6` | `27,2` · `86,7` · `131,8` | `59,57` | **`27,2`** | **`+28,61` m** |

İkisinde de referansa yakın **hiçbir** kesişim yok (`87`: en yakını
`37,08` m uzak). Yani bu iki noktada yüzey **konumlandırılamıyor** —
sayı yerine red doğru cevaptır. KAYIT-091 §7 bu iki sayıyı
"savunulamayan" diye işaretlemişti; sebebi artık **biliniyor**.

## 5. Çözüm: `tarama="en_yakin"` — yeni parametre **yok**

[ADR-0064](../adr/ADR-0064-yuzey-referansa-en-yakin-kesisimdir.md),
koddan **önce** yazıldı (`7493db8`). Bütün aşağı kesişimler toplanır ve
**aynı ışının referans yüzeyine** en yakın olanı seçilir. Ölçüt,
nokta başına **ölçülmüş** referans yüzeyin kendisidir — ayarlanmış bir
sabit değil.

Sentetik levhada beş senaryo ölçüldü (`595aa46`, 12 sınav):

| senaryo | `distan` | `icten` | **`en_yakin`** |
|---|---|---|---|
| örtü yok, boşluk yok | `+0,9216` | `+0,9216` | **`+0,9216`** |
| örtü `30` m, boşluk yok | ÖRTÜLÜ | `+0,9216` | **`+0,9216`** |
| örtü yok, iç boşluk | `+0,9216` | **`+0,0000`** | **`+0,9216`** |
| **örtü `30` m + iç boşluk ← ÜRETİM** | ÖRTÜLÜ | **`+0,0000`** | **`+0,9216`** |
| örtü `12` m + iç boşluk | ÖRTÜLÜ | **`+0,0000`** | **`+0,9216`** |

Dördüncü satır idx `6` ve `87`'nin durumudur: krater **örtülü** *ve*
içinde **boşluk**. `distan` örtüye takılıyor, `icten` boşlukta çöküyor,
**`en_yakin` ikisini birlikte aşıyor.** Beş senaryonun hepsinde doğru
olan tek tanım.

**Varsayılan değişmedi:** `35/35` mevcut krater sınavı bit-aynı geçti.

## 6. Aşağı yöndeki eşik **KONMADI** — ve niçin

Geriye tek nokta kalıyor: `87`, referansın `37,08` m altında. Simetrik
bir kapı (`derinlik > 2h` → red) onu yakalardı **ama** idx `14`/`16`/`19`'un
gerçek kraterlerini de (`+4,27`/`+4,44`/`+4,93` m) yakalardı. Fizik
simetrik değil: malzeme aşağı **kazılabilir**, ama referans yüzeyin
üstüne çıkıp krater tabanı **olamaz**.

`4,93` ile `37,08` arasında herhangi bir sayı aynı sınıflamayı verir —
ama o sayıyı **bu veriye bakarak** seçmek tam olarak kural 6'nın
yasakladığı şey. Bu yüzden eşik **konmadı**; `87` yayımlanmaz olarak
kalıyor ve sebebi artık yazılı.

> Bir eşik uydurup `87`'yi de kurtarmak kaydı `%7` daha dolu
> gösterirdi. Ölçümden türetilemeyen bir sayıyı **koymamak**, koymaktan
> değerlidir.

## 7. Mühürlü kayıt **DEĞİŞTİRİLMEDİ**

`en_yakin` seçim kuralı **ölçüm görüldükten sonra** yazıldı. Kural 6
gereği, sonuca bakılarak kurulan bir ölçüt o sonucun ürettiği sayıları
*düzeltmek* için kullanılamaz. Bu yüzden:

- `ONKAYIT_HERA_KRATER_uretim66` (SHA-256 `1b3b811e…`) **olduğu gibi
  duruyor**; `en_yakin` ona uygulanmadı ve uygulanmayacak.
- Yeni sayı gerekiyorsa **yeni etiketle** (`enyakin7x`) ayrı kayıt.
- `66` noktanın sayıları da değişmiyor: orada kesişim `%95,5` oranında
  zaten **tek**, ve tek kesişimde "en yakın" ile "ilk" **aynı** şeydir
  (ADR-0064 §5 geri alma koşulu bunu sınıyor).

## 8. Havuz doğrulaması — iş `6892243`, kapıları **önceden** kilitli

`scripts/tani_krater_en_yakin_havuz.py` üç tanımı `96` noktada yan yana
koyuyor. ADR-0064 §3.3'ün `13` noktalık tahmin tablosu betiğe
`ONGORU` sözlüğü olarak **aynen** alındı; yani betik bir keşif değil,
**ADR'nin sınavı**. Üç kapı:

1. **GERİ ALMA** (ADR-0064 §5): `distan`'ın ölçtüğü her noktada
   `en_yakin` aynı sayıyı `1e-9` bağıl farktan fazla değiştirirse kip
   geri alınır.
2. **KAYIP YOK:** `en_yakin`'in `OLCULDU` sayısı `distan`'ınkinin
   altına düşmemeli.
3. **ÖNGÖRÜ:** `13`'te en az `10` tutmazsa ADR-0064 §3.3
   **çürütülmüş** sayılır.

> Sonuç bu kaydın **§9**'una yazılacak. Kapılar yukarıda, sonuç
> görülmeden duruyor.

## 9. Havuz sonucu

*(iş `6892243` koşuyor — bu bölüm sonuç gelince doldurulacak)*

## 10. Kilitli yargılara etkisi — YOK

`krater_derinlik` ADR-0055 ile isteğe bağlı, posteriora girmiyor.
`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), mühürlü spin ön kaydı (KAYIT-084) ve
mühürlü krater ön kaydı (KAYIT-092) **etkilenmez**.
