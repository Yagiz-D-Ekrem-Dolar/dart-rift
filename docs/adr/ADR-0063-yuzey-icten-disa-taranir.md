# ADR-0063 — Yüzey **içten dışa** taranabilir: `tarama = "icten"`

**Tarih:** 2026-10-28 · **Durum:** KABUL EDİLDİ (yan yana alan;
**varsayılan DEĞİŞMEDİ**)
**Öncül:** [ADR-0061](ADR-0061-krater-penceresi-durum-basina-kurulur.md),
[ADR-0062](ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md),
[KAYIT-089](../defter/KAYIT-089_2026-10-27_ADR-0061-tek-basina-30-nani-30-yanlis-sayiya-cevirecekti.md),
[KAYIT-090](../defter/KAYIT-090_2026-10-28_havuzda-krater-yeniden-okundu-ve-geri-alma-kapisi.md)
**Kod:** `observables/crater_shape.py::_doluluk_kesisimi`, `krater_yuzey`
**Sınav:** `tests/test_krater_tarama_yonu.py` (11)
**Ölçüm:** işler `6864679` (`arama_derinligi` taraması), `6864736`
(yön karşılaştırması), 96/96 nokta, sıfır GPU

---

## 1. Bağlam

ADR-0062, eksende kaçmamış ejekta varsa operatörün sayı yerine
reddetmesini sağladı. Ama reddin kendisi bir çözüm değil: havuzun
`50/96` noktasında krater okunamıyor ve bunların `Y₀` ortancası
(`9,3` Pa) tam posteriorun işaret ettiği yer.

ADR-0062 §3 asıl çözümü ismen saymış ama **reddetmemişti**:

> *"Taramayı içten dışa çevirmek … fizik olarak doğru yön ve örtüyü
> yapısal olarak ıskalar … Hera ön kaydı yazılmadan, veri gelmeden
> yapılabilecek bir iş; bu ADR onu engellemiyor, sırayı koruyor."*

Bu ADR o işi yapar.

## 2. Karar

`krater_yuzey`'e `tarama` alanı eklenir. İki değer:

| değer | tanım |
|---|---|
| **`"distan"`** (VARSAYILAN) | `z_ust`'ten aşağı inilir; `phi` eşiği **ilk aştığı** yer yüzeydir. Kilitli davranış, **bit-aynı**. |
| `"icten"` | `z_alt`'tan yukarı çıkılır; `phi`'nin eşiğin **altına ilk düştüğü** yer yüzeydir. `z_alt = 0`, yani `taban`'ın kendisi — kütle merkezi düzlemi, cismin içi. |

`"icten"` kipte `arama_derinligi` **kullanılmaz**: yüzeyin yeri bir
mesafe ayarıyla değil, dolulukla belirlenir. Aynı `phi`, aynı `esik`,
aynı ikiye bölme; değişen yalnız **hangi kesişimin yüzey sayıldığı**.

**Varsayılan `"distan"` kalır.** Gerekçe §5'te.

## 3. Niçin bu bir *tanım*, ayar değil

### 3.1 Sentetik — örtü nereye konursa konsun aynı sayı

Levha, `1 m` derin paraboloit çukur, eksen üstünde **bağlı** (hızsız)
örtü:

| örtü | `distan` | `icten` |
|---|---|---|
| yok (ejekta kaçtı) | **+0,9216** | **+0,9216** |
| `2 m` | RED (ADR-0062) | **+0,9216** |
| `12 m` | RED | **+0,9216** |
| `30 m` | RED | **+0,9216** |
| `50 m` | RED | **+0,9216** |
| `0 m` (yüzeye **değiyor**) | `−0,9134` | `+0,9161` |

`distan`'da eğim `−1,000` (örtüyü okuyor), `icten`'de **`0`**. Ve örtü
gerçekten çukuru doldurduğunda (`0 m`, perde yüzeye değiyor) `icten`
bunu **görüyor** — yani kör değil.

### 3.2 Üretim — 46 kilitli ölçümü **birebir** yeniden üretiyor

`distan`'ın ölçtüğü 46 noktada `icten` ile bağıl fark: ortanca
**`0,000e+00`**, en büyük **`1,868e-14`**. Yani makine hassasiyeti.
Yeni tanım hiçbir yayımlanmış sayıyı değiştirmiyor.

### 3.3 Bağımsız bir tanıyla çapraz doğrulandı

`arama_derinligi`'ni `60 m`'ye çıkarmak (ADR-0062 §3'te *düzeltme
olarak* reddedilmişti; burada yalnız **ikinci bir tanı**) 96 noktada
ayrı ayrı koşuldu:

| `arama_derinligi` | ÖLÇÜLDÜ | ÖRTÜLÜ | YÜZEY_YOK |
|---:|---:|---:|---:|
| 10 m (kilitli) | 46 | 25 | 25 |
| 20 m | 51 | 28 | 17 |
| 40 m | 59 | 30 | 7 |
| 60 m | 66 | 30 | **0** |

Pencereyi uzatmak **hiçbir ölçülen değeri değiştirmiyor** (46 noktada
en büyük fark `1,4e-14` m) — pencere yalnız uzuyor.

`icten`'in kurtardığı 33 noktanın **20**'sini `distan@60m` de ölçüyor:

| | n |
|---|---:|
| iki tanı da ölçüyor ve **`%1` içinde uyuyor** | **20** |
| iki tanı da ölçüyor ama **çelişiyor** | **0** |
| yalnız `icten` ölçüyor (`distan@60m` ÖRTÜLÜ diyor) | 13 |

Sıfır çelişki. Örnek (idx, `Y₀` Pa, `icten`, `distan@60m`):
`7, 54,21, +2,217, +2,217` · `8, 688,8, +0,684, +0,684` ·
`9, 52,0, −0,651, −0,651` · `18, 4100,8, +0,772, +0,772`.

## 4. Sınır — **13 nokta çapraz doğrulanmıyor**

`icten` bu 13 noktada sayı veriyor, `distan@60m` ise ÖRTÜLÜ diyor. Ve
bazı değerler fiziksel değil: idx 87'de **`+36,490 m`**
(`V = 3 043 m³`), idx 6'da **`+28,609 m`** — hedefin yarı eksenleri
`58 – 88,5` m, yani bu "krater" gövdenin yarısı kadar.

Ayrım **sayıya vuruyor**: çapraz doğrulanan 66 noktanın `d_merkez`
aralığı **`−4,930 … +4,428` m**; doğrulanmayan 13'te `−5,587 …
+36,490` m. İki absürt değerin ikisi de doğrulanmayan kümede.

**Sebep:** `icten`, `taban`'dan dışa çıkarken `phi`'nin eşik altına
**ilk** düştüğü yeri alır. Çarpma gövde içinde bir boşluk (hasar,
gözeneklilik, ayrılmış katman) bırakmışsa tarama **dış yüzeye
varmadan** orada durur. Yani `icten` da yanlış kesişimi seçebiliyor —
sadece başka bir sebeple.

İki yön de aynı sınıfın hatasını yapıyor: **doğru kesişimi doğrultuya
bakarak seçmek**. Asıl çözüm bağlantılılık ölçütüdür (`taban`'ı içeren
*bağlantılı bileşenin* dış yüzeyi). Bu ADR onu yazmıyor; önünü de
kapatmıyor.

## 5. Niçin varsayılan **değişmiyor**

Bugün düzeltilen kusurun özü şuydu: *savunulamayan bir sayıyı sessizce
döndürmek*. `icten`'i varsayılan yapmak, 13 noktada savunamadığımız
sayıları üretim tablolarına sokardı. Kural 8'in tam tersi.

Yani `icten` **kabul edildi ve sınandı**, ama:

- **Tanı ve Hera ön kaydı için tercih edilen tanım `icten`'dir** — ve
  yalnız **çapraz doğrulanmış 66 nokta**ta (46 `distan` ile birebir +
  20 `distan@60m` ile `%1` içinde) kullanılır. Hangi noktaların hangi
  kümede olduğu satır satır
  [`havuz_krater_tarama_96.csv`](../sonuclar/havuz_krater_tarama_96.csv)
  `capraz_dogrulandi` sütununda yazılı
  (`EVET_distan_ile` 46 · `EVET_60m_ile` 20 · `HAYIR_tek_tani` 13 ·
  `olculmedi` 17).
- **Varsayılanın değişmesi** 13 noktanın çözülmesine bağlıdır
  (bağlantılılık ölçütü ya da ejekta düştükten sonraki bir anlık
  görüntü). O zaman bu ADR güncellenir, şimdi değil.

## 6. Ne DEĞİŞMİYOR

`esik = 0,5`, `arama_derinligi = 10 m` (`distan` kipinde), `s_max`,
`ds`, `n_azimut`, doluluk tanımı, ayrılma ölçütü, ADR-0062 örtü kapısı,
düşüşün tanımı (`z_ref − z_son`). Mevcut 24 krater sınavı **aynen**
geçiyor; `tarama` verilmediğinde sonuç bit-aynı (sınavla bağlı).

## 7. Geri alma koşulu

`icten`, `distan`'ın ölçtüğü herhangi bir noktada `d_merkez`'i
`> %1` değiştirirse (şu an en büyük fark `1,9e-14`) ya da çapraz
doğrulanan 20 noktanın herhangi birinde iki tanı `%1`'den fazla
ayrışırsa, bu ADR geri alınır ve sebep KAYIT'a yazılır. İkisi de
`scripts/tani_krater_tarama_yonu.py` ile yeniden üretilebilir.

## 8. Etkilenmeyen yargılar

`krater_derinlik` ADR-0055 ile isteğe bağlı; posteriora girmiyor.
`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085) ve mühürlü spin ön kaydı
**etkilenmez**.
