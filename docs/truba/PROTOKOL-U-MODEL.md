# Protokol U — model yeterliliği: β DART gözlemine ulaşabiliyor mu?

**Yazıldı:** 2026-09-14, **koşudan ÖNCE**. Kural `scripts/u_model_raporu.py`'de
kilitli; sınavı `tests/test_u_model_raporu.py`.

## 1. Neden

Sahnenin kendi hedef kütlesiyle (`≈ 4,16e9 kg`) depo arayüzü gözlenen
`β ≈ 3,12 ± 0,34` (`β−1 ≈ 2,12`) veriyor. Plato anında (0,1–0,2 s) ölçülen
simülasyon değerleri: T orta `β−1 = 0,82–0,85`, Tkt kaba `0,92–0,97`. M
(24 ms) boyunca önseldeki en büyük değer `~0,78`. Yani **üretim modeli, önsel
boyunca, gözlenen β'nın yarısına bile ulaşmıyor olabilir.** Protokol D bunu
kilitli olarak soracak; U, cevap "ÖNSEL DIŞI (YUKARI)" çıkarsa **hangi model
bileşeninin** farkı kapatabildiğini önceden ölçer.

## 2. Tasarım

Merkez θ `(α_b 1,15 ; Y₀ 1e5 Pa ; f 0,275)`, `t = 0,1 s`, kesme + taban,
matris sahası, tohumlar `20260906`, `99991111`.

| varyant | değişiklik | gerekçe |
|---|---|---|
| U0 | yok (üretim) | taban |
| U1 | `Y₀ = 1e1 Pa` (**önsel dışı**) | çok zayıf kohezyon |
| U2 | `Y₀ = 1e0 Pa` (**önsel dışı**) | neredeyse kohezyonsuz |
| U3 | `μ_f = 0,2` | düşük iç sürtünme |
| U4 | `μ_f = 0,05` | sürtünmesize yakın |
| U5 | `Pe = 1e5`, `Ps = 1e7` | kolay ezilen gözenek |
| U6 | yığın yoğunluğu `1500` | daha gözenekli hedef (gözlenen β da kütleyle değişir) |
| U8 | U2 + U3 + U5 + U6 | en gevşek birleşim |

Kaba: 8 × 2 = 16 koşu; orta: U0 ve U8 × 2 = 4 koşu.

## 3. Yargı (kilitli)

`z = (β−1_gözlem − β̄−1_sim) / σ_β`, gözlenen `β` varyantın **kendi**
hedef kütlesiyle. `|z| ≤ 2` → **BANDA ULAŞIYOR**; `z > 2` → **ALTINDA**;
`z < −2` → **ÜSTÜNDE**. Genel: en az biri ulaşıyorsa **MODEL GÖZLEME
ULAŞABİLİYOR** (liste), aksi **HİÇBİR VARYANT ULAŞMIYOR** (en yakın).

## 4. Yorum tablosu (koşudan önce)

| sonuç | anlamı | sıradaki adım |
|---|---|---|
| U1/U2 ulaşıyor | `Y₀` önseli (`≥ 1e3 Pa`) gerçek Dimorphos'u dışarıda bırakıyor | ADR: önsel alt sınırı `1 Pa`'ya; N/P yeniden |
| U3/U4 ulaşıyor | iç sürtünme bir **çıkarım parametresi** olmalı | ADR: θ'ya `μ_f` eklenir |
| U5/U6 ulaşıyor | gözeneklilik/yoğunluk varsayımı belirleyici | ADR: sahne varsayımı |
| yalnız U8 | tek bileşen yetmiyor, birleşim gerekiyor | çok boyutlu önsel genişletme |
| hiçbiri | model bu fizikle (yerçekimsiz, 0,1 s, SPH) DART β'sını üretmiyor | yerçekimi / uzun zaman / ejekta modeli; Bitiş 3 sonucu "model gözleme ulaşmıyor" diye yazılır |

## 5. Sınırlar

- Tek θ, tek faktör; etkileşimler yalnız U8'de.
- Kaba çözünürlükte β mutlak değeri kayık (M); orta satırlar (U0, U8)
  kaymanın yönünü gösterir.
- Önsel dışı varyantlar çıkarım havuzlarına **girmez** (`onsel_disi = true`).
