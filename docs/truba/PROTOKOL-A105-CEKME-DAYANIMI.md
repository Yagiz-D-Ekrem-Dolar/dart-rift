# Protokol A105 — çözünürlük farkını "çekmesiz ayrılma" mı taşıyor? (granüler çekme dayanımı)

**Yazıldı:** 2026-09-26, **A105 koşularından ÖNCE**.

**Kilitlemeden önce bilinenler:**
- UY, UG, A98 (5 kolun 4'ü; `k_p6400` koşuyor), A98K, A103;
- A104 koşuyor, sonuç yok;
- kontrollü akış keşif koşuları (TRUBA `claude-cozunurluk-20260925/`,
  işler `1579566`, `1579567`; kilitli değil):
  - Q, h'ye bağlı, parçacık sayısına değil: aynı `h = 1,5`'te `s = 1` ile
    `s = 0,5` arasında fark `%1,6`;
  - çekme sınırı `T = 10 Pa`, `s = 1`'de geç Q'yu `%79` düşürüyor;
  - `T = 10 Pa`'da `s = 1 → 0,5` bağıl Q değişimi `−%34` (T = 0'da
    `+%16`), yani kontrollü akışta bağıl çözünürlük duyarlılığı kalkmadı;
  - `s = 0,25` kolları bu protokol yazılırken koşuyordu.

Hiçbir A105 kolu koşulmadı.

**Öncül:** `docs/COZUNURLUK-DENETIMI.md` §8.4.
**Rapor:** `scripts/a105_cekme_raporu.py` → `S_A105.json` (kilitli).
**İş:** `truba/is_A105_cekme.slurm`.

---

## 1. Neden

Geç evreye ilişkin bulgular (§8.4):
- Geç evrede basınç pratikte sıfır. Madde çekme taşıyamadığı için
  (`P ≥ 0` kırpık, `--matris-cekme-yok`) hacimsel olarak karşılıksız ayrılıyor.
- Geç ejekta (12–36 m) sığ bir katmandan fırlıyor: kaynak derinliği medyan
  `~4 m`. Bu katman kabada `h = 5,6 m`, ortada `2,8 m` ile çözülüyor.
- Kontrollü akışta 10 Pa'lık bir çekme sınırı fırlayan momentumu `%79`
  düşürüyor.

Model kaymada `Y₀ = 10 Pa` kohezyon taşıyor, çekmede **hiç** taşımıyor.
Mohr–Coulomb / Drucker–Prager tutarlılığı çekme tepesini
`T = Y₀ / μ_f = 10 / 0,6 = 16,7 Pa`'ya koyar. Sıfır çekmeli ayrılmanın
doğal uzunluk ölçeği yok; ayrılan katmanın kalınlığını ayrıklaştırma
belirleyebilir.

**Soru (C1):** Kaba–orta farkını taşıyan bu çekmesiz ayrılma mı?

## 2. Tasarım

UY, A98 ve A103 ile **aynı** her şey:
- L1 küresi, `Y₀ = 10 Pa`, `μ_f = 0,6`, `t_geçiş = 0,2 s`, `A_geç = 1e5 Pa`;
- AV `(1, 2)`, dondurma, yerçekimi;
- kod `agac_a98` (`SABIT_COMMIT` `b738992`).

**Tek fark:** `--matris-cekme-siniri 16.666666666666668`, yani
`P_eff = max(P, −T_m)`. Bloklar ve mermi zaten kırpılmıyor; bu sahnede
`f = 0`.

| görev | ad | merdiven | `T_m` |
|---|---|---|---|
| 0 | `A105_k_T` | kaba | `Y₀/μ_f` |
| 1 | `A105_o_T` | orta (`48:2.8 … 3:0.175`) | `Y₀/μ_f` |

Kıyas kolları (yeniden koşulmaz):
- kaba `A98_k_av1` (`T_m = 0`);
- orta `UY_orta` (`T_m = 0`).

`T_m` değeri akma doğrusunun çekme tepesinden seçildi. **DART `β`'sına
göre ayarlanmadı.** Erken evrede (`P ~ MPa–GPa`) etkisiz.

## 3. Geçerlilik

Her kol `gecerli = True` olmalı ve 300 s'ye ulaşmalı. Değilse o kolun
girdiği yargı OKUNMAZ. Rapor **beklenen dört kolu** sayar.

## 4. Kilitli yargı

`β = β(300 s)` (`beta_aninda`). Bağıl çözünürlük farkı
`g = (β_orta − β_kaba) / β_orta`:
- `g₀` `T_m = 0`'da,
- `g_T` `T_m = Y₀/μ_f`'de.

**C1 (ana), `r = g_T / g₀`:**

| yargı | koşul |
|---|---|
| **ÇEKMESİZ AYRILMA ÇÖZÜNÜRLÜK FARKININ ÇOĞUNU TAŞIYOR** | `|r| ≤ 0,5` |
| **… BİR KISMINI TAŞIYOR** | `0,5 < |r| < 1` |
| **… TAŞIMIYOR** | `|r| ≥ 1` |

**C3 (tanı; model duyarlılığı):**
`Δ = β_kaba(T_m) − β_kaba(0)`. `|Δ| > 0,1` →
**BETA ÇEKME DAYANIMINA DUYARLI**, değilse **DUYARSIZ**.

Ek tanı (yargısız): geç artış `β(300 s) − β(3 s)` her kolda.

`genel` = C1.

## 5. Dürüst sınırlar

- `T_m` bir **fizik** parametresidir, sayısal bir düzeltme değil. C1
  "ÇOĞUNU TAŞIYOR" çıksa bile `T_m`'yi üretime almak kullanıcının
  fizik kararıdır (ADR). BULGULAR §6 bunu zaten "ADR gerekiyor" diye açık
  tutuyor.
- C3 "DUYARLI" çıkarsa `β` çıkarımı `T_m` seçimine bağlıdır. Bu sonuç
  gizlenmez.
- Tek `θ` noktası (`Y₀ = 10 Pa`, `f = 0`), tek `T_m` değeri, iki
  çözünürlük. Yakınsamayı kanıtlamaz.
- Kontrollü akışta `T = 10 Pa` bağıl çözünürlük duyarlılığını kaldırmadı
  (bilinenler). C1'in "TAŞIMIYOR" çıkması da olasıdır ve öyle yazılır.
- Hiçbir ayar gözlenen DART `β`'sına göre yapılmaz.

## 6. Maliyet

- **Görev 0:** `n = 14 616`, beklenen `~1–2 sa`.
- **Görev 1:** `n = 66 601`, beklenen `~5 sa`.
- Toplam `≤ ~7 GPU-sa`, **2 GPU**, süre sınırı 16 sa.
- Otomatik yeniden gönderim yok.
