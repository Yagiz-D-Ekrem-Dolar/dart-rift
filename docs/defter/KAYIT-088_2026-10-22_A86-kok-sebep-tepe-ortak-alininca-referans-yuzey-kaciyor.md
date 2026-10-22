# KAYIT-088 — A86 kök sebep: `tepe` iki durumdan **ortak** alınınca referans yüzey pencereden kaçıyor

**Tarih:** 2026-10-22 · **Sıfır GPU** · **Kilitli operatöre dokunulmadı**
**Öncül:** A86 (2026-09-14, *açık, incelenmedi*), ADR-0055
**Veri:** üretim havuzu, **30/96** nokta `krater_derinlik = nan`

---

## 1. Tek cümle

`nan` dönen şey **referans** yüzeydir, son yüzey değil. Çarpmanın
yukarı attığı ama **kaçmayan** malzeme `tepe`'yi şişiriyor; `10` m'lik
arama penceresi o tepeden aşağı sarkıtıldığında orijinal yüzeye
(`z ≈ 59,5` m) **hiç inemiyor**.

## 2. Ölçüm — operatör enstrümante edildi

`_doluluk_kesisimi` sarmalanıp `k = 0` (eksen ışını) çağrıları kaydedildi:

| idx | `Y₀` (Pa) | `z_ref` | `z_son` | pencere | sonuç |
|---|---:|---:|---:|---|---|
| 0 | 28,3 | **nan** | 105,916 | 91,76 – 113,66 | HATA |
| 3 | 8,5 | **nan** | 100,213 | 95,30 – 117,20 | HATA |
| 5 | 20,7 | **nan** | 106,733 | 94,43 – 110,73 | HATA |
| 1 | 58 708 | 59,517 | 58,769 | 49,35 – 71,25 | ✓ |
| 2 | 1 266 | 59,517 | 58,625 | 54,42 – 76,32 | ✓ |

İki çalışan nokta `z_ref = 59,517` veriyor — **aynı sayı**, çünkü
referans sahne hepsinde aynı. Düşen noktalarda pencerenin tabanı
`91–95` m: referans yüzeyin **30–35 m yukarısı**.

Zincir: `z_ref = nan` → `dusus[0,0] = nan` → `profil[0]` sonlu değil →
`ValueError: eksen isininda yuzey bulunamadi`.

## 3. Niçin `tepe` şişiyor

Kodda `tepe`, eksenden `s_max` içindeki parçacıkların en üst noktası
olarak **iki durumdan birden** alınıyor:

```
for ad, xx, sec in (("ref", x0, hepsi), ("son", xk, bagli)):
    ...
    tepe = max(tepe, float(np.max(z[yakin])))
```

Zayıf matriste çarpma, malzemeyi eksen boyunca yukarı fırlatıyor ama
bir kısmı kaçış hızını geçmiyor — yani `bagli` sayılıyor ve `tepe`'yi
belirliyor. Pencere (`arama_derinligi = 10` m) o tepeden sarkıyor ve
referans yüzey dışarıda kalıyor.

## 4. Bu, kodda **zaten kayıtlı** bir hatanın kardeşi

`crater_shape.py` içindeki yorum aynı aileyi anlatıyor:

> *"İlk sürüm tepeyi `max(z + 2h)` ile alıyordu ve gerçek DART
> durumunda DÜŞTÜ (ölçüldü): merdivenin kaba parçacıklarında
> `h = 14 m`, tepe `98,8 m`'ye şişiyor, `10 m`'lik pencere
> `82 m`'deki yüzeye inemiyordu."*

Mekanizma aynı — **tepe şişiyor, pencere yüzeye inemiyor**. Değişen
yalnız şişiren etken: o zaman `2h` payıydı, şimdi **yukarı atılmış
bağlı malzeme**.

## 5. Kayıtlı teşhis düzeltiliyor

A86 (2026-09-14) şunu yazıyordu:

> *"merkez ışın boyunca doluluk `φ` pencerenin tamamında eşiği (`0,5`)
> kesmiyor: ışın altında eşik altı doluluk (boşluk ya da ayrılmış
> seyrek katman) pencerenin alt ucuna kadar sürüyor."*

Yani **son** durumun seyrelmesi suçlanıyordu. Üretim havuzunun 30
vakasında ölçülen bu değil: `z_son` **bulunuyor**, `z_ref`
bulunamıyor. O zamanki tek vakada (M2, 24 ms) başka bir dal etkin
olmuş olabilir; ama üretim rejiminde baskın mekanizma budur.

A86'nın *"pencereyi büyütmek muhtemelen çözmez"* öngörüsü de
**yanlış** çıkar: pencereyi `35` m'ye çıkarmak ya da referans ışını
kendi `tepe`'siyle pencerelemek bu 30 vakayı doğrudan çözer.

## 6. Niçin düşük `Y₀`'da yoğunlaşıyor — ölçüldü

`nan` olma ile parametreler arasındaki ayırt edicilik (AUC):

| değişken | AUC | yorum |
|---|---:|---|
| `log10 Y₀` | **0,087** | güçlü, **ters** (düşük `Y₀` → düşme) |
| ejekta kütle kesri | 0,942 | güçlü |
| `β` | 0,929 | güçlü |
| `α_b` | 0,515 | bilgi yok |
| `f` | 0,359 | zayıf |

**30 `nan` noktanın hepsinde `Y₀ < 149` Pa.** `Y₀ < 149` Pa olan 41
noktanın 29'u (`%71`) düşüyor. Yani kusur rastgele değil, **zayıf
matris rejimine** bağlı — çünkü yukarı atılan bağlı malzeme orada çok.

## 7. Önerilen düzeltme — **uygulanmadı**

Kilitli operatöre dokunulmadı (kural 6). Önerilen, en küçük
müdahaleli yol:

**Pencereyi ışın başına değil, _durum başına_ kur.** `z_ref` referans
durumun kendi `tepe_ref`'inden, `z_son` son durumun `tepe_son`'undan
pencerelensin. İki yüzey ayrı ayrı bulunduktan sonra `düşüş =
z_ref − z_son` yine hesaplanır; ortak pencere zorunluluğu yoktur.

Bu, `tepe` şişmesini tanım gereği ortadan kaldırır ve `arama_derinligi`
ayarına bağımlılığı azaltır.

**Alternatif (daha zayıf):** `arama_derinligi`'ni büyütmek. Bu 30
vakayı çözer ama şişmenin kendisini çözmez; bir sonraki rejimde yine
düşer. Sayı ayarlamak yerine tanımı düzeltmek tercih edilmelidir.

## 8. İkinci, ayrı kusur hâlâ açık

A86'nın ikinci tespiti yerinde duruyor: istisna `gozlem_vektoru`
içinde sebepsiz `nan`'a çevriliyor (`KeyError, ValueError → nan`).
30 vakanın tamamı, sebebi çıktıya yazılmadan sessizce kayboldu —
kök sebebi bulmak için bu oturumda operatörü elle sarmalamak
gerekti. **Sebep çıktıya yazılmalı.**

## 9. Sonuca etkisi

`krater_derinlik` ADR-0055 ile **isteğe bağlı** gözlenebilir ilan
edilmişti; `nan` kayıt düşürmüyor ve posteriora girmiyor. Dolayısıyla
bu kusur `n_yön = 1` dâhil hiçbir kilitli yargıyı etkilemez.

Etkilediği tek şey: krater ekseni üzerinden ek bir gözlenebilir
kazanma ihtimali. Düzeltilirse zayıf matris rejiminde 30 nokta daha
okunur hâle gelir — ama o gözlenebilirin DART karşılığı
(`R_krater`) zaten A11'den beri gözlenemez sayılıyor.
