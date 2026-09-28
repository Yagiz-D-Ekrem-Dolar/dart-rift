# ADR-0051 — Çıkarımın kalibrasyonu, tanımlanabilirlik ve kaynaklı model eksikliği

**Durum:** ÖNERİ (karar kullanıcıda) · **Tarih:** 2026-09-19 (kod), 2026-09-28 (belge)
**Öncül:** `docs/SONUC-M-N-P-J-T.md` §1 (P2 **KALİBRASYON DÜŞTÜ**, P-v4b GP
**AŞIRI GÜVENLİ**), ADR-0050 (tarih eşleme), KAYIT-067, KAYIT-069
**Kod:** `inference/kalibrasyon.py`, `inference/tanimlanabilirlik.py`,
`inference/gp_vekil.py` (`gp_varyans_kalibre`), `inference/tarih_esleme.py`,
`observables/dart_gozlemleri.py` · **Sınav:** `tests/test_adr0051_istatistik.py` (22)

---

## 1. Bağlam — üç ayrı kusur, üç ayrı çare

| kusur | kanıt | sonucu |
|---|---|---|
| **posterior kalibre değil** | P2 dış örneklem: `Y₀` kapsama68 `0,26`, `f` `0,46`, `α_b` `0,43`; P-v4b GP `0,34–0,44` | iddia ettiğimiz `%68` aslında `%30`; bant çok dar |
| **hangi parametre veriden geliyor belirsiz** | N/P-v4: `α_b` hiçbir gözlem vektöründe çözülmüyor; L2/L11/L15: aynı `β`'yı birçok iç yapı üretiyor | "posterior çıktı" demek yetmiyor |
| **model eksikliği tahmindi** | `MODEL_EKSIKLIGI` dört sayı, hiçbiri bizim kodumuzla ölçülmemişti | payda uydurma; `I < 3` kararı havada |

## 2. Karar

### 2a. Kalibrasyon **sınanır**, varsayılmaz (SBC)

`inference/kalibrasyon.py`: gerçek `θ` **önselden** çekilir → veri üretilir →
posterior hesaplanır → gerçeğin posterior CDF'deki yeri (PIT) kaydedilir.
Kalibre çıkarımda PIT `U(0,1)`'dir (Cook ve diğ. 2006; Talts ve diğ. 2018,
arXiv:1804.06788). Eşikler **ölçümden önce** sabit:

| tanı | koşul |
|---|---|
| AŞIRI GÜVENLİ | `%68` kapsama `< 0,68 − 2 SE` |
| AŞIRI TEMKİNLİ | `%68` kapsama `> 0,68 + 2 SE` |
| YANLI | ortalama PIT `0,5`'ten `2 SE` uzak |
| KALİBRE | hiçbiri **ve** KS `p ≥ 0,05` |

G4-C (tek `θ`) **kaldırılmaz**, yanına konur: tek noktada bant gerçeği
içerebilir ama posterior sistematik olarak dar olabilir.

### 2b. GP varyansı **çapraz doğrulamayla** kalibre edilir

`gp_varyans_kalibre` (Bachoc 2013, *CSDA* 66, 55): bırak-bir-grup artıklarının
Mahalanobis ortalaması `k`; kalibre GP'de `E[k] = 1`. Ortalama değişmez,
varyans `k` ile çarpılır. Varsayılan `yalniz_buyut=True`: `k < 1` olsa bile
varyans **küçültülmez** (az noktayla ölçülen bir ölçekle posterioru daraltmak
kanıtlanmamış kesinliktir). `varyans_carpani = 1` → eski davranış **bit-aynı**.

### 2c. Tanımlanabilirlik **ayrıca** raporlanır

`inference/tanimlanabilirlik.py`, üç bağımsız tanı:

1. **posterior daralması** `c = 1 − Var_post/Var_önsel` (Schad ve diğ. 2021)
2. **profil olabilirlik** (Raue ve diğ. 2009): profil iki yönde `1,92`
   düşmüyorsa o yönde **pratik olarak tanımlanamaz**
3. **Fisher yönleri** `F = JᵀΣ⁻¹J`: `rank(F) ≤ min(k, d)`

Üçüncüsü kilit: **`k` gözlenebilirle en çok `k` yön öğrenilir.** Yalnız `β`
ile (k = 1) üç parametreden **en çok bir birleşim** çözülür. Bu bir
simülasyon kusuru değil, aritmetik. Sonucu: `α_b`'yi çözmek için `β`'nın
yanına en az iki bağımsız gözlenebilir gerekir (ejekta kütlesi
`1,6 ± 0,3 × 10⁷ kg`; koni açısı — **A95 düzeltilmeden değil**).

### 2d. Model eksikliğinin her terimi **kaynaklıdır**

`MODEL_EKSIKLIGI_KAYNAKLI`: her terim `(değer, kaynak)`. Ölçülmemiş terim
`nan`'dır ve **seçilirse hata verir** — ölçülmemiş bir terimi sessizce sıfır
saymak, ölçülmemiş bir kesinlik iddiasıdır. Ölçülenler: uzak alan
çözünürlüğü `0,004` (UA), plato `0,01` (W2). Literatürden: çarpma yeri
`0,10` (L12), mermi geometrisi `0,15` (L9, üst sınır), hedef şekli `0,20`
(L1, üst sınır), çarpma açısı `0,05`. Bekleyen: yakın alan çözünürlüğü ve
geçiş anı (UY/UG sonuçlandı → ADR-0052 kaydına taşındı), kod kıyası
(üretim geçiş anında yeniden ölçülecek).

### 2e. Gözlem sabitleri tam metinden

Daly ve diğ. 2023 (Nature 616, 443) Tablo 1 okundu: hız `6144,9 ± 0,3 m/s`,
uzay aracı kütlesi `579,4 ± 0,7 kg`, şekil merkezinden `25 ± 1 m`, normale
`17 ± 7°`, çarpma yerinin yanında iki blok (`6,5 m` ve `6,1 m`). Eski
`CARPMA_ACISI` (arama özeti) **yerinde kaldı**, tam metin sürümü yanına
kondu.

## 3. Sonucu

- P2'nin "kalibrasyon düştü" sonucu artık **teşhis edilebilir**: aşırı
  güvenli mi, yanlı mı, dağınık mı ayrı ayrı görünüyor.
- Aşırı güvenliliğin bilinen bir sebebi (ML varyansı) için **ölçülmüş** çare
  var.
- Bitiş 3'ün iddiası, hangi eksenin veriden geldiğini **göstererek**
  yazılacak; "üç parametreyi de çözdük" denemez.

## 4. Riskler

- SBC vekilin kendisini simülatör sayarsa yalnız **algoritmayı** sınar,
  modeli değil. Model yeterliliği için ayrı tutulan koşularla (dış örneklem)
  koşulmalı.
- CV varyans ölçeği az noktada gürültülüdür; `yalniz_buyut` bu yüzden
  varsayılan.
- Tanımlanabilirlik eşikleri (0,5 / 0,1 / 1,92 / 36) **seçimdir**; koşudan
  önce yazıldılar ve protokolde yeniden yazılmazlar.
