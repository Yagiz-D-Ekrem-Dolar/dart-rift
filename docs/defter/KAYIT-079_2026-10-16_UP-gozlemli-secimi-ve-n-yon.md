# KAYIT-079 — PROTOKOL-UP §3/§4 koşuldu: `n_yön = 1`

**Tarih:** 2026-10-16 · **Havuz:** 96/96, kayıp koşu yok ·
**Koşucu:** `scripts/up_gozlemli_secimi.py` ·
**Çıktı:** [`docs/sonuclar/UP_secim_96.json`](../sonuclar/UP_secim_96.json)
**Öncül:** [PROTOKOL-UP](../truba/PROTOKOL-UP-POSTERIOR.md) (2026-10-08,
havuzdan hiçbir nokta görülmeden), KAYIT-077 §4, ADR-0058

---

## 1. Yargı

> **1 YÖN ÖĞRENİLİYOR (3 parametre için YETMİYOR)**
> Yan yargı: **YÖN SAYISI NOKTAYA VE KOVARYANSA BAĞLI** → §4 gereği
> **en küçük** `n_yön` alındı.

KAYIT-077 §4'te açtığım "üç parametre" iddiası bununla **kapanır**.
PROTOKOL-UP'ın veriden önce yazdığı beklenti `n_yön = 2` idi; o da
tutmadı. İkisi de kayda geçiyor, hiçbiri silinmiyor.

## 2. Seçimde tercih yoktu

Kapı A (DART karşılığı var) ve Kapı B (grup başına en çok bir) uygulanınca
geriye **tam üç** aday kalıyor ve her biri ayrı grupta:

| aday | grup |
|---|---|
| `beta` | `periyot_degisimi` |
| `M_kacan` | `ejekta_kutlesi` |
| `e_hiz` | `ejekta_hiz_dagilimi` |

Yani `k = 3` alt kümesi tek seçenekti; E-optimal ölçüt bir şey *seçmedi*,
yalnız değerlendirdi. 96 noktanın hiçbirinde eksik alan yok
(`eksik_alan = 0`), tutarlılık kapısı (`M_kacan`, `v_ort`, `kos_ort`,
`1e-6` bağıl) 96/96 geçti.

## 3. Asıl sebep: gradyanlar neredeyse paralel

Bu σ'dan **bağımsız** bir geometri. Birim gradyanlar arası açı, beş θ
noktasında:

| `u0` | `β`~`M_kaçan` | `β`~`e_hız` | `M_kaçan`~`e_hız` | tekil değerler | koşul |
|---|---:|---:|---:|---|---:|
| merkez | 7,42° | **4,64°** | 3,95° | 1,7294 · 0,0917 · 0,0307 | 56 |
| (0,25;0,25;0,25) | 23,07° | 13,84° | 10,98° | 1,7074 · 0,2836 · 0,0646 | 26 |
| (0,75;0,25;0,75) | 26,95° | 12,78° | 14,22° | 1,7003 · 0,3297 · 0,0107 | 159 |
| (0,25;0,75;0,75) | 29,48° | 24,40° | 5,12° | 1,6889 · 0,3840 · 0,0072 | 236 |
| (0,75;0,75;0,25) | 6,23° | **0,62°** | 5,90° | 1,7299 · 0,0864 · 0,0066 | 263 |

Umut şuydu: `e_hız` kütle–hız dağılımının *şeklini* ölçüyor, `β` ise
momentum *toplamını*; aynı kütleyi yavaş-çok parçayla da, hızlı-az
parçayla da fırlatabilirsin ve `β` bunları karıştırır. Ölçüm bunu
çürüttü — `e_hız`'ın gradyanı `β`'nınkinden merkezde **4,64°**, bir
köşede **0,62°** sapıyor. Üçü de aynı yöne bakıyor.

## 4. Hassasiyet kurtarmıyor — ve nedeni

σ(`e_hız`) için kilitli bir değer **yok** (`ADAYLAR` kütüğü: *"karşılığı
var, sayısı henüz yok"*). Havuzu gördükten sonra bir σ seçmek ön kayıt
olmayacağı için σ serbest bırakılıp tarandı (merkez, ρ=0):

| σ(`e_hız`) | ikinci öz değer |
|---:|---:|
| 0,001 | 4,165 |
| 0,01 | 4,040 |
| 0,1 | 2,536 |
| 1,0 | 2,351 |
| 10,0 | 2,349 |

σ'yı **1000 kat** küçültmek ikinci öz değeri `2,35 → 4,17` yapıyor; eşik
**36**. Öz değer σ ile **doyuyor**. Sebebi basit: σ'yı küçültmek o
satırın *ağırlığını* artırır, *yönünü* döndürmez. Neredeyse eşdoğrusal
gradyanları hiçbir ölçüm kesinliği ayırmaz.

> **Sınır — abartmamak için.** Bu tarama **yalnız merkez noktada ve
> ρ = 0'da** yapıldı. Diğer θ noktalarında ikinci öz değer çok daha
> yüksek çıkıyor (§5); dolayısıyla "hiçbir σ açmıyor" cümlesi **merkez
> için** doğrudur, bütün uzay için değil.

## 5. Kafes: 3 ρ × 5 θ, ikinci öz değer eşiğin iki yanında

Referans σ(`e_hız`) = 1,0. Eşik **36** (değiştirilmedi).

| ρ \\ `u0` | merkez | (0,25;0,25;0,25) | (0,75;0,25;0,75) | (0,25;0,75;0,75) | (0,75;0,75;0,25) |
|---|---:|---:|---:|---:|---:|
| **0,0** | 2,35 | 27,41 | 28,74 | **38,44** | 1,67 |
| **0,4** | 3,51 | **40,56** | **43,62** | **54,59** | 2,20 |
| **0,8** | 9,44 | **107,76** | **118,29** | **140,53** | 5,27 |

Kalın olanlar eşiği geçiyor (`n_yön = 2`), diğerleri geçmiyor
(`n_yön = 1`). İkinci öz değer **1,67 – 140,53** aralığında: eşiğin
iki yanında.

İki gözlem:

1. **Noktaya bağlı.** Jakobyen nerede doğrusallaştırılırsa yargı değişiyor
   — PROTOKOL-UP §4'ün "yerellik bu yargının en zayıf yeri" uyarısı
   birebir gerçekleşti.
2. **ρ büyüdükçe öz değer büyüyor.** İlk bakışta ters görünür ama
   doğrudur: korelasyonlu hata çıkarılabilir, dolayısıyla *farklar*
   bilgi taşır. ADR-0058 §3'ün `R = I` tuzağının aynası.

§4'ün kuralı açık ve uygulandı: **en küçüğü al.** En iyi noktayı seçip
onu raporlamak kiraz toplamak olurdu.

## 6. Ne değişti, ne değişmedi

**Değişmedi:** `FISHER_ESIGI = 36`, yargı tablosu, grup kuralı, Kapı
A/B — hepsi 2026-10-08'de kilitliydi ve hiçbirine dokunulmadı.

**Değişti:** Artık ölçülmüş bir `n_yön` var. Raporun *"kaç yön"* sorusu
kısmen değil **tam** yanıtlandı; cevap **bir**.

## 7. Dürüstlük notları

- **Koşucu havuz görüldükten sonra yazıldı.** `grup_kisitli_secim` ve
  `secim_raporu` yazılmış ve sınavlıydı ama hiçbir yerden
  çağrılmıyordu (A116 ailesi). Betik ölçüt/eşik/yargı **tanımlamıyor**,
  yalnız veriyi kilitli fonksiyonlara taşıyor — ama bu sıralama kayda
  geçmeli, saklanacak bir şey değil.
- **İki ara kusur bulundu ve düzeltildi:** (i) `fizik_tani` npz'de JSON
  dizgesi, sözlük değil; (ii) küresel indeks dosya adından okunamıyor —
  havuz her dilimdeki dört dosyayı da `nokta_0000_<hash>.npz` diye
  adlandırıyor. İkincisi sessiz kalsaydı Jakobyen yanlış θ'larla
  kurulurdu. Artık indeks dosyanın kendi `theta`'sının kilitli tasarımla
  birebir eşleşmesinden geliyor ve eşleşme birebir değilse betik duruyor.
- **σ(`e_hız`) hâlâ yok.** §5 kafesindeki referans değer `1,0` keyfîdir;
  yargıyı belirleyen o değil, §4'ün en-küçük kuralıdır (merkez ve
  (0,75;0,75;0,25) noktaları her σ'da 1 veriyor).

## 8. Bundan sonra

`n_yön = 1` olduğu için PROTOKOL-UP §3 şunu emrediyor: *"yalnız o kadar
birleşim için posterior; kalan bileşenler **önselden ayırt edilemez**
yazılır."* Yani üretim posteriorunun başlığı `n_yön` parametreli olacak
ve `α_b` ile `f` için **sayı verilmeyecek**.

Sırada: §5 (önsel duyarlılığı) ve §6 (tarih eşleme), ikisi de sıfır GPU.
