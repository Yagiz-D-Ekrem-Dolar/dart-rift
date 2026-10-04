# DY2 ve DK sonuçları (koşular 2026-09-30, okuma 2026-10-04)

TRUBA `egitimg16u3`, `/arf/scratch/egitimg16u3/driftclaude/kampanya/`.
Kod **`f31c13d`** (`agac_dy2` çivili ağacı — A112 düzeltmesini içerir;
kurallar koşudan önce kilitli: PROTOKOL-DY §6).

| dosya | TRUBA SHA-256 |
|---|---|
| `S_DY2.json` | `976bc28ee582ffdff81c5e3f3f6aa2696123aab20b1c4b4a89e4943940aad10d` |
| `S_DK.json` | `68748b5df99f6889c7f146d28f4cc92561eb1e42d1722ba3e52fd878017075d5` |
| `DY2_dart_g1p0` durum npz | `40765c5ca015dad99478f5f8c8204fa79061da9f872dbfdb3669b8ebcc8c33f0` |
| `DK_kure_g1p0` durum npz | `76994a41664ddc5752b54dad7538fdc779b370516d7be7a10a0ebc3530ed8efc` |

Buradaki JSON'lar **sıkıştırılmış yazımdır** (alanlar ve değerler aynı;
yalnız `dosya` alanı mutlak TRUBA yolundan göreli yola kısaltıldı).
Raporlar koşulardan 4 gün sonra (2026-10-04) `scripts/dy_dart_raporu.py`
ile üretildi — betik koşulardan **önce** kilitliydi, `--kure-kol` seçeneği
dahil (commit `67f0071`, PROTOKOL-DY §6.3).

İşler: `1583605_0` (`COMPLETED`, 04:50:53) ve `1583605_1`
(`COMPLETED`, 04:48:52) — toplam **`~9,7 GPU-saat`**.

**Kilitli yargılar:** DY2 → **MODEL GÖZLEME ULAŞIYOR** (`β = 3,748`,
`I = 1,40`, kesme `3,0`). DK → aynı yargı (`β = 3,772`, `I = 1,45`).
**Kilitli ölçüm:** `σ_şekil = 0,0086` (literatürden ödünç `0,20` yerine).

Defter: KAYIT-072. Önceki tur: `UY2_DY_2026-09-29/`.
