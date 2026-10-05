# DM ve DT sonuçları (koşular 2026-10-05, PROTOKOL-DY §7)

TRUBA `egitimg16u3`, `/arf/scratch/egitimg16u3/driftclaude/kampanya/`.
Kod **`7a2a9b0`** (`agac_dmdt` çivili ağacı; kurallar koşulardan önce
kilitli: PROTOKOL-DY §7, commit `7a2a9b0`). Rapor `agac_dodc` (`e87193d`)
ile üretildi — betik `7a2a9b0`'da da aynıydı (`--mermi-kol`/`--tohum-kol`
o commit'te eklenmişti).

| dosya | TRUBA SHA-256 |
|---|---|
| `S_DM_DT.json` | `02922cebf0c861d921893dcb079e9be7b5724cd9a1afe93c22f4a337e3f1261f` |
| `DM_tekkure_g1p0` durum npz | `20cf299f3441312c894e9facf40fbabab2d01d987343fed66892d26c84bb5d7c` |
| `DT_tohum2_g1p0` durum npz | `bb029f77485710478204fdbe770e0ca6c936cb9e306c2429e2a1117cdd6ece07` |

İşler: `1588084_0` (DM, `COMPLETED`, 05:02:10) ve `1588084_1`
(DT, `COMPLETED`, 05:00:57) — toplam **`~10,1 GPU-saat`**.

**Kilitli ölçümler:** `σ_mermi = 0,134` (ödünç `0,15` yerine),
`σ_gerçeklem(β, DART) = 0,013` (eski model `0,033` yerine).
**Yan ölçüm:** `σ_gerçeklem(M_ejekta, DART) = 0,129`.

**A114 canlı doğrulandı:** DM'nin ensemble kaydı `y: null`
(krater, çarpma ekseni kutusunda `3` parçacık buldu). DT'nin kaydı tam.
Yani DART sahnesinin üç koşusundan **ikisi** (`DY2`, `DM`) `y` üretmedi.
Ölçümler `npz`'nin `fizik_tani`'sından okunduğu için **etkilenmedi**.

Defter: KAYIT-074. Önceki tur: `DY2_DK_2026-09-30/`.
