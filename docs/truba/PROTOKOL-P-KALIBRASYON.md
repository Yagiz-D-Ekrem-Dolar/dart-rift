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
