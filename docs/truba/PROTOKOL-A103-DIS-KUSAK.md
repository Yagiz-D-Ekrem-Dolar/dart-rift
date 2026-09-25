# Protokol A103 — geç `β` farkını merdivenin dış kuşağı mı taşıyor?

**Yazıldı:** 2026-09-26, **`A103_dis2` koşusundan ÖNCE**.

**Kilitlemeden önce bilinenler** (tümü mevcut koşulardan, salt okur; §1):
- UY sonuçları;
- PROTOKOL-A98'in iki kolu (`A98_k_av1`, `A98_k_av01`);
- kaçan momentumun başlangıç konumuna göre dağılımı
  (`claude-cozunurluk-20260925/ejekta_koken.py`).

`A103_dis2` hiç koşulmadı.

**Öncül:** PROTOKOL-UY, PROTOKOL-A98, `docs/COZUNURLUK-DENETIMI.md`, rapor
A103 (`docs/FAZ4-SIKINTI-RAPORU.md`).
**Rapor:** `scripts/a103_dis_kusak_raporu.py` → `S_A103.json` (kilitli).
**İş:** `truba/is_A103_dis_kusak.slurm`.

---

## 1. Neden (keşif, yargı değil)

UY'de `β(300 s)` kaba `3,686`, iç `3,823`, orta `3,978`. A98'in iki kolu
şunu gösterdi: geç evre AV'sini `0,1`'e indirmek kabada `β`'yı **düşürdü**
(`3,686 → 3,476`). Yani "AV frenini azalt → kaba orta'ya yaklaşır"
beklentisi tam sahnede tutmadı (A98 notu).

Kaçan hedef maddesinin **başlangıç konumuna** göre eksenel momentumu,
kaba (`A98_k_av1`) ve orta (`UY_orta`), ikisi de 300 s'de [kg m/s]:

| çarpma noktasına uzaklık | kaba | orta | fark |
|---|---|---|---|
| 0–3 m | 1,713e6 | 1,583e6 | −0,130e6 |
| 3–6 m | 1,407e6 | 1,446e6 | +0,039e6 |
| 6–12 m | 2,290e6 | 2,427e6 | +0,138e6 |
| **12–18 m** | 1,390e6 | 1,796e6 | **+0,405e6** |
| **18–24 m** | 0,923e6 | 1,189e6 | **+0,267e6** |
| **24–36 m** | 0,336e6 | 0,494e6 | **+0,158e6** |
| toplam | 8,059e6 | 8,935e6 | +0,876e6 |

Farkın **%95'i** (`0,830e6`) 12–36 m'den başlayan maddeden geliyor. Kaba
merdivende orada aralık 2,8–5,6 m (`h = 5,6–11,2 m`); geç krater ~36 m'ye
kadar büyüyor (36–48 m'den kaçan yok). İç kolda (iç 12 m 2×) kazanç
**inceltilen** kuşaktan geldi (6–12 m `+0,33e6`). 12–24 m'lik kuşak, kaba ile
iç kolda aynı çözünürlükte; oradan kaçan kütle iki kolda birebir aynı
(`1,5522e7 kg`).

> **Hipotez (A103):** geç `β` farkı yereldir. Her kuşağın katkısı o kuşağın
> kendi çözünürlüğüyle belirlenir; farkın çoğunu, geç kraterin oluştuğu dış
> kuşak (12–48 m) taşır. Merdiven şok için tasarlanmış (ince bölge çarpma
> noktasında); geç krater ise kaba kuşaklarda oluşuyor.

## 2. Tasarım

UY ve A98 ile **aynı** her şey:
- L1 küresi, `Y₀ = 10 Pa`, `t_geçiş = 0,2 s`, `A_geç = 1e5 Pa`;
- AV `(1, 2)`, dondurma, yerçekimi;
- kod: A98 ağacı `agac_a98` = `SABIT_COMMIT` `b738992`, yani UY fiziği.

Tek fark merdiven:

| kol | merdiven | not |
|---|---|---|
| `A103_dis2` | `48:2.8 24:1.4 6:0.7 3:0.35` | 12–48 m 2× ince, iç 12 m kaba ile aynı (`n = 32 985`) |

Kıyas kolları (yeniden koşulmaz): kaba `A98_k_av1` (R0'da W2 ile aynı),
iç `UY_ic`, orta `UY_orta`. `A103_dis2`, UY'deki iç kolun **tümleyenidir**.

Merdivende aynı aralıklı iki ardışık kademe yazılamıyor (`λ` içe doğru kesin
artmalı). Bu yüzden `24:1.4`, 6–24 m'yi kapsar. Kabanın `12:1.4` kademesi zaten
6–12 m'de 1,4 m; iç bölge değişmez.

## 3. Geçerlilik

Her kol `gecerli = True` olmalı ve 300 s'ye ulaşmalı. Değilse o kol eksik
sayılır ve bütün yargılar OKUNMAZ. Rapor **beklenen dört kolu** sayar.

## 4. Kilitli yargı

`β` = `β(300 s)`, UY raporunun log-zaman aradeğeri (`beta_aninda`).
Tanımlar:
- `Δ_dış = β_dış2 − β_kaba`
- `Δ_tümleyen = β_orta − β_iç` (UY'de `0,1555`)
- `Δ_toplam = β_orta − β_kaba` (`0,2920`)

**Y1 — yerellik ve toplamsallık:**
`|Δ_dış − Δ_tümleyen| ≤ 0,05` → **KUŞAK KATKILARI YEREL VE TOPLAMSAL**;
değilse **TOPLAMSAL DEĞİL**.

**Y2 — ANA YARGI:**
`Δ_dış / Δ_toplam ≥ 0,5` → **DIŞ KUŞAK (12–48 m) FARKIN ÇOĞUNU TAŞIYOR**;
değilse **DIŞ KUŞAK FARKIN AZINI TAŞIYOR**.

**Y3 — kuşak ejektası:** 12–36 m'den başlayan kaçan maddenin momentumu
(yöntem §1, `kusak_momentumu`).
`|P_dış2 − P_orta| / P_orta ≤ 0,10` → **DIŞ KUŞAK EJEKTASI ORTA İLE AYNI**;
değilse **ORTADAN FARKLI**.

`genel` = Y2.

## 5. Dürüst sınırlar

- Tek bir ek koşu. Yerelliği **sınar** ama gereken çözünürlüğü
  **belirlemez**. Dış kuşakta yakınsama için daha ince bir seviye gerekir
  (A103 notundaki öneri).
- `Y₀ = 10 Pa` bu sahnede kraterin büyük olduğu durum (~0,5 R). Daha
  dayanıklı hedefte krater küçülür ve sorunlu kuşak içe kayar. Sonuç Y₀'a
  genellenmez.
- Hiçbir ayar gözlenen DART `β`'sına göre yapılmaz.

## 6. Maliyet

`n = 32 985`, en küçük `h` mermide ve üç merdivende aynı (0,19 m). Kaba
80 dk sürdü, bu kol `~2–4 sa` bekleniyor. **1 GPU**, süre sınırı 16 sa.
Otomatik yeniden gönderim yok.
