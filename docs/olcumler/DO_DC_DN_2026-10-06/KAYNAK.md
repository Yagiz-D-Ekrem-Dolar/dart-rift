# DO, DC ve DN sonuçları (koşular 2026-10-05/06)

TRUBA `egitimg16u3`, `/arf/scratch/egitimg16u3/driftclaude/kampanya/`.

| kol | kod (çivili ağaç) | iş | süre |
|---|---|---|---|
| `DO1_Y500_g1p0` | `e87193d` (`agac_dodc`) | `1590670_0` | 04:55:54 |
| `DO2_Y5000_g1p0` | `e87193d` (`agac_dodc`) | `1590670_1` | 05:22:53 |
| `DC_cekme_g1p0` | `e87193d` (`agac_dodc`) | `1590671` | 05:09:07 |
| `DN_nisan25_g1p0` | `bf2f05d` (`agac_dn`) | `1590696` | 04:57:03 |

Toplam **`~20,4 GPU-saat`**. Dördü de `COMPLETED`, `gecerli = True`.
`src/` DN ile DO/DC arasında yalnız `tarih_esleme.py` (bütçe terimleri
sözlüğü) farklıdır; koşu yolu onu **okumuyor** (grep ile denetlendi), yani
sahne bit-aynıdır.

| dosya | TRUBA SHA-256 |
|---|---|
| `S_DO.json` | `f92cd6c414fdf1b80ed914f2b0747ccdbd9baba9e6a5cd095761be221fec57d6` |
| `S_DC_DN.json` | `afcc4df6e59182fda0213cfe069b1fb151a0e5954342d92ae9c870d985cf2395` |

**Kilitli yargılar:**
- DO → **ÖNSEL GÖZLEMİ İÇERMİYOR** (`Y₀(3,12) = 55,5 Pa`, alt kenara `−1,26` dekad;
  uydurma `GÜÇ YASASI`, `p = −0,1791`, artık `0,1198 < 0,15`)
- DC → **ÇEKME DART'TA DAHA ETKİLİ** (`σ_çekme = 0,9706`)
- DN → **L12 İLE UYUMLU** (`σ_çarpma_yeri = 0,03019`; `ONEMSIZ` eşiğini
  `0,00019` ile aştı)
- `M_ejekta` kazancı → **M_EJEKTA TANIMLAYICI** (`×1,52` vs `β` `×2,67`)

**A114:** DN'nin ensemble kaydı `y: null` (krater, kutu 0'da 3 parçacık).
DO1/DO2/DC `y` üretti ama `y[1]` (krater derinliği) **negatif**
(`−3,02 / −2,97 / −3,83 m`) — A19 duruyor.

Defter: KAYIT-076. Önceki tur: `DM_DT_2026-10-05/`.
