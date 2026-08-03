# Yöntem — sessiz kusurlar nasıl aranır

Bu belge, 2–3 Ağustos 2026 kampanyasında **20 kusuru** bulan yöntemi
aktarılabilir hâle getirir. Kampanyanın çıkış noktası şuydu:

> 627 test geçiyordu. G3 kapısı 7/7. Kırmızı takım 14/14. Kapsam %97.
> **Ve 20 kusur vardı — hepsi kapsanan satırlarda.**

Yani: yeşil bir test takımı, bir kusursuzluk kanıtı değildir. Aşağıdaki üç
soru, o takımın göremediği şeyi görmek içindir.

---

## Soru 1 — "Fiziği dondur, değişmemesi gerekeni ölç"

**Ne zaman:** bir modülün formülleri sınanmış ama **döngüye bağlanışı**
sınanmamışsa.

**Nasıl:** modelin bir parametresini sabitle, hiçbir evrim üretmeyecek bir
kurulum yap, ve **değişmemesi gereken** büyüklüğü adım adım yazdır.

```python
D = np.full(n, 0.5)              # hasari DONDUR
S0[:, 0, 1] = 1.0e7              # bilinen bir gerilme koy
for k in range(4):
    s.D.assign(D)                # her adimda geri koy: buyume olmasin
    s._eval()
    print(k, s.S.numpy()[0, 0, 1])   # SABIT kalmali
```

**Bulduğu:** K1. Ölçülen: `1,0e7 → 5,0e6 → 2,5e6 → 1,25e6 → 6,25e5`.

**Neden işe yarar:** formül testleri "çıktı doğru mu" sorar. Bu soru
"**durum bozuldu mu**" sorar — ve durum bozulması formülden bağımsızdır.

**Genellemesi:** her alan değerlendirmesi **saf bir fonksiyon** olmalıdır.
Bunu bir değişmez olarak sınayın:

```python
s._eval(); once = durum_kopyala(s)
s._eval(); sonra = durum_kopyala(s)
assert bit_ayni(once, sonra)
```

---

## Soru 2 — "Aynı büyüklük iki yerde mi yazılı?"

**Ne zaman:** bir fiziksel büyüklük hem konfigürasyonda hem türetmede
görünüyorsa.

**Nasıl:** büyüklüğü grep'le. Birden fazla yerde **yazılıysa**, ikincisinin
birincisinden **türetilip türetilmediğine** bak.

```bash
grep -rn "6\.67" src/ configs/          # G kac yerde yazili?
grep -rn "bulk_density\|alpha0\|rho0" src/dartrift/setup/
```

**Bulduğu:** K7, K10, K11, K12.

| büyüklük | yer 1 | yer 2 | sonuç |
|---|---|---|---|
| yığın yoğunluğu | `bulk_density` (kütle) | `alpha0` (yoğunluk) | **−7,62 GPa** |
| başlangıç distansiyonu | `pile.alpha0` (dizi) | `porosity.alpha0` (skaler) | **−1,14 GPa** |
| mermi yoğunluğu | `impactor_density` | `ρ₀`/`alpha0` | %11–26 hacim |
| yığın yoğunluğu | mesh hacmi | dolu hacim | %1,19 |

**Kritik gözlem:** dördü de üretim değerlerinde **tesadüfen** tutuyordu.
Yani "şu an doğru" ama hiçbir şey onu doğru tutmuyordu.

**Kural:**
> Bir büyüklük iki yerde yazılıysa, ikincisi birinciden **türetilmeli** ya da
> ayrışma **hata vermeli**. Aynı **ad** iki hesabı taşıyorsa ikisi ayrı
> adlandırılmalı ve ilişki **kapalı formda** kilitlenmeli.

**Ucuz sigorta:** ayrışmayı imkânsız kılan bir test yaz (bkz.
`tests/test_constants_single_source.py`). Davranış değiştirmez, sessiz
ayrışmayı engeller.

---

## Soru 3 — "Bu ölçüt gerçekten sormak istediğim soruyu mu ölçüyor?"

**Ne zaman:** her zaman. En verimli soru buydu — sekiz kusur.

Beş alt biçimi var:

### 3a — Yanlış **büyüklüğü** ölçüyor
```python
f_meas = np.sum(m[is_boulder]) / np.sum(m)     # KUTLE kesri
"boulder_fraction_target": 0.30,                # HACIM hedefi
```
Tekdüze kütlede aynı sayı; kütleler ayrışınca **+%44,5** sapma. → **K13**

**Sınama:** hedefin **tanımına** bak (`f_boulder = boulder_volume/mesh_volume`)
ve ölçülenin **aynı tanım** olduğunu doğrula.

### 3b — **Vekil** ölçüyor
```python
"impactor_outside_target": imp_dist > target_radius   # ESDEGER KURE yaricapi
```
Kürede doğru, elipsoitte **yanlış negatif**. → **K14**

**Sınama:** ölçütü, vekilin **bozulduğu** bir örnekte koştur. Küre için
yazılmış her şeyi elipsoitte dene.

### 3c — **Yanlı örneklemde** ölçüyor
```python
np.mean(cn[cn >= np.median(cn)])     # ornekklem, OLCULEN buyuklukle seciliyor
```
%25 bozuk kafes **11,19** verip `[11,0 ; 12,01]` bandından geçiyordu; gerçek
**10,25**. → **K15**

**Sınama:** seçim ölçütü ile ölçülen büyüklük **aynı şey mi**? Öyleyse sonuç
kendini doğrular. Seçimi **geometrik** (ya da başka bağımsız) yap.

### 3d — Yanlış **davranış** bekliyor
```python
"volume_error_converges": rows[0]["volume_error"] > rows[-1]["volume_error"]
```
Ama o büyüklük **monoton değil** — bir adımda +0,01625 artıyor. Kriterin
sonucu **hangi N'lerin seçildiğine** bağlıydı. → **K16**

**Sınama:** büyüklüğü **çok daha fazla noktada** ölç ve gerçekten beklenen
davranışı gösterip göstermediğine bak.

### 3e — **Hiç düşemiyor**
```python
abs(a + b - 100.0) < 1e-9      # a = 100k/n, b = 100(n-k)/n  -> OZDESLIK
"X" if "X" in doc else "Y"     # esik, aranan metinden seciliyor
```
→ **K20**, **K19-B**

**Sınama:** *"Bu koşulun düştüğü bir dünya var mı?"* Yoksa kanıt değil.

---

## Ek soru — "Bu ölçüm, sinyal ile bir yanlılığın toplamı mı?"

```
deformasyonsuz cisim : global_radius_change = -1,5335 m   (gercek 0)
16 m kraterli        : -1,5335 m   -> fark  +0,0000
%10 buzusme          : -9,3802 m   -> fark  -7,8466
```

Ölçüm **yanlılık + sinyal**. Elle yazılmış `< 5.0` eşiği yalnızca yanlılığı
barındıracak kadar genişti. → **K18**

**Kural:**
> Yanlılığı **ayrı ölç** (sinyalin sıfır olduğu bir kurulumda) ve kriteri
> **farka** uygula.

---

## Her yeni kriterin yanına: boşluk kontrolü

Kampanyanın kalıcı kuralı:

> Yazdığın test **boş bir doğruyu** mu sınıyor?

Örnekler:

```python
# K2 icin: vekil GERCEKTEN yaniliyor mu?
assert scene["irregular_proxy_disagrees"] is True

# K15 icin: bozuk kafeste iki olcut AYRISMALI
assert kendi > geom + 0.5

# K17 icin: ters sarim hacmi GERCEKTEN bozuyor mu?
assert hatalar[-1] > 0.10

# K18 icin: gercek buzusme YAKALANIYOR mu? (pozitif kontrol)
assert obs["crater_detects_real_shrink"] is True

# TestDamageCross icin: hasar GERCEKTEN buyudu mu?
assert st.D.max() > 1.0e-2
```

Boşluk kontrolü olmadan, "krater küresel değişimden ayrışıyor" iddiasını
**her şeye 0 diyen** bir çıkarıcı da sağlar.

---

## Yapısal boşluk taraması

Kod okumadan da bulunabilecek bir sınıf: **hangi modülün bağımsız referansı
yok?**

```bash
ls src/dartrift/warp_core/*.py     # 16 GPU cekirdegi
ls src/dartrift/cpu_reference/*.py #  5 CPU referansi
grep -rln "matches_reference" tests/
```

Eşleştir. Boşluk çıkarsa, orası kusurun **saklanabileceği** yerdir:

- `damage_gradykipp` → referansı **yoktu** → K1 orada yaşıyordu
- `timestep` → çapraz kontrolü **yoktu** → B1

---

## Turun kendi hataları — üçü de kaydedildi

Yöntem uygulanırken **üç kez** kendi ölçümüm/varsayımım yanlış çıktı:

| # | ne | nasıl anlaşıldı |
|---|---|---|
| S1 | *"zayıf kohezyon daha çok plastik iş üretir"* | test düştü; üç kolla ölçüldü, **ters** çıktı (866×) |
| S2 | `str.replace` çapası Türkçe **ı**/`i` yüzünden tutmadı | belge denetimi: tablo 12, gövde 10 kimlik |
| S3 | *"`dt` hızla değişir"* | boşluk kontrolü düştü; yayılım **%1,9** |

Ve iki kez ölçüm aracım kirlendi:

- `kernel_w`'nin ilk argümanı `q = r/h`, ham mesafe değil
- `is_edge_manifold` **parantezsiz** çağrıldı → `<bound method>`, hep truthy

**Ders:** ölçüm aracını da kalibre et. Bilinen bir cevabı olan bir vaka koştur
(düzgün FCC → 12; sağlam küre → 0 hayali krater) ve aracın onu verdiğini gör.

---

## Sıralama — hangi soruyu önce sor

Verim sırası (bu kampanyada ölçülen):

| soru | kusur | maliyet |
|---|---|---|
| 3 — ölçüt doğru şeyi mi ölçüyor | **8** | düşük (kod okuma + küçük ölçüm) |
| 2 — aynı büyüklük iki yerde mi | **6** | düşük (grep) |
| 1 — fiziği dondur | **1** *(ama en ağırı)* | orta (GPU koşusu) |
| yapısal boşluk taraması | **2** | çok düşük (ls + grep) |

**Ama:** Soru 1'in bulduğu tek kusur (K1) en şiddetlisiydi — 1000 kat sapma.
Verim ile önem aynı şey değil.

---

## Kapanış kuralı

> Bir kriter geçtiğinde, **geçme sebebinin** de ölçülmüş olması gerekir.
>
> *"Sonuç değişti"*, *"yayılım pozitif"*, *"derinlik makul"*, *"yakınsıyor"* —
> hepsi doğru sebeple **ve** yanlış sebeple sağlanabilir.

Bu yüzden eklenen her kriter artık **neyin iş gördüğünü** ayrı ayrı raporlar:
`radius_axis_active`, `speed_axis_active`, `reference_is_spherical`,
`target_radius_estimated`, `volume_consistency_min/max`,
`matrix_alpha0_was_solved`, `coordination_interior_n`,
`volume_error_monotone`, `irregular_proxy_disagrees`,
`crater_global_bias`, `crater_detects_real_shrink`.
