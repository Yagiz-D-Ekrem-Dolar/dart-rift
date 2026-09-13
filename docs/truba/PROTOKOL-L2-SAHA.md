# Protokol L2 — çarpma sahası koşullanmış duyarlılık pilotu

**Yazıldı:** 2026-09-13, **koşudan ÖNCE**. Eşikler Protokol L'den
(`scripts/duyarlilik_raporu.py`) aynen; rejim tekrar sınavı
`scripts/l2_rejim_raporu.py`'de kilitli, sınavlarıyla
(`tests/test_l2_rejim_raporu.py`) commit'lendi.

## 1. Neden

Protokol L ([sonuç](../SONUC-L-DUYARLILIK.md)): düzeltilmiş fizikte
kilitli yargı **HİÇBİR YÖN**. Koşudan sonra ölçüldü: `β`'yı çarpma
noktası altındaki blok belirliyor — bloğa çarpma `β−1 ≈ 0,03`, matrise
`≈ 0,5` (en yakın blok `≤ 0,35 m` ↔ `≥ 2,2 m`, kusursuz ayrım). Rastgele
saha bu ikili anahtarı gürültüye çeviriyor ve parametre etkisini
gömüyor. Uzman: *"Çarpma noktasında bilinen yüzey bloklarını koşullayın;
bilinmeyen iç yapıyı rastgeleleştirin."*

## 2. Tasarım

Protokol L ile **aynı** 7 noktalı tasarım (merkez `θ_c = (1,15 ; 1e5 Pa ;
0,275)`, çeyrek aralık adımları), iki türev tohumu (`20260906`,
`99991111`) ve altı merkez gerçekleşmesi. Kaba merdiven, `t = 24 ms`.

| kol | çarpma sahası |
|---|---|
| **L2_matris** | çarpma noktasının `3 m` küresinde **hiç blok yok** (iç yapı rastgele) |
| **L2_blok** | çarpma noktası `4 m` yarıçaplı gömülü bir **bloğun içinde** (iç yapı rastgele) |

Ortak fizik — elimizdeki en iyi yapılandırma: `--akma-kipi ara` (A72),
`--matris-cekme-yok`, `--blok-uretici v2 --malzeme-kaynagi geometri
--blok-rmin 1.7 --blok-rmax 6.5` (A74), `--mermi-h-kipi kendi` (A78),
`--mermi-eos aluminyum` (A75), `--ilk-dt-duzelt` (A77),
`--komsu-arama bvh` (A52).

## 3. Yargı 1 — duyarlılık (her kol AYRI, Protokol L eşikleri)

| `s` | yön |
|---|---|
| `≥ 2` | AYIRT EDİLEBİLİR |
| `1 – 2` | ZAYIF |
| `< 1` | GÜRÜLTÜ ALTINDA |

Türev tekrarı `> 0,5` → eksen "türev gürültüde". Merkez gerçekleşmesi
`≥ 4`. Her noktada kuvvet anı `q/Y ≤ 1 + 1e-9`.

## 4. Yargı 2 — rejim tekrar sınavı

`oran = medyan(β−1 | L2_matris merkez) / medyan(β−1 | L2_blok merkez)`

| oran | yargı |
|---|---|
| `≥ 5` | **REPLİKE** |
| `2 – 5` | **BELİRSİZ** |
| `< 2` | **REPLİKE DEĞİL** |

Blok kolunda medyan `β−1 ≤ 0` ise: matris kolu `≥ 0,05` → REPLİKE,
değilse BELİRSİZ.

## 5. Yorum tablosu (koşudan önce)

| L2_matris | L2_blok | anlamı |
|---|---|---|
| ≥ İKİ YÖN | herhangi | saha koşullanınca parametreler gürültünün üstüne çıkıyor → orta çözünürlükte tekrar; gözlem modeline sahanın gerçek (DRACO) geometrisi girer |
| TEK YÖN | TEK YÖN | yalnız bir eksen; zayıf yön için ek gözlem (LICIACube blok hızları, uzman S9) |
| HİÇBİR YÖN | HİÇBİR YÖN | koşullama gürültüyü kaldırmadı → kaynak iç bloklar ya da sayısal; yeni tanı |
| diğer | diğer | tabloda yok — **öyle yazılır**, sonradan açıklanır ve etiketlenir |

## 6. Bilinen sınırlar (koşudan önce)

- Kaba merdiven, 24 ms anlık görüntü; enerji sapması `~%2` (A77,
  düzeltmeyle azalır).
- Saha geometrisi **idealleştirilmiş** (tek küresel blok ya da bloksuz
  küre), gerçek DRACO sahası değil.
- Mermi kendi `h`'siyle (A78) `dt` `~5` kat küçülüyor; L ile büyüklükler
  birebir karşılaştırılamaz — L2'nin kendi iki kolu karşılaştırılır.
- `α_m` bağlaşımı (uzman S3) L'deki gibi sürüyor.

## 7. Maliyet

H200 + bvh, kaba: `~22 ms/adım`, `~16 bin adım` → nokta başına `~6 dk`.
Kol başına `2 × 7 + 4 × 1 = 18` nokta, iki kol `~4` GPU-saat.

## 8. Ek — matris kolu orta merdivende (kaba sonuç GELDİKTEN sonra, orta koşudan ÖNCE yazıldı, 2026-09-13)

Kaba sonuç ([SONUC-L2-SAHA](../SONUC-L2-SAHA.md)): matris kolu ÜÇ EKSEN
AYRIŞIYOR. §5 yorum tablosu *"orta çözünürlükte tekrar"* diyor; bu ek o
tekrarı tanımlıyor. **Hiçbir eşik değişmiyor.**

- Kol `L2o_matris`: `L2_matris` ile aynı tasarım, aynı 6 tohum, aynı fizik
  ve saha; yalnız `--kademeler orta`. İş: `truba/is_L2o_orta.slurm`.
- Rapor: `duyarlilik_raporu.py --kol L2o_matris`; okunacak alan
  `karar_okunur` (A79).
- Yargı:

| orta `karar_okunur` | anlamı |
|---|---|
| ÜÇ EKSEN AYRIŞIYOR (okunmaz eksen yok) | kaba sonuç orta çözünürlükte **ayakta** |
| İKİ / TEK YÖN ya da okunmaz eksen var | kaba sonuç çözünürlükle **zayıflıyor**; hangi eksen düştüyse o yazılır, M'nin yakınsama yargısıyla birlikte okunur |
| HİÇBİR YÖN | kaba "üç eksen" bir **çözünürlük yapıtı** olabilir; Bitiş 3 bu çözünürlükte açılmaz |

- Ek betimleyici (yargıyı değiştirmez): kopya gözlenebilirler (`d_max`,
  `P_ejekta`) çıkarılmış `s₃` ve kaba ile orta arasında merkez `β − 1`
  medyanı yazılır.

Maliyet: orta nokta `~550 s` (M ölçümü), 18 nokta `~2,8` GPU-saat.
