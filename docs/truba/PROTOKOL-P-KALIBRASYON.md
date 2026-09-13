# Protokol P — kapalı döngü posterior kalibrasyonu

**Yazıldı:** 2026-09-13, **N verisi gelmeden ÖNCE**. Yargı kuralı
`scripts/p_kalibrasyon_raporu.py`'de kilitli ve sentetik sınavlarıyla
(`tests/test_p_kalibrasyon_raporu.py`) commit'lendi.

## 1. Soru

Bitiş 3 bir posterior istiyor. Posteriorun **gerçek DART verisine**
uygulanmasından önce iki şey gösterilmeli:

1. Zincir (vekil → olabilirlik → ızgara) **bilinen bir θ'yı geri
   buluyor mu**?
2. Verdiği aralıklar **dürüst mü** — `%68` aralık gerçekten vakaların
   `%68`'inde gerçeği içeriyor mu?

Bunu ölçmenin tek temiz yolu kapalı döngü: benzetimin kendisini "gözlem"
saymak. Gerçek Dimorphos'un iç yapısı TEK bir gerçeklemedir; bu yüzden
"gözlem" olarak **eğitimde görülmemiş** bir θ'nın bir tohumu kullanılır.

## 2. Veri

Protokol N'in 24 θ × 2 tohum koşusu (kaba, matris sahası, en iyi fizik,
`t = 24 ms`). Ek GPU koşusu yok.

## 3. Yöntem (kilitli)

- **Gözlenebilir seçimi:** koşuların en az `%90`'ında sonlu; N raporu
  "AYIRT EDİYOR" demiş; tam veride ikinci derece vekil `q2 > 0,5`.
- **Dönüşüm:** `V_krater`, `M_ejekta`, `β − 1` için `log10` (tabanlar
  `1e-6`, `1e-3`, `1e-4`); diğerleri olduğu gibi.
- **Bırak-bir-θ:** her θ için kalan 23 θ'nın 46 koşusuyla vekil.
- **Kovaryans:** eğitim kümesinin **bırak-bir-θ** artıklarının (aynı
  θ'nın iki tohumu birlikte dışarıda; tek koşu bırakılınca ikiz tohum
  tahmini kendine çeker ve vekil hatası görünmez olur — sınanıyor)
  gözlenebilirler arası kovaryansı, köşegene küçültülmüş
  (`λ = 0,3`). Artık = gerçekleme gürültüsü + vekil hatası. Krater
  derinliği, yarıçapı ve hacmi aynı gerçeklemede birlikte sapar;
  bağımsız saymak aynı bilgiyi birkaç kez sayar (sınanıyor:
  `test_ayni_bilgiyi_IKI_KEZ_saymak_posterioru_yapay_daraltiyor`).
- **Posterior:** düzgün önsel (birim küpte; `Y₀` log), `40³` ızgara.

## 4. Yargı

Eksen başına, 48 vaka üzerinden:

| koşul | yargı |
|---|---|
| `%68` kapsama `< 0,50` | **AŞIRI GÜVENLİ** |
| kapsama `0,50`–`0,87`, medyan `%68` genişlik `< 0,34` | **ÇÖZÜLÜYOR** |
| kapsama `> 0,87`, medyan genişlik `< 0,34` | **ÇÖZÜLÜYOR (TEMKİNLİ)** |
| medyan genişlik `≥ 0,34` | **BİLGİ YOK** |

- `0,50`–`0,87`: 24 bağımsız θ'da `%68` kapsamanın binom `%95` bandı.
- `0,34` = G4-C2'nin ölçütü (önselin `%68` aralığı `0,68`'in yarısı).

**Genel:** herhangi bir eksen AŞIRI GÜVENLİ → **KALİBRASYON DÜŞTÜ**.
Aksi halde çözülen eksen sayısı: ÜÇ / İKİ / TEK / HİÇBİRİ.

**Gürültü tepkisi (G4-C3 ruhu):** kovaryans `1×, 2×, 4×` iken en dar
eksenin medyan genişliği büyümüyorsa (adım başına `%2` tolerans, toplamda
`> %2` büyüme) yargıya **GÜRÜLTÜ TEPKİSİZ, GEÇERSİZ** eklenir.

### 4b. Dış örneklem (N2)

Kapalı döngüde gözlenebilir seçimi ile sınama aynı 48 koşudan geliyor.
Bunu kapatmak için **N2** koşuluyor: aynı fizik ve saha, aynı iki tohum,
ama **başka bir LHS** (`root_seed = 20260914`). Vekil ve kovaryans N'nin
bütün 48 koşusuyla kurulur; N2'nin 48 koşusu yalnız sınamada kullanılır.
Eşikler ve yargı kuralı §4 ile **aynı**. Kapalı döngü ile dış örneklem
farklı yargı verirse **dış örneklem esastır** ve fark raporlanır.

### 4c. İkinci vekil: Gauss süreci (veri gelmeden eklendi, 2026-09-13)

G1 ölçtü: `Y₀` → krater derinliği bir **eşik** (plato + dik düşüş),
ikinci derece polinom onu iyi taşımıyor. Sentetik eşik verisinde ölçüldü
(`test_ESIK_bicimli_veride_GP_polinomun_goremedigi_ekseni_cozuyor`):
polinom `log10_Y0`'ı çözemiyor, GP çözüyor, ikisi de kalibre.

**GP yolu** (`--vekil gp`, `inference/gp_vekil.py`): ARD kare-üstel
çekirdek, deterministik hiperparametre araması, θ'ya bağlı öngörü
varyansı + bırak-bir-θ standart artıklarından korelasyon (`λ = 0,3`
birim köşegene), log-det terimli ızgara posterior. Seçimde `q2`
GP'nin kendi bırak-bir-θ `q2`'sidir. Eşikler §4 ile **aynı**.

**Hangi yol esas (kilitli):** iki yol da N2 dış örnekleminde koşulur.

1. Bir yol KALİBRASYON DÜŞTÜ ya da GÜRÜLTÜ TEPKİSİZ ise o yol elenir.
2. Kalan yollardan **dış örneklemde daha çok ekseni çözen** esastır.
3. Eşitlikte kuadratik esastır (daha basit model).
4. İki yol da elendiyse yargı **KALİBRASYON DÜŞTÜ**'dür.

Seçim dış örneklemde yapıldığı için "iki modeli dene, iyi olanı al"
iyimserliği aralık kalibrasyonuyla sınırlanıyor: elenmeyen bir yol
tanım gereği N2'de dürüst aralık vermiş olur.

### 4d. P-v4 — havuzlanmış K-kat dış doğrulama (2026-09-13, kesmeli veri gelmeden)

**Neden (A82).** Kesmesiz N→N2 dış örnekleminde iki vekil de KALİBRASYON
DÜŞTÜ. Keşif tanısı (yargı değil): dış örneklem `z` sapması `~1,4`
(bırak-bir-θ'da `1,0`), gözlenebilirlerde aynı yönlü `±0,3–0,4σ` ortalama
kayması, en kötü noktalar önsel köşesinde. Korelasyon küçültmesi (`λ`)
etkisiz; yalnız 4-kat artıklar (P-v3) da yetmedi (`Y₀` kapsama `0,46` /
`0,33`). Yorum: 23 θ'lık eğitimde vekilin kendi sapması baskın.

**Kural (kilitli).** Kesmeli üretim verisinde (`Nk` + `N2k` kaba;
`Nok` + `N2ok` orta) **ayrı ayrı**:

1. Havuz = iki tasarım, 48 θ × 2 tohum.
2. Gözlenebilir seçimi §3 ile aynı; `S_N` havuzun N raporundan.
3. θ-gruplu 4 kat (grup kimliği `% 4`). Her katta vekil ve gürültü
   kovaryansı **yalnız öbür üç katla** kurulur; kovaryans iç 4-kat
   artıklarından (`--artik kfold4`); o kat hiç görülmemiş gözlem.
4. 96 vakada §4 eksen yargısı ve genel yargı — eşikler **aynı**.
5. Kuadratik ve GP; yol seçimi §4c (bu kez katlı yargılar üzerinde).

Kesmesiz N/N2 sonuçları (P, P2, P-v3 keşfi) yalnız betimleyicidir.
P-v4'ün kesmesiz havuzda bir kez koşulması **keşiftir** ve kuralı
değiştirmez.

### 4e. P-v4b — zaman örnekleriyle genişletilmiş gözlem vektörü (ikincil, kesmeli veri gelmeden)

Keşif (kesmesiz havuz, yargı değil): P-v4 kuadratik **kalibre** oldu
(kapsama68 `0,63 / 0,63 / 0,71`) ama aralıklar geniş (`0,38–0,47 ≥ 0,34`)
→ HİÇBİR EKSEN. Bilgi var, eşiği geçmiyor. Aynı kesmesiz havuzda N,
47 θ ile **ÜÇ EKSEN GÖRÜNÜR** dedi (24 θ'da TEK).

**Ek adaylar:** `impuls_egrisi`'nden `β−1` ve `M_ejekta` 8 ms ve 16 ms
(`log10`, tabanlar §3 ile aynı; hedef ana `%10` içinde örnek yoksa `nan`).
Seçim: sonlu kesir `%90` ve `q2 > 0,5` (N raporu bunları değerlendirmediği
için N kapısı yok; temel gözlenebilirler N kapısından geçmeye devam eder).
Kural §4d ile **aynı** (`--katli --artik kfold4 --genis-gozlem`).

**Hangisi esas:** §4d (P-v4) **birincil**dir. P-v4b yalnız şu durumda
yargı cümlesine girer: kalibre (elenmemiş) ve P-v4'ten **daha çok ekseni**
çözüyor — o zaman sonuç "zaman örnekleriyle genişletilmiş gözlem
vektörüyle" diye, iki satır birlikte yazılır.

### 4f. Büyütülmüş havuzlar (2026-09-14, veri gelmeden)

§4d–4e kuralları **aynen** şu havuzlarda da koşulur (kesme + taban):
**ince** (`Ni + N2i`, 48 θ), **kaba-72** (`Nk + N2k + Nkd + N3k`), **orta-72**
(`Nok + N2ok + Nokd + N3ok`); N3 = `root_seed 20260921`. Patlayan nokta
dolgusuz kalırsa havuz eksik noktalarla okunur ve sayısı raporda yazılır.
Esas sonuç **en yüksek çözünürlüklü tam havuzun** kilitli yol seçimidir;
çözünürlükler arasında çözülen eksen kümesi farklıysa ikisi birlikte
yazılır ve M2'ye göre yorumlanır.

## 5. Yorum tablosu (veri gelmeden)

| sonuç | anlamı | sıradaki adım |
|---|---|---|
| ÜÇ EKSEN | Bitiş 3 zinciri kaba çözünürlükte kapanıyor | M'nin çözünürlük hatasını kovaryansa ekle; gerçek gözleme uygula |
| İKİ / TEK EKSEN | çözülmeyen eksen(ler) için posterior önseldir; dürüstçe öyle bildirilir | ek gözlenebilir (T: geç zaman; ejekta hız dağılımı) ya da daha çok θ |
| KALİBRASYON DÜŞTÜ | vekil ya da gürültü modeli yetersiz; aralıklara güvenilemez | GP vekil / heteroskedastik gürültü; ADR |
| HİÇBİRİ | 24 ms kaba gözlemleri θ taşımıyor | T sonucuna göre süre, M'ye göre çözünürlük |

## 6. Bilinen sınırlar

- Seçim ve kapalı döngü aynı 48 koşuyu kullanıyor; seçim hafif iyimserlik
  katar (7 adaydan eleme). Dış örneklem (§4b) bunu kapatıyor.
- Kaba çözünürlük hatası (M) ve gözlem hatası kovaryansta **yok**;
  gerçek veriye uygulamada eklenmeleri zorunlu.
- İkinci derece vekil keskin rejim geçişlerini (L: blok altında/matriste)
  kaçırabilir; matris sahası bu geçişi dışarıda tutmak için seçildi.
