# ADR-0061 — Krater arama penceresi **durum başına** kurulur, ortak değil

**Tarih:** 2026-10-27 · **Durum:** KABUL EDİLDİ
**Öncül:** A86 (2026-09-14, açık), [KAYIT-088](../defter/KAYIT-088_2026-10-22_A86-kok-sebep-tepe-ortak-alininca-referans-yuzey-kaciyor.md) (kök sebep),
ADR-0055 (krater isteğe bağlı gözlemli)
**Kod:** `observables/crater_shape.py::krater_yuzey`
**Sınav:** `tests/test_krater_pencere_durum_basina.py`

---

## 1. Bağlam

`krater_yuzey`, krateri referans ve son durumun yüzeyleri arasındaki
düşüş olarak ölçüyor. İki yüzey de aynı eksen ışını boyunca, **tek bir
ortak pencerede** aranıyor:

```python
for ad, xx, sec in (("ref", x0, hepsi), ("son", xk, bagli)):
    ...
    tepe = max(tepe, float(np.max(z[yakin])))      # ORTAK
z_alt = tepe - arama_derinligi                      # 10 m
```

KAYIT-088 bunun üretim havuzunda **30/96** noktada `nan` ürettiğini
ölçtü. Operatör enstrümante edildiğinde `nan` dönenin hep **`z_ref`**
olduğu görüldü:

| idx | `Y₀` (Pa) | `z_ref` | `z_son` | pencere |
|---|---:|---:|---:|---|
| 0 | 28,3 | **nan** | 105,916 | 91,76 – 113,66 |
| 3 | 8,5 | **nan** | 100,213 | 95,30 – 117,20 |
| 1 | 58 708 | 59,517 | 58,769 | 49,35 – 71,25 |

Referans yüzey `z ≈ 59,5` m'de; düşen noktalarda pencerenin tabanı
`91–95` m, yani yüzeyin **30–35 m yukarısı**.

**Mekanizma:** zayıf matriste çarpma, malzemeyi eksen boyunca yukarı
fırlatıyor; bir kısmı kaçış hızını geçmediği için `bagli` sayılıyor ve
**ortak** `tepe`'yi belirliyor. `10` m'lik pencere o şişmiş tepeden
sarkınca referans yüzeyi hiç görmüyor.

Bu, kodda zaten kayıtlı bir düşüşün kardeşi: ilk sürüm `tepe`'yi
`max(z + 2h)` ile alıyordu ve kaba parçacıkların `h = 14` m'si onu
şişirince aynı şey olmuştu. O zaman `2h` payı kaldırıldı; şişiren
ikinci etken (**yukarı atılmış bağlı malzeme**) kaldı.

## 2. Niçin **şimdi**

Hera Kasım 2026'da Didymos'a varıyor. PROTOKOL-HT'nin mühürlü krater
ön kaydı `R_krater` ve `V_krater` istiyor ve ikisi de bu operatörden
geliyor.

Düzeltme olmadan ön kayıt 66 noktayla kurulur — ama kaybedilen 30
noktanın **hepsinde `Y₀ < 149` Pa** ve posteriorun kipi `18,7` Pa.
Yani ön kayıt, verinin işaret ettiği bölgeyi sistematik olarak dışlayan
bir örneklemle kurulmuş olurdu. Bu örneklem azlığı değil **seçilim
yanlılığıdır**.

> **Ve Hera verisi gelmeden yapılmalı.** Operatörü veri geldikten sonra
> değiştirmek, sonucu gördükten sonra ölçüm aracını ayarlamak olur.
> Bu ADR'nin tarihi ve commit'i o sıralamanın kanıtıdır.

## 3. Karar

**Arama penceresi ışın başına değil, _durum başına_ kurulur.**

- `z_ref`, referans durumun kendi `tepe_ref`'inden pencerelenir;
- `z_son`, son (bağlı) durumun kendi `tepe_son`'undan;
- düşüş yine `z_ref − z_son` olarak hesaplanır.

Ortak pencere zorunluluğu **yoktur**: iki yüzey bağımsız bulunup
farkları alınır. İki durum aynı `a` ekseni ve aynı `c0` tabanı
üzerinde tanımlı olduğundan `z` ölçeği ortaktır; pencerenin ortak
olması gerekmez.

### 3.1 Ne DEĞİŞMİYOR

- `esik = 0,5`, `arama_derinligi = 10` m, `s_max = 6` m, `ds`,
  `n_azimut`: **hiçbiri ayarlanmadı**.
- Doluluk tanımı `φ = Σ V_j W` aynı.
- Ayrılma ölçütü, rijit kayma düzeltmesi, kabuk hesabı aynı.
- Düşüşün tanımı (`z_ref − z_son`) aynı.

Bu bir **tanım düzeltmesidir**, eşik ayarı değil. Yönü de önceden
belli: ortak pencere yalnız **kaybettiriyordu**; durum başına pencere
daha az `nan` verir, daha fazla değil.

> **NOT (2026-10-27) — bu ADR tek başına YETMEZ.**
> Düzeltme uygulandıktan sonra ölçüldü (KAYIT-089): `nan` gerçekten
> kalkıyor, ama yerine gelen sayı krater derinliği **değil** —
> `d_merkez = −(örtü yüksekliği + 0,913)` m, yani eksendeki kaçmamış
> örtünün tepesi okunuyor. Üretimde `59,517 − 105,916 = −46,4` m.
> Yukarıdaki satırlar silinmedi ve yanlış değil: pencere düzeltmesi
> doğru ve gerekliydi. Eksik olan, *"daha az `nan`"* cümlesinin
> ima ettiği şey: kaybolan `nan`'ların yerine **ölçüm** değil, başka
> bir **red** gelir. O reddi
> [ADR-0062](ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md)
> tanımlıyor; bu iki ADR birlikte uygulanır.

## 4. Reddedilen seçenekler

**`arama_derinligi`'ni büyütmek.** 30 vakayı çözer ama şişmenin
kendisini çözmez: bir sonraki rejimde (daha şiddetli çarpma, daha
yüksek fırlatma) yine düşer. Sayı ayarlamak, tanımı düzeltmenin yerine
geçmez — ve "kaç metre" sorusunun veriden bağımsız bir cevabı yok.

**`tepe`'yi yalnız referanstan almak.** Son durumun yüzeyi referansın
üstüne çıkabilir (kabarma); o zaman `z_son` kaçardı. Simetrik olmayan
bir düzeltme yeni bir yanlılık getirir.

**Operatöre dokunmamak, 66 noktayla devam.** §2'deki seçilim yanlılığı
yüzünden reddedildi.

## 5. Geri alma koşulu

Düzeltilmiş operatör, `nan` sayısını düşürmek yerine **artırırsa** ya
da daha önce okunan 66 noktanın herhangi birinde `d_merkez`'i
`> %1` değiştirirse, bu ADR geri alınır ve sebep KAYIT'a yazılır.
Sınav bu iki koşulu da bağlar.

## 6. Etkilenmeyen yargılar

`krater_derinlik` ADR-0055 ile **isteğe bağlı** gözlemli; `nan` kayıt
düşürmüyor ve posteriora girmiyor. Dolayısıyla `n_yön = 1` (KAYIT-079),
tarih eşlemesi (KAYIT-080), SBC (KAYIT-081) ve çözünürlük yanlılığı
(KAYIT-085) **etkilenmez**. Bu düzeltme yalnız krater gözlemlisini
okunur hâle getirir.
