# Protokol N — küresel ayırt edilebilirlik taraması (koşullanmış saha, en iyi fizik)

**Yazıldı:** 2026-09-13, **koşudan ÖNCE**. Yargı kuralı
`scripts/n_ayirt_raporu.py`'de kilitli, sınavlarıyla
(`tests/test_n_ayirt_raporu.py`) commit'lendi.

## 1. Neden

Protokol G (G1/G2) önsel boyunca `θ`'nın gözlemden ayırt edilip
edilmediğini sordu ve `Y₀`'ı gördü. Ama o tarama: bir yüzey olmayan krater
ölçüsüyle (A73), sahneye ulaşmayan blok kesriyle (A74), kuvvet anında
aşılan akma sınırıyla (A72) ve **rastgele** çarpma sahasıyla yapıldı.
Protokol L gösterdi ki rastgele saha `β`'yı ikili bir anahtara bağlıyor.

N aynı soruyu düzeltilmiş her şeyle soruyor. Bitiş 3'ün vekil modeli
için gereken **küresel harita** budur; L2 ise tek noktadaki yerel
duyarlılığı ölçer — ikisi birbirini tamamlar.

## 2. Tasarım

| | |
|---|---|
| θ | `lhs_design(DART_UZAYI_S3, 24, root_seed = 20260906)` — G1 ile aynı nokta kümesi |
| tohum | `20260906`, `99991111` (iç yapı gerçekleşmesi) → 48 koşu |
| çarpma sahası | **matris** (`3 m` küresinde blok yok). DART gövdesi iki büyük bloğun arasına çarptı; bu idealleştirme ona yakın |
| fizik | `--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh` |
| merdiven / süre | kaba, `t = 24 ms` |

## 3. Yargı

Gözlemler: `d_merkez`, `V_krater`, `R_krater`, `dV_sikisma`,
`beta_eksi_1`, `M_ejekta`, `mu_ejekta` (`gozlem_vektoru.py`).

**Gözlem başına (Protokol G eşikleri aynen):** `F = S_θ / S_gürültü`;
`F > 4` ve en az bir eksende `|ρ| > 0,5` ve `p < 0,05` → **AYIRT
EDİYOR**; iki varyans da sıfır → **DEJENERE**; aksi → **AYIRT ETMİYOR**.

**Eksen sayımı (çoklu sınav düzeltmeli):** 7 gözlem × 3 eksen = 21 sınav.
Bir eksen, AYIRT EDEN bir gözlemde `|ρ| > 0,5` ve `p <` `0,05 / 21` `≈ 0,00238`
(Bonferroni) ise **görünür**. 3 → ÜÇ EKSEN GÖRÜNÜR, 2 → İKİ EKSEN,
1 → TEK EKSEN, 0 → HİÇBİRİ.

## 4. Yorum tablosu (koşudan önce)

| sonuç | anlamı |
|---|---|
| ÜÇ EKSEN GÖRÜNÜR | vektör gözlemle üç parametre küresel olarak iz bırakıyor → vekil model + posterior (gürültü modeli dahil) kurulabilir; M ile çözünürlük hatası eklenir |
| İKİ EKSEN | görünmeyen eksen için ek gözlem (LICIACube blok hızları, yörünge bileşenleri; uzman S9) ya da daha uzun süre (T) |
| TEK EKSEN (`Y₀`) | G1 sonucu düzeltilmiş fizikte de ayakta; blok eksenleri bu gözlemlerle görünmüyor |
| HİÇBİRİ | düzeltilmiş fizikte krater/ejekta gözlemleri 24 ms'de parametre taşımıyor → daha geç zaman ya da farklı gözlem gerekir |

## 5. Bilinen sınırlar

- Kaba merdiven, `t = 24 ms`; M ve T sonuçlarıyla birlikte okunmalı.
- İki tohum: gürültü varyansı θ başına 1 serbestlik derecesiyle kestiriliyor.
- İdealleştirilmiş matris sahası; gerçek DRACO sahası değil.
- Spearman korelasyonu tek eksenli tekdüze ilişkileri yakalar; etkileşimleri kaçırabilir.

## 6. Maliyet

H200 + bvh, kaba: nokta başına `~6 dk`; 48 nokta `~5` GPU-saat
(6 görev × 8 nokta).
