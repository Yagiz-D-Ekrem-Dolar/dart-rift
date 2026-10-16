# Protokol HS — Hera için mühürlü **spin** öngörüsü (ön kayıt)

**Yazıldı:** 2026-10-16, **öngörü hesaplanmadan ÖNCE.**
**Öncül:** [PROTOKOL-SI](PROTOKOL-SI-SON-ISLEME.md) §5 (ölçümün tanımı),
[PROTOKOL-HT](PROTOKOL-HT-HERA-TAHMIN.md) (krater ön kaydı),
[PROTOKOL-UP](PROTOKOL-UP-POSTERIOR.md) §6, KAYIT-079, KAYIT-080
**Kod:** yazılacak (`scripts/hera_spin_onkayit.py`) ·
**Kayıt:** `docs/onkayit/ONKAYIT_HERA_SPIN_<etiket>.json`

---

## 1. Niçin yeni bir protokol

PROTOKOL-SI §5 spin ölçümünü tanımladı ve şunu yazdı:

> *"Üçü (§5 spin, §6 yoğunluk, §7 şekil) Hera'nın sınayacağı öngörü
> olabilir; **mühürleme PROTOKOL-HT'nin işi**, bu protokol yalnız
> ölçümü tanımlar."*

Ama PROTOKOL-HT yalnız `R_krater`, `V_krater` ve `M_ejekta` kapsıyor —
**spin orada yok.** Yani ölçüm tanımlı, mühür yeri belirtilmiş, mühür
atılmamış. Bu protokol o boşluğu kapatıyor. HT'nin hiçbir satırı
değişmiyor (kural 6); bu onun yanına geliyor.

## 2. Niçin değerli — ve niçin tam burada

KAYIT-079 kilitli yargısı: `n_yön = 1`. `β` yalnız `Y₀` yönünü taşıyor;
`α_b` ve `f` **önselden ayırt edilemiyor.** Dolayısıyla "`f` nedir"
sorusunun bu veriyle cevabı yok.

Havuzda ölçülen sıra korelasyonları ise şunu söylüyor: çarpmanın
kazandırdığı açısal momentum `β`'ya **neredeyse dik** (`r = 0,131`) ve
`β`'nın kör olduğu eksene duyarlı (`ρ(ω, f) = +0,459`).

Ve Hera **bu niceliği ölçecek**: radyo bilimi Dimorphos'un spin hızını
`10⁻³`'ten iyi, spin kutbunu `1°`'den iyi veriyor; "çarpmanın kattığı
libasyon ve spin uyarımı" görev hedeflerinde yazılı.

Yani bu ön kayıt, projenin **kendi negatif sonucunun** işaret ettiği
yere konan bir bahis: *`β` bu ekseni göremiyor, ama şu gözlem görebilir,
işte sayısı.*

## 3. Dürüstlük beyanı — neye kör DEĞİLİZ

Bu protokol **tam kör değildir** ve öyleymiş gibi yazılmayacak:

| gördüğümüz | durum |
|---|---|
| `ρ(ω, f) = +0,459`, `r(β,ω) = +0,131` (88 nokta) | **GÖRÜLDÜ**, KAYIT-078 |
| `n_yön = 1`, eleme bölgesi %7,37 | **GÖRÜLDÜ**, KAYIT-079/080 |
| öngörülen `ω` aralığının kendisi | **görülmedi** — bu protokol onu üretecek |
| Hera'nın ölçeceği değer | **görülmedi** (görev henüz varmadı) |

Yani ön kayıt şunu sabitliyor: **hangi θ kümesinden, hangi yöntemle,
hangi kantillerle ve hangi yanlışlanma kuralıyla** bir aralık
üretileceği. Korelasyonu gördükten sonra "kördük" demek sahtekârlık
olurdu; sabitlenen şey korelasyonun varlığı değil, **ondan sayıya
giden yol**.

## 4. Ne mühürleniyor

### 4.1 Öngörü — `ΔL` ve periyot değişimi

PROTOKOL-SI §5'in tanımladığı nicelik, değiştirilmeden:

    L = Σ m (r − r_km) × (v − v_km) ,  bağlı malzeme (v ≤ v_esc)

Raporlanan: `|L|`, yönü, ve eylemsizlik tensöründen kestirilen **dönme
periyodu değişimi**.

### 4.2 `θ` nereden örnekleniyor — **eleme bölgesinden**

PROTOKOL-UP §6 yargısı **POSTERIOR DAR**: ana sonuç tarih eşleme
bölgesidir, posterior ona koşullu bir ektir. Bu protokol o yargıya
uyar:

- `θ` örnekleri **`I ≤ 3` bağdaşır bölgesinden** (önsel hacmin %7,37'si)
- bölge içinde **düzgün** ağırlık — posterior ağırlığı **kullanılmaz**

Gerekçe: posterior bağdaşır bölgeden 14,8 kat dar ve bu darlık
olabilirlik varsayımından geliyor. Daha dar olanı seçmek öngörüyü
sahte biçimde keskinleştirirdi. **Geniş olan seçiliyor** — yanlışlanması
zorlaşıyor, ama dürüst kalıyor.

### 4.3 Ters yön — asıl kullanışlı ürün

Tek bir aralıktan daha değerlisi, **`ω → f` eşlemesi**: ölçülen bir
açısal momentum değişimi, `f` hakkında ne söyler? Mühürlenen şey bu
eşleme ve belirsizliği olacak. Hera (ya da sonraki bir çalışma)
çarpmanın kattığı `ΔL`'i belirlediğinde, eşleme doğrudan `f`'ye
çevrilebilir.

Bu, projenin asıl katkı adayıdır: `β`'nın kör olduğu ekseni açan
**kalibre bir dönüşüm**.

### 4.4 Sayılar ve tohum

`20 000` örnek, tohum **`20261016`**. Kantiller `q05, q16, q50, q84,
q95`, doğal birimde. Vekil belirsizliği ve ölçülmüş `σ_model`
öngörüye **dâhil**; ihmal edilmez.

## 5. Kayıt biçimi

`docs/onkayit/ONKAYIT_HERA_SPIN_<etiket>.json`: öngörü + meta (örnekleme
bölgesi, koşu sayısı, `t_end`, vekil künyesi, git commit, UTC zaman) ve
içeriğin **SHA-256**'sı. Aynı adla ikinci kayıt **üzerine yazılmaz**
(hata). Kayıt depoya commit'lenir; commit tarihi zaman damgasının
ikinci kanıtıdır.

## 6. Yanlışlanma kuralı — KİLİTLİ

Hera'nın değeri geldiğinde, **kayda dokunulmadan**:

| yargı | koşul |
|---|---|
| **TUTARLI** | ölçülen değer `q05 – q95` içinde |
| **TUTARSIZ** | dışında |

Kantil yazılır. Eşik sonradan gevşetilmez; `q05–q95` burada,
öngörüden önce seçilmiştir.

## 7. Uyarı — **kaydın ayrılmaz parçası**

Bu uyarı öngörüyle birlikte taşınır ve karşılaştırma raporuna aynen
geçer:

1. **Zaman ölçeği uyuşmazlığı.** Model `ΔL`'i `t_end = 600 s`'deki
   değerdir: çarpmanın **kattığı** açısal momentum. Hera 2026 sonunda
   varıyor ve **dört yıl evrilmiş** bir durum ölçecek — NPA sönümü,
   gelgit etkileşimi, yeniden birikme araya giriyor. İkisi aynı nicelik
   **değildir**. Doğrudan karşılaştırma ancak bir geri-yayma modeliyle
   anlamlıdır ve o model bu depoda **yok**.
   Bu, PROTOKOL-HT §5'in krater için taşıdığı uyarının eşidir.

2. **`f` önselden baskın.** `n_yön = 1` olduğu için `f` veriyle
   kısıtlanmıyor; öngörünün genişliği büyük ölçüde **önselin**
   genişliğidir. Dar bir aralık beklenmemeli — ve dar çıkarsa bu bir
   başarı değil, bir hata işaretidir.

3. **Tek sabit sahne.** Bütün havuz tek bir elipsoit sahnede koştu;
   öngörü o sahneye koşulludur.

4. **Çözünürlük açığı kapanmadı.** ADR-0059'un `σ` mı yanlılık mı
   sorusu açık (`−%13` ↔ `%5,3`, 2,5 kat). İnce koşu yanlılık
   gösterirse bu öngörü de yeniden üretilmelidir.

## 8. Bu protokolün yapmadığı

- **HT'yi değiştirmiyor.** Krater ön kaydı olduğu gibi duruyor.
- **SI §5'in ölçümünü değiştirmiyor.** Tanım oradan alınıyor.
- **`ω`'yı posteriora sokmuyor.** `ω`'nın DART karşılığı yok; Kapı A'ya
  takılıyor ve takılı kalıyor. Bu bir **öngörü**, kısıt değil.
- **Eşik gevşetmiyor.** `I = 3`, `q05–q95`, tohum: üçü de burada ve
  önceden.
