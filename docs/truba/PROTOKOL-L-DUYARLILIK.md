# Protokol L — üç eksenli duyarlılık pilotu

**Yazıldı:** 2026-09-11, **koşudan ÖNCE**. Eşikler
`scripts/duyarlilik_raporu.py`'de kilitli, sınavlarıyla
(`tests/test_duyarlilik_raporu.py`) birlikte commit'lendi.

**Kaynak:** uzman yanıtı (2026-09-11), Soru 13: *"Ölçeklenmiş
parametrelerde, gözlem hatalarıyla beyazlatılmış J'nin tekil
değerlerine bakın. Bu pilotu üçüncü ayın sonunda değil ilk ayda yapın.
En küçük tekil değer sayısal/yerleşim gürültüsünün altındaysa, daha
fazla MCMC o ekseni açmaz."*

---

## 1. Soru

Bitiş 3'ün kapısı: **bu gözlem vektörüyle, bu çözünürlükte, üç eksen
(`α_b`, `Y₀`, `f`) gerçekleşme gürültüsünün üstünde birbirinden
ayrılabiliyor mu?** G1/G2 tek skalerle (krater derinliği) yalnız `Y₀`'ı
gördü; yerel Gauss olabilirlikte tek skaler `JᵀΣ⁻¹J`'yi en çok rank 1
yapar (uzman). Soru, **vektörün** rankı.

## 2. Tasarım

- Merkez `θ_c = (α_b = 1,15 ; Y₀ = 1e5 Pa ; f = 0,275)` — S3 önselinin
  ortası.
- Adım: `δ = (0,075 ; 0,5 onluk ; 0,075)` — `α_b` ve `f` için önsel
  aralığın çeyreği; `Y₀` için yarım onluk (geçiş bölgesinin tek
  tarafında kalmak için).
- **Türev koşuları**: `θ_c ± δ_j`, 6 nokta, **iki** sahne tohumuyla
  (`20260906`, `99991111`) — ortak rastgele sayılar.
- **Gürültü koşuları**: `θ_c`, **altı** sahne tohumu (türev
  görevlerinin iki merkezi + `11111111`, `22222222`, `33333333`,
  `44444444`).
- Kaba merdiven (`N ≈ 17 bin`), `t_end = 0,024 s`.

| kol | fizik | amaç |
|---|---|---|
| **L_ara_kirpik** | `ara` akma kipi + matris çekme sınırı + blok alanı **v2** + **geometriden** malzeme + blok yarıçapı `1,7 – 6,5 m` | en iyi mevcut fizik (granüler matris vekili) |
| **L_son_uretim** | üretim (G1 ile aynı: `son`, çekme var, v1, kabadan kopya, `14 – 42 m`) | karşılaştırma |

## 3. Gözlem vektörü (`scripts/gozlem_vektoru.py`)

`d_merkez`, `d_max`, `V_krater`, `R_krater`, `dV_sikisma` (yeni yüzey
operatörü, A73); `beta_hedef`, `M_ejekta`, `P_ejekta`, `theta_ejekta`
(momentum defteri); `mu_ejekta` (`M(>v)` eğimi). Merkez gerçeklemeleri
arasında sapması sıfır ya da tanımsız olan gözlem **düşürülür ve
yazılır**.

## 4. Ön koşullar

| # | koşul | eşik |
|---|---|---|
| Ö1 | merkez gerçekleme sayısı | `≥ 4` |
| Ö2 | geçerli gözlem sayısı | `≥ 3` |
| Ö3 | `ara` kolunda her noktada kuvvet anı `q/Y` | `≤ 1 + 1e-9` (Protokol J ile aynı) |

## 5. Yargı (her kol AYRI)

`J̃_kj = [y_k(θ_c + δ_j) − y_k(θ_c − δ_j)] / (2 σ_k)`, iki tohumun
ortalaması. Tekil değerler `s₁ ≥ s₂ ≥ s₃`:

| `s` | yön |
|---|---|
| `≥ 2` | **AYIRT EDİLEBİLİR** |
| `1 – 2` | **ZAYIF** |
| `< 1` | **GÜRÜLTÜ ALTINDA** |

Toplam: `s₃ ≥ 2` → **ÜÇ EKSEN AYRIŞIYOR**; `s₂ ≥ 2 > s₃` → **İKİ
YÖN**; `s₁ ≥ 2 > s₂` → **TEK YÖN**; aksi → **HİÇBİR YÖN**.

Türev tekrarı: bir eksenin iki tohumdaki beyaz sütunları arasında
bağıl fark `> 0,5` ise o eksen **"türev gürültüde"**; o eksenin
katıldığı yön için yargı OKUNMAZ diye yazılır.

Raporlanan: tekil değerler, en zayıf ve en güçlü yön (sağ tekil
vektörler), gözlem başına katkı, düşen gözlemler.

## 6. Bilinen sınırlar — koşudan önce yazılı

- **Anlık görüntü**: `24 ms` geçici evre; nihai krater değil.
- **Kaba çözünürlük**: `x₀` çözünürlükle kayıyor (A71). Pilot "bu
  çözünürlükte" der; olumlu çıkarsa orta çözünürlükte tekrarlanır.
- **Köşegen gürültü**: 6 gerçeklemeyle tam kovaryans kestirilemez;
  gözlemler arası ilinti tekil değerleri şişirebilir.
- **Blok boyutu**: `1,7 – 6,5 m` **yarıçap** olarak alındı; gözlenen
  değerlerin yarıçap mı çap mı olduğu kaynakla doğrulanmadı (uzman
  Soru 4). Çapsa yarıçaplar yarıya iner ve en ince seviyede
  `r_b/s = 2,4`'e düşer.
- **`α_m` bağlaşımı**: yığın yoğunluğu sabit tutulduğu için `α_b` ve
  `f` türevleri matris gözenekliliği değişimini de içerir (uzman
  Soru 3). Bu, "blok etkisi" diye yorumlanmaz.
- **L_son_uretim'de `f`**: v1 doyduğu için (A74) `f = 0,35` bazı
  tohumlarda nominalden düşük gerçekleşir; o kolun `f` türevi
  zayıflatılmış olabilir.

## 7. Yorum tablosu (koşudan önce)

| L_ara_kirpik | L_son_uretim | anlamı |
|---|---|---|
| ÜÇ EKSEN | TEK YÖN | Düzeltilmiş fizik + vektör gözlem Bitiş 3'ün kapısını açıyor; orta çözünürlükte tekrar |
| İKİ YÖN | TEK YÖN | Bir eksen (en zayıf yön) hâlâ kapalı — o yönü en çok değiştiren gözlem/geometri tasarlanır (uzman) |
| TEK YÖN | TEK YÖN | Vektör gözlem de yetmiyor; yörünge + LICIACube hız–yön gözlemi (uzman Soru 9) gerekiyor |

## 7b. EK (2026-09-11, L sonuçları GÖRÜLMEDEN önce) — gözlem operatörü düzeltmesi

Protokol commit'lendikten sonra, **başka bir koşuda** (yerel mermi `h`
deneyi, kol A) yüzey operatörünün "ayrılan ejekta" ölçütünde bir yapıt
ölçüldü: kaçış hızı `8,2 cm/s`; stres dalgasıyla `~0,2 m/s` dışa giden
ve yalnız `3–6 mm` yer değiştirmiş 707 yüzey parçacığı ejekta sayılıp
silindi ve 6–18 m yanalda `2,75 m`'lik sahte bir halka oluştu. Düzeltme:
parçacık ancak kendi çekirdek desteğinin (`2h`) dışına çıkmışsa ayrılmış
sayılır (`krater_yuzey(ayrilma_mesafesi=2.0)`). L'in gözlem vektörü bu
düzeltilmiş operatörü kullanır. L'in hiçbir sonucu bu karardan önce
okunmadı; yargı eşikleri değişmedi.

## 8. Maliyet

Kol başına 18 koşu × `~5 dk` = `~1,5` GPU-saat. İki kol `~3` GPU-saat.
