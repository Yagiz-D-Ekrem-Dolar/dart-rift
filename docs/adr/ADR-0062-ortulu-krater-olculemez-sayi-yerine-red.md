# ADR-0062 — Örtülü krater **ölçülemez**: sayı yerine red

**Tarih:** 2026-10-27 · **Durum:** KABUL EDİLDİ
**Öncül:** [ADR-0061](ADR-0061-krater-penceresi-durum-basina-kurulur.md) (pencere durum başına),
A86, [KAYIT-088](../defter/KAYIT-088_2026-10-22_A86-kok-sebep-tepe-ortak-alininca-referans-yuzey-kaciyor.md),
[KAYIT-089](../defter/KAYIT-089_2026-10-27_ADR-0061-tek-basina-30-nani-30-yanlis-sayiya-cevirecekti.md)
**Kod:** `observables/crater_shape.py::krater_yuzey`
**Sınav:** `tests/test_krater_pencere_durum_basina.py`,
`tests/test_krater_yuzey.py::test_hizsiz_perde_dislanamaz_ve_krateri_DOLDURUR`

---

## 1. Bağlam — ADR-0061 tek başına yetmiyor

ADR-0061 pencereyi durum başına kurdu ve referans yüzeyin kaçması
bitti. **Ama `nan`'ın yerine gelen sayı krater derinliği değil.**

Düzeltme uygulandıktan sonra ölçüldü (sentetik levha, FCC `s = 0,35`,
`h = 0,70`, `N = 32 490`; eksen üstüne *bağlı*, hızsız bir örtü
konuldu):

| örtü yüksekliği (m) | `d_merkez` (m) |
|---:|---:|
| 0,0 | −0,913 |
| 2,0 | −2,913 |
| 12,0 | −12,913 |
| 30,0 | −30,913 |
| 50,0 | −50,913 |

Bağıntı birebir: **`d_merkez = −(yükseklik + 0,913)`**, eğim
`−1,000 ± 0,001`. Yani okunan şey kraterin tabanı değil,
**örtünün tepesi**. Ejekta kaçmış hâlde aynı çukur `+0,922 m` veriyor.

Üretim havuzunun ölçümü aynı mekanizmayı gösteriyor (KAYIT-088 §2):
`z_ref = 59,517` m, `z_son = 105,916` m → **`d_merkez = −46,4` m**.

Sebep operatörün tanımında: `_doluluk_kesisimi`, `phi = esik`
eş-yüzeyini **dıştan içe** ilk kesişimde buluyor. Eksende, kaçış
hızını geçmemiş (yani `bagli` sayılan) yoğun malzeme varsa ilk
kesişim onun tepesidir. Kaçış hızı Dimorphos için `~8,2 cm/s`;
`600 s`'te `46 m` yükselmiş malzemenin ortalama hızı `~7,7 cm/s`
— tam eşiğin altında. Yani bu malzeme fizik olarak *geri düşecek*
ama ölçüm anında havada.

## 2. Karar

**Merkezde son yüzey, referans yüzeyin bir çekirdek desteği (`2h`)
üzerine çıkmışsa operatör `ValueError` atar ve derinlik döndürmez.**

```python
ortu_payi = 2.0 * h_eksen
if profil[0] < -ortu_payi:
    raise ValueError("ORTULU KRATER: ...")
```

Mesaj iki yüzeyin yerini, aradaki farkı ve çekirdek desteğini yazar.
Çağıran taraf (`gozlem_vektoru`, `forward`) gözlemliyi `nan` yapar ve
sebebi `sebepler["krater"]` içine kaydeder — A86'nın ikinci tespiti
(sessiz `nan`) böylece kapanır.

### 2.1 Eşik **ayarlanmış bir sayı değil**

`2h` çekirdek desteğidir: doluluk alanının bir şey çözebildiği en
küçük uzunluk. Kodda zaten her yerde kullanılıyor (`dest = 2h`,
`ayrilma_mesafesi = 2,0` — `h` biriminde). "Referansta boş olan yerde,
çözünürlükten büyük ölçekte madde var" demek için başka sayı gerekmez.

Daha önemlisi **eşiğin yeri geniş**:

| | `d_merkez` (m) |
|---|---:|
| üretimde çalışan iki nokta | **+0,748**, **+0,892** |
| kapı (`−2h`, `h = 0,70`) | −1,400 |
| üretimde düşen 30 nokta | **−46,4** |

Arada `45 m` boşluk var. Kapı `−1` ile `−45` m arasında **herhangi**
bir yere konsa aynı sınıflamayı verir; sınav bunu dört ayrı değerle
(`−1`, `−5`, `−20`, `−45`) bağlıyor. Bir eşiğin ayarlanmadığını
göstermenin yolu bu: sonucu değiştirmediğini ölçmek.

### 2.2 Yönü önceden belli

Kapı yalnız **sayıyı redde** çevirir. Hiçbir yerde krater yaratmaz,
var olan bir krateri yok etmez, hiçbir pozitif derinliği
büyütmez/küçültmez. Ejekta kaçmış hâl sınavla bağlı: `+0,922 m`
ölçülmeye devam ediyor.

### 2.3 Ne DEĞİŞMİYOR

- `esik = 0,5`, `arama_derinligi = 10` m, `s_max`, `ds`, `n_azimut`:
  dokunulmadı.
- `ayrilan` tanımı (`vr > v_kaçış` **ve** `r − r0 > 2h`) **aynı**:
  rijit kayma, küresel düşüş, hacim değişimi, `n_ayrilan` etkilenmedi.
- Doluluk tanımı, ayrılma ölçütü, düşüşün tanımı aynı.

## 3. Reddedilen seçenekler

**ADR-0061'i tek başına yayınlamak.** 30 dürüst `nan`'ı 30 yanlış
sayıya çevirirdi (`≈ −46 m` "derinlik"). Kural 8'in tam tersi: rapor
bulduğunu değil beklediğini saymalı, ve `nan` bir sayıdan dürüsttür.

**Havada malzemeyi hızdan bağımsız, mesafeyle dışlamak**
(`r − r0 > 2h` → yüzey aramasından çıkar). 30 vakayı "çözer" ama
`ayrilan`'ın hız şartını fiilen kaldırır; A73'te ölçülmüş olan sahte
halka kusuru (`2,75 m`) o şart yüzünden kapanmıştı. İki ölçütü
karıştırmamak gerekiyor.

**Taramayı içten dışa çevirmek** (`c0`'dan dışa ilk `phi < esik`
kesişimi). Fizik olarak doğru yön ve örtüyü yapısal olarak ıskalar;
ama bütün mevcut sınavların anlamını değiştiren büyük bir ameliyat ve
`taban`'ın cismin **içinde** olmasını şart koşar. Hera ön kaydı
yazılmadan, veri gelmeden yapılabilecek bir iş; bu ADR onu
**engellemiyor**, sırayı koruyor. Şimdilik dürüst red tercih edildi.

**`arama_derinligi`'ni büyütmek.** ADR-0061'den sonra zaten gereksiz:
pencere durum başına kurulduğundan `1e-6` m arama derinliğinde bile
iki yüzey bulunuyor (ölçüldü, sınavla bağlı).

## 4. Sonuç — bu bir **bulgu**, yalnız düzeltme değil

Kapının söylediği şey şu: **`t = 600 s`'te, zayıf matris rejiminde
geçici krater gözlenemez**, çünkü kaçmamış ejekta hâlâ onu örtüyor.
Örtünün yüksekliği boş bir sayı değil; `Y₀` ile güçlü biçimde
ilişkili (KAYIT-088 §6: `AUC = 0,087`, ters). 30 düşen noktanın
hepsinde `Y₀ < 149` Pa, posteriorun kipi `18,7` Pa.

Bunun Hera için doğrudan sonucu var ve **PROTOKOL-HT yazılmadan önce**
bilinmesi gerekiyordu: Hera *son* krateri görecek (ejekta düştükten
sonra), bizim `600 s` anlık görüntüsü ise verinin işaret ettiği
rejimde *geçici* krateri bile göstermiyor. Yani krater ön kaydı
`600 s` durumundan `d_merkez`/`V_krater` olarak kurulamaz.

## 5. Geri alma koşulu

Kapı, üretimde **pozitif** derinlik ölçülen herhangi bir noktayı
reddederse ya da daha önce okunan 66 noktanın `d_merkez`'ini
`> %1` değiştirirse bu ADR geri alınır ve sebep KAYIT'a yazılır.
İkisi de sınavla bağlı (`test_ortu_KACARSA_krater_OLCULUYOR`,
`test_URETIM_SAYILARI_dogru_tarafa_dusuyor`).

## 6. Etkilenmeyen yargılar

`krater_derinlik` ADR-0055 ile **isteğe bağlı** gözlemli; `nan` kayıt
düşürmüyor ve posteriora girmiyor. `n_yön = 1` (KAYIT-079), tarih
eşlemesi (KAYIT-080), SBC (KAYIT-081), çözünürlük yanlılığı
(KAYIT-085) ve mühürlü spin ön kaydı **etkilenmez**.
