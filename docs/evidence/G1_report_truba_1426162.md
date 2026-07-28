# G1 Kapi Raporu — "Sok motoru calisiyor" (KRITIK go/no-go)

- Tarih (UTC): 2026-07-28T02:18:39.072891+00:00
- Makine: kolyoz9 / Linux-5.14.0-427.13.1.el9_4.x86_64-x86_64-with-glibc2.34
- Cihaz: cuda:0 
- pytest: cikis 0 (pytest_full.log)

| # | Kriter | Sonuc | Kanit |
|---|--------|-------|-------|
| C1 | Kutle korunumu ~makine hassasiyeti (P1-VR-01) | **GECTI** | maks kutle sapmasi 0.00e+00 |
| C2 | Dogrusal momentum goreli hatasi < 1e-6 (P1-VR-02) | **GECTI** | izole maks 8.39e-16; Sod duvar-impuls kapanisi 0.49% |
| C3 | Toplam enerji hatasi < %0.5 (P1-VR-03) | **GECTI** | maks enerji goreli hatasi 0.432% |
| C4 | Sod post-sok degiskenleri analitik cozume %3-5 (P1-VR-04) | **GECTI** | res=256: rho_post=0.52%; v_post=0.52%; p_post=0.67%; rho_star_left=0.80%; shock_speed=0.08% |
| C5 | Sedov sok yaricapi benzerlik cozumune ~%5 (P1-VR-05) | **GECTI** | n=64^3: r=0.2387 vs 0.2499 (4.46%) |
| C6 | Kernel + komsu + CPU<->GPU capraz testleri geciyor | **GECTI** | tests/test_kernel_fn.py + test_neighbors.py + test_sph_cross.py |
| C7 | Zaman adimi kisit-yuzdesi logu uretiliyor (P1-FR-07) | **GECTI** | her senaryoda kisit-yuzdesi ozeti mevcut ve tutarli |
| C8 | G0 determinizm altin hash'leri hala gecerli | **GECTI** | tests/test_determinism_golden.py::test_golden_hash_matches |

- Yakinsama (P1-VR-06): L1(rho) 0.02 -> 0.0134 -> 0.01107 (monoton azaliyor)
- Kesme/Balsara: bastirma orani 0.000 (esik < 0.05)
- AV parametreleri: alpha=1.0, beta=2.0 (sartname §2.5 tipik; raporlandi)
- Grafikler: sod_profile.png, sedov_profile.png

## SONUC: G1 GECTI — FAZ 2 baslayabilir

> Gorsel olarak makul krater kanit DEGILDIR; kanit test ve sayidir.

---

## Kosu kunyesi (bu dosya elle duzenlenmemistir; kaynak SLURM ciktisidir)

- SLURM is kimligi: **1426162**
- Bolum / dugum: `kolyoz-cuda` / `kolyoz9` (NVIDIA H100 80GB HBM3, surucu 580.95.05)
- Depo commit: `4dfd83c`
- Ortam: Python 3.10.15, NumPy 1.26.4, warp 1.15.0, CUDA Toolkit 12.9
- pytest: **354 gecti**, 0 kaldi, 14:11 (`pytest_full.log`)
- G1 duvar saati: 882 s
- Ham cikti: `g12_1426162.out`, metrikler: `g1_metrics.json`

### Ayni kosuda G2 ne oldu?

G2 kriterlerinin FIZIGI kostu, ancak metrik dosyasi yazilirken
`TypeError: Object of type bool_ is not JSON serializable` ile coktu
(`scripts/run_g2_gate.py:198`). Bu bir KAPI SONUCU DEGIL, raporlama
hatasidir; `dartrift.reporting.write_metrics` ile duzeltildi ve
`tests/test_reporting.py` ile sabitlendi. G2 kanitli sonucu ayri bir kosuda
uretilir — bu rapor G2 hakkinda hicbir iddia icermez.
