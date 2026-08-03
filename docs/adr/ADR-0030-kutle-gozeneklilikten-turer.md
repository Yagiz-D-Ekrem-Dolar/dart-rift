# ADR-0030 — Parçacık kütlesi gözeneklilikten türer; `bulk_density` bir HEDEFTİR

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3, P3-FR-02/03/04 (moloz yığını), G3 C2
- **İlgili:** ADR-0015 (süreklilik vs toplam yoğunluk), ADR-0022 (gerilmesiz
  gözenekli başlangıç), ADR-0025 (altın sahne mekanizması), ADR-0029

## Kusur

`build_rubble_pile` kütleyi şöyle atıyordu:

```python
m = np.full(len(x), bulk_density * v_p)      # TEKDÜZE
```

Çözücü ise başlangıç yoğunluğunu şöyle atıyor (ADR-0022, gerilmesiz başlangıç):

```python
rho = rho0_solid / alpha0                     # PARÇACIK BAŞINA
```

Bu ikisi **birbiriyle tutarlı olmak zorundadır**. SPH'de bir parçacığın
kapladığı hacim `m/rho`'dur ve kafeste kapladığı hacme (`V_p`) eşit olmalıdır;
aksi halde birim bölünmesi bozulur:

```
sum_j (m_j / rho_j) W_ij = 1
```

Üretim konfigürasyonu (`p3_dimorphos.yaml`) tam bu çelişkiyi taşıyordu:

```yaml
rho0: 2700.0            # katı bazalt (Tillotson)
bulk_density: 1800.0    # yorumu: "~%33 gözeneklilik"  -> alpha = 1.5 demek
matrix_alpha0: 1.6      # -> yığın yoğunluğu 1687.5, 1800 DEĞİL
boulder_alpha0: 1.05    # -> 2571.4
```

Konfigürasyonun **kendi yorumu kendi parametresiyle çelişiyordu**: %33
gözeneklilik α = 1,5 demektir, yazılı değer 1,6.

## Ölçülen etki

Birim bölünmesi (`sum_j (m_j/rho_j) W_ij`, 1 olmalı) — üç farklı `h`'de,
yani `h`'den bağımsız:

| h / spacing | M0 (homojen) | M1 matris | M1 blok |
|---|---|---|---|
| 1,3 | 1,0707 | 0,9837 | **0,7705** |
| 1,6 | 1,0677 | 0,9662 | **0,7842** |
| 2,0 | 1,0669 | 0,9519 | **0,8031** |

M0'daki sabit +%6,7 tam olarak `1800 / (2700/1,6) = 1,0667`'dir — yani
kusurun kapalı-form imzası.

Aynı parçacık dizilimi için atanan ve toplam (summation) yoğunluk:

| | atanan ρ | toplam ρ | ayrışma | P (toplam yoğunlukla) |
|---|---|---|---|---|
| M0 / matris | 1687,5 | 1800,4 | **+%6,7** | **1,117e+09 Pa** |
| M1 / matris | 1687,5 | 1800,4 | **+%6,7** | **1,117e+09 Pa** |
| M1 / blok | 2571,4 | 1800,4 | **−%30,0** | **−7,624e+09 Pa** |

ADR-0015 iki yoğunluk yöntemini de destekliyor. Aynı sahne, biriyle P = 0
(tasarım gereği), diğeriyle bloklarda **−7,6 GPa yapay çekme** veriyordu.
Yani ablasyon karşılaştırması geçersizdi ve süreklilik yolunda da kuvvetler
%6,7–30 yanlı hesaplanıyordu.

## Neden hiçbir kriter görmedi

- **G3 C2** kütle bütçesini ölçüyor (`bulk_density` geri okunuyor) — `m`
  kullanır, geçer.
- **G3 C3** gerilmesiz başlangıcı ölçüyor (`a_SPH = 0` tam olarak) — `rho`
  kullanır, geçer.
- İkisi **birbiriyle çelişiyor** ve **hiçbir kriter tutarlılığa bakmıyordu**.

ADR-0029'daki kök nedenin aynısı: parçalar ayrı ayrı doğru, bütün sınanmamış.

## Karar

**1. Kütle gözeneklilikten türer — bağımsız verilmez:**

```python
rho_i = rho0_solid / alpha0_i        # parçacığın YIĞIN yoğunluğu
m_i   = rho_i * V_p
```

Bu bir tercih değil, SPH tutarlılığının ve ADR-0022'nin birlikte zorunlu
kıldığı sonuçtur. `rho0_solid` artık üreticiye **verilmek zorunda** — kusurun
kök nedeni, üreticinin `rho0`'ı hiç bilmemesiydi.

**2. `bulk_density` bir HEDEFTİR, `matrix_alpha0` ondan ÇÖZÜLÜR:**

```
rho_yığın = f * (rho0/alpha_blok) + (1-f) * (rho0/alpha_matris)
```

`f` blokların parçacık kesridir ve ancak yerleştirmeden **sonra** bilinir;
bu yüzden çözüm yerleştirme sonrası yapılır. `matrix_alpha0=None`
(yeni varsayılan) bunu ister.

**3. Açık bir `matrix_alpha0` verilirse ve hedefi tutturmuyorsa HATA verilir**
— hedefi tutturan değeri de söyleyerek. Sessizce farklı bir cisim üretmek,
gözeneklilik çıkarımının girdisini görünmeden kaydırırdı; projenin asıl
çıkarım parametresi tam olarak gözenekliliktir.

**4. `matrix_alpha0` konfigürasyonlardan çıkarıldı.** Türetilen bir büyüklüğü
elle yazmak, çelişkiyi geri getirmenin en kolay yoludur.

## Düzeltme sonrası ölçüm

| | M0 homojen | M1 bloklu |
|---|---|---|
| çözülen `matrix_alpha0` | **1,5000** | **1,7273** |
| yığın yoğunluğu (hedef 1800) | 1800,0000 | 1800,0000 |
| hacim tutarlılığı `m/(rho·V_p)` | **[1,000000 ; 1,000000]** | **[1,000000 ; 1,000000]** |
| birim bölünmesi — matris | 1,0002 | 1,0002 |
| birim bölünmesi — blok | — | **1,0002** |
| blok kütlesi / matris kütlesi | — | **+%65** |

M0 için çözülen değer **tam 1,5000** çıkıyor — konfigürasyonun kendi
yorumundaki "%33 gözeneklilik" tam olarak budur. Yani doğru değer zaten
belgede yazılıydı, parametrede yanlış yazılmıştı.

Bloklar artık gerçekten **%65 daha ağır**: katı kaya, gözenekli matristen
yoğundur. Önceden aynı kütleye sahiplerdi, yani "blok" yalnızca bir etiketti.

## Kalan sınır (yeni kusur değil)

M1'de atanan ve toplam yoğunluk hâlâ ayrışıyor (matris +%20,3, blok −%11,0).
Bu **bookkeeping değil, fizik**: SPH toplam yoğunluğu keskin bir yoğunluk
sıçramasını çekirdek genişliğinde yumuşatır. Kanıtı, birim bölünmesinin artık
her iki malzemede de 1,0002 olması — interpolasyon tutarlı, yumuşama ise
süreklilik yoğunluğunun neden seçildiğinin (ADR-0015) doğrudan gerekçesi.
M0'da ayrışma **+%0,0**'a düştü; yani eski +%6,7 tamamen bookkeeping hatasıydı.

## Ek — kütle heterojenleşince ortaya çıkan iki hasar kusuru

Kütleler artık parçacıktan parçacığa değiştiği için, hasar modülünün hacim
kullanımı sınandı. **İki farklı hacim** vardır ve karıştırılıyorlardı:

| kullanım | doğru hacim | eski kod |
|---|---|---|
| kusur yoğunluğu (Weibull) | **katı** `m/rho0` | `mean(m)/rho0` — tek değere indirgenmiş |
| çatlak yolu (`r_s`) | **geometrik** `m·alpha/rho0` | katı hacim — gözenekler sayılmıyor |

**Kusur 1 — `r_s` gözenekleri saymıyordu.** `damage_ref.damage_rate` `r_s`'yi
açıkça *"çatlağın kat etmesi gereken uzunluk"* diye tanımlar; çatlak gözenekler
dahil bütün parçacığı geçer. Ölçüldü (α = 1,5):

```
r_s mevcut (katı hacimden)  = 3,8624 m
r_s doğru  (geometrik)      = 4,4214 m      -> %12,6 küçük
dD/dt ~ 1/r_s               -> hasar %14,5 HIZLI büyüyordu
```

**Kusur 2 — kusurlar hacimden bağımsız dağıtılıyordu.** `seed_flaws`
sahipliği `rng.integers` ile **tekdüze** seçiyordu; bu yalnızca bütün hacimler
eşitken doğrudur. ADR-0030'dan sonra M1 yığınında katı hacim gerçekten
değişiyor (**blok 344,8 · matris 209,6 m³ — %56 yayılım**) ve tekdüze dağıtım
gözenekli matrise hak ettiğinden fazla kusur verirdi.

Düzeltme: sahiplik hacimle orantılı (ters-CDF, aynı RNG akışı, deterministik).
Ölçüldü: 2× hacim → **1,9775× kusur** (beklenen 2,0); tekdüze hacimde iki yarı
arası oran **0,9977** (beklenen 1,0).

`geometrik hacim = m·alpha/rho0` her parçacıkta **tam olarak kafes hacmi
V_p = 362,04 m³** çıkıyor — ADR-0030 tutarlılığının bağımsız bir doğrulaması.

## Altın sahne karması

Kütleler değiştiği için `Scene.digest` değişti:
`6d6f1d10eaff64e2…` → `ca730c2c8fa666b1…`. Altın dosya ADR-0025'in
mekanizmasıyla, eski karma `history` altına gerekçesiyle yazılarak yenilendi.
Bu, mekanizmanın **amacına uygun çalıştığının** kanıtıdır: sessiz bir kütle
değişikliğini durdurdu.
