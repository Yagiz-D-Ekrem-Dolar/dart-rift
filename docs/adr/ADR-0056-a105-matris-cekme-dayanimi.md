# ADR-0056 — **A105:** matris çekme dayanımı açık mı kapalı mı

**Durum:** ÖNERİ (karar kullanıcıda — **A105'in cevabı**) · **Tarih:** 2026-10-04
**Öncül:** **A105** (ölçüldü: `T_m = Y₀/μ_f` açılınca `β` `−%23`),
PROTOKOL-A105, KAYIT-072 (DY2 `MODEL GÖZLEME ULAŞIYOR`),
ADR-0054 (hedef `β = 3,5418`), L1/L2
**Kod:** `--matris-cekme-yok` (üretim ayarı, şu an kullanılan)

---

## 1. Ölçülen

Aynı sahnede, Mohr-Coulomb uç kesmesi (`T_m = Y₀/μ_f`) **açılınca**:

| merdiven | çekme KAPALI | çekme AÇIK | fark |
|---|---|---|---|
| kaba | `3,686` | `2,854` | **`−%23`** |
| orta | `3,978` | `3,074` | **`−%23`** |

Geç evre artışı da kayboluyor (`+0,77 → −0,04`). Çözünürlük farkı bağıl
olarak neredeyse aynı (`0,073` vs `0,072`).

**Bu, çözünürlük belirsizliğinden (`0,053`) dört kat büyük bir
MODELLEME SEÇİMİ.** Kilitlenmeden havuza girilemez.

## 2. Literatür ne yapıyor

L1/L2 (Raducan & Jutzi; Raducan ve diğ. 2024) moloz yığınını şöyle kuruyor:

- **Matris:** dayanım = **kohezyon** (sıfır basınçtaki kayma dayanımı),
  `0 – 500 Pa`. Bizim `matrix_Y0`'ımızın tam karşılığı.
- **Bloklar:** çekme dayanımı `~10 MPa` (yani bloklar *gerçekten* çekmeye
  dayanıyor, matris değil).
- Raducan ve diğ. 2022b ilk modelleri **kohezyonsuz** (`Y₀ = 0 Pa`)
  yığınlara koştu, iç sürtünme `f = 0,55` (bizde `μ_f = 0,6`).

Yani literatürün matrisi, kohezyonu olan ama **çekme dayanımı verilmemiş**
bir malzeme. Mohr-Coulomb uç kesmesinin izin verdiği
`T_m = Y₀/μ_f ≈ 1,7 Y₀` kadar çekme, moloz yığını matrisi için fiziksel
dayanağı olmayan bir ek dayanımdır: gevşek regolit, makroskopik ölçekte
çekmeye **dayanmaz**; dayandığı yer bloklardır ve bloklar modelde zaten
ayrı malzeme.

## 3. Karar (öneri)

**Üretim: matris çekmesi KAPALI (`--matris-cekme-yok`) — kilitlenir.**

Gerekçe: (a) moloz yığını matrisi makroskopik çekmeye dayanmaz; (b) L1/L2
matrise çekme dayanımı **vermiyor**, bloklara veriyor ve bizim modelimizde
bloklar ayrı malzeme olarak zaten var; (c) hâlihazırda bütün doğrulanmış
koşular (W2, UA, UY, UG, DY2, DK) bu ayarla koşuldu — seçimi değiştirmek
bütün kıyas zincirini geçersiz kılar.

### `−%23`'ü bütçeye EKLEMİYORUZ — ve niçin

`MODEL_EKSIKLIGI_KAYNAKLI`'ya `matris_cekme = 0,23` eklemek cazip görünür
("dürüst olalım, belirsizdir"). **Yanlış olur:**

- Bu bir **reddedilen model**, bir belirsizlik değil. Fiziksel gerekçeyle
  seçim yapıp sonra reddettiğimiz alternatifi hata çubuğuna koymak, hata
  çubuğunu *inandığımız* modelin belirsizliğinden değil *inanmadığımız*
  modelden şişirmek olur.
- Sayısal olarak: `0,23` eklenirse `σ_model` bağıl `0,1067 → 0,254`
  (`2,4` kat) ve payda `0,330 → 0,580` olur. `I` `0,63 → 0,36`'ya düşer.
  Yani ekleme, sınavı **kolaylaştırır**. Kendi sınavını kolaylaştıran bir
  "dürüstlük" dürüstlük değildir (ADR-0051 §2b'nin `AŞIRI TEMKİNLİ`
  tanısının tam konusu).

### Bunun yerine: **koşullu duyarlılık** olarak raporlanır

Sonuç cümlesi şöyle yazılır ve her raporda **yan yana** durur:

> Bu sonuç matris çekme dayanımının sıfır olmasına **koşulludur.**
> Mohr-Coulomb uç kesmesi açılırsa `β` `%23` düşer
> (`3,75 → ~2,89`) ve model gözlemin (`3,54 ± 0,19`) **altına** iner:
> `I ≈ 2,0`, hâlâ kesmenin (`3,0`) içinde ama bandın alt yarısında.
> Yani çıkarılan `Y₀` bu seçime bağlıdır ve seçim fizikle, sonuçla değil,
> **önceden** yapılmıştır.

Bu, bütçeye saklamaktan **daha** dürüst: okuyucu farkı görüyor ve
gerekçeyi tartışabiliyor.

## 4. Ölçülmesi önerilen (1 GPU-saat sınıfı)

`−%23` **kıyas** sahnesinde ölçüldü. DART sahnesinde aynı mı? DY2 ile
birebir aynı, yalnız çekme açık bir kol (**DC**) bunu söyler. Maliyet
`~5 GPU-saat`. Yukarıdaki koşullu cümlenin `3,75 → ~2,89` kısmı o zaman
**ölçülmüş** olur; şu an kıyas sahnesinden taşınmış bir orandır.

Sıra: PROTOKOL-DO'dan sonra, 2 GPU hakkıyla DO ile aynı dizide.

## 5. Reddedilen seçenekler

- **Çekmeyi açmak.** Fiziksel gerekçe yok (yukarıda); üstelik bütün
  doğrulanmış kıyas zinciri kapalı ayarla koşuldu.
- **`T_m`'yi `θ`'ya dördüncü eksen olarak eklemek.** Gözlemli sayısı
  **2**; üç parametre bile tanımlanamıyor (ADR-0051 §2c, KAYIT-073 §5).
  Dördüncü eksen posterioru tamamen önsel-baskın yapar.
- **Ara bir değer (`T_m = 0,1 Y₀` gibi) seçmek.** Ölçülmemiş bir sayıyı
  "orta yol" diye seçmek, uydurmaktır. Ya fiziksel gerekçeli `0`, ya
  ölçülmüş bir değer.
- **`0,23`'ü bütçeye eklemek.** §3'te gerekçesiyle reddedildi.
