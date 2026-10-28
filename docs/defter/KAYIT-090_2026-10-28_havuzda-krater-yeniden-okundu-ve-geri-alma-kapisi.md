# KAYIT-090 — Havuzda krater yeniden okundu; bir geri alma koşulu **lafzen tetiklendi**

**Tarih:** 2026-10-28 · **Sıfır GPU** (CPU kuyruğu, `debug`)
**İşler:** `6864648` (yeni operatör), `6864667` (taban çizgisi: **aynı
betik, eski `crater_shape.py`**), `6864679` (tanı taraması)
**Öncül:** [KAYIT-088](KAYIT-088_2026-10-22_A86-kok-sebep-tepe-ortak-alininca-referans-yuzey-kaciyor.md),
[KAYIT-089](KAYIT-089_2026-10-27_ADR-0061-tek-basina-30-nani-30-yanlis-sayiya-cevirecekti.md),
[ADR-0061](../adr/ADR-0061-krater-penceresi-durum-basina-kurulur.md),
[ADR-0062](../adr/ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md)
**Veri:** [`docs/sonuclar/havuz_krater_96.csv`](../sonuclar/havuz_krater_96.csv)

---

## 1. Tek cümle

Düzeltme havuzda ölçüldü; ADR-0061 kendi hedefini **tam** tutturdu
(`REFERANS` tarafından düşen hiç kalmadı), ADR-0062 yalnız **3** sayıyı
reddetti ve **üçü de negatifti** — ama okunamayan nokta sayısı `47 → 50`
olduğu için ADR-0061 §5'in geri alma koşulu **lafzen tetiklendi**. Bu
kayıt onu gizlemiyor, sebebini sayıyla yazıyor.

## 2. Taban çizgisi nasıl ölçüldü — *aynı betik, eski operatör*

Düzeltmeyi kendi eski hâliyle kıyaslamanın tek dürüst yolu, **aynı
okuma kodunu** eski operatörle koşturmaktı:

```
cp -r agac_havuz agac_oncesi
cd agac_oncesi && git checkout d5721b1 -- src/dartrift/observables/crater_shape.py
```

İş kütüğü bunu yazıyor (`kirli: 1 dosya`). Yani taban çizgisi
hatırlanan bir sayı değil, **bugün ölçülen** bir sayı.

## 3. Sonuç

| sınıf | **yeni** | **eski (taban)** |
|---|---:|---:|
| ÖLÇÜLDÜ | **46** | 49 |
| ÖRTÜLÜ (ADR-0062) | **25** | — (tanım yoktu) |
| YÜZEY_YOK | **25** | 47 |

Geçiş matrisi (96/96, kayıp yok):

| eski → yeni | n |
|---|---:|
| ÖLÇÜLDÜ → ÖLÇÜLDÜ | 46 |
| YÜZEY_YOK → **ÖRTÜLÜ** | 22 |
| YÜZEY_YOK → YÜZEY_YOK | 25 |
| ÖLÇÜLDÜ → **ÖRTÜLÜ** | 3 |

- Eski 47 başarısızlığın **hepsi** "yüzey bulunamadı"ydı.
- Yeni 25 `YUZEY_YOK`'un **tamamı `SON` tarafı**; `REFERANS` tarafından
  düşen **sıfır**. ADR-0061'in iddiası buydu ve tuttu.
- ADR-0062'nin reddettiği 3 noktanın eski değerleri: `−12,457`,
  `−8,192`, `−6,495` m. **Üçü de negatif.**
- Eskiden **pozitif** okunan **39** noktanın `d_merkez`'i `%1` içinde
  değişmedi — **ihlal `0`**.

## 4. Geri alma koşulu: lafzen tetiklendi, tutuldu — gerekçe **ölçüldü**

ADR-0061 §5: *"`nan` sayısını düşürmek yerine **artırırsa** … geri
alınır ve sebep KAYIT'a yazılır."* Ölçüm: `47 → 50`. Sebep burada.

**1. ADR-0061 tek başına koşulu geçiyor.** Geçiş matrisinden: 22 nokta
`YUZEY_YOK`'tan çıkıyor, hiçbiri girmiyor. ADR-0062 olmasaydı
okunamayan sayısı **47 → 25** olurdu. Koşulun hedef aldığı değişim
koşulu **geçiyor**.

**2. Artışın tamamı ADR-0062'nin kasıtlı reddi.** 3 nokta, üçü de
negatif çöp. ADR-0062'nin kendi kapısı — *"pozitif derinlik ölçülen
herhangi bir noktayı reddederse"* — **tetiklenmedi** (0 pozitif
reddedildi).

**3. Koşul yanlış taban çizgisine göre yazılmıştı.** ADR-0061 §5
*"daha önce okunan **66** nokta"* diyor. O `66`, `crater_profile`'ın
(`havuz_96.csv`'deki `krater_derinlik`) sayısı. Yüzey operatörünün
gerçek tabanı **49**. İki çıkarıcı birbirini hiç çağırmıyor;
KAYIT-088'in başlığındaki `30/96` de aynı karışıklığın ürünüydü ve
orada NOT olarak düzeltildi.

**Kural değiştirilmedi.** Koşul olduğu gibi duruyor; tetiklendiği
yazıldı, tetiklenme sebebi üç ayrı ölçümle ayrıştırıldı. Birinin
"geri alınmalıydı" demesi için gereken şey elde: sayılar burada.

## 5. 50 başarısızlığın **tek** bir fiziği var

`YUZEY_YOK` noktalarının son pencereleri `82 – 118` m aralığında, yani
referans yüzeyin (`z ≈ 59,5` m) çok yukarısında. Demek ki orada da
bağlı malzeme var — ama `φ` eşiği kesmiyor.

| eksende bağlı ejekta | sonuç | n |
|---|---|---:|
| **yoğun** (`φ ≥ 0,5`) | tepesi yüzey sanılır → **ÖRTÜLÜ** reddi | 25 |
| **seyrek** (`φ < 0,5`) | hiçbir yüzey bulunamaz → **YÜZEY_YOK** | 25 |

Örtü yüksekliği (yoğun koldan ölçülen): `6,50 … 47,99` m, ortanca
**`30,89` m**. `Y₀` ortancaları: ÖLÇÜLDÜ `3 650` Pa, ÖRTÜLÜ `9,3` Pa,
YÜZEY_YOK `88,4` Pa — örtü **zayıf matris** rejiminde yoğunlaşıyor,
KAYIT-088 §6'nın AUC ölçümüyle aynı yönde.

## 6. Yan ölçüm: `R_krater` 96 noktanın **2**'sinde sonlu

`4,0` m (idx 48) ve `3,8` m (idx 67). A11'in *"krater yarıçapı
gözlenemez"* yargısı ayakta ve artık havuz ölçeğinde sayılı.

## 7. Bundan çıkan cümle ve Hera'ya etkisi

> `t = 600 s`'te, zayıf matris rejiminde geçici krater **gözlenemiyor**:
> kaçmamış ejekta eksende `6 – 48` m yükseklikte duruyor.

Hera **son** krateri görecek. Krater ön kaydı bu anlık görüntüden
`d_merkez` / `V_krater` olarak kurulamaz. Seçenekler (ADR-0062 §3):
ejekta düştükten sonraki bir anlık görüntü (kütükten ölçülen maliyet:
`t_end = 600 → 5000 s` toplam adımı **~4 katına** çıkarır, nokta başına
`~20` GPU-saat), ya da yüzey taramasının içten dışa çevrilmesi.

## 8. Kilitli yargılara etkisi — YOK

`krater_derinlik` ADR-0055 ile isteğe bağlı; posteriora girmiyor.
`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), `n_yön` dayanıklılığı (KAYIT-087) ve
mühürlü spin ön kaydı **etkilenmez**.
