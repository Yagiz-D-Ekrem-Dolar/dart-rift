# G2 Kapi Raporu — "Gercek malzeme fizigi"

- Tarih (UTC): 2026-07-28T14:27:50.039945+00:00
- Makine: kolyoz23 / Linux-5.14.0-427.13.1.el9_4.x86_64-x86_64-with-glibc2.34
- Cihaz: cuda:0 
- pytest: cikis 0

| # | Kriter | Sonuc | Kanit |
|---|--------|-------|-------|
| C1 | Rijit donme yapay gerilme uretmiyor (P2-VR-01) | **GECTI** | S es-donme hatasi 1.66%, vm drift 1.66%; Jaumann kapaliyken 200% |
| C2 | Taylor bar + elastik dalga benchmark'a yakin (P2-VR-02/03) | **GECTI** | elastik dalga (res=600) 4458 m/s vs teorik 4593 (2.96%, hata 300->600 azaliyor); Taylor L/L0=0.731 (bant 0.60-0.80), Y0 2x -> 0.824, enerji 0.083% (yogunluk: sureklilik, ADR-0015) |
| C3 | Crush curve fiziksel; alpha>=1; geri genlesme yok (P2-VR-04) | **GECTI** | cevrim: monoton+geri-genlesme-yok+is>=0; SPH: P_tepe porozlu/kati = 0.28, alpha_min=1.207 |
| C4 | Iki-cisim + duzgun kure yercekimi; drift sinirli (P2-VR-05) | **GECTI** | iki-cisim 20 yorunge: E hatasi 2.4e-07, yaricap drifti 1.3e-08; kure: BH-direct medyan 0.43%, kabuk hata maks 4.65% |
| C5 | Global korunum yercekimi dahil (P2-VR-06) | **GECTI** | soguk collapse: enerji 0.36% (pot olcegine), momentum 1.2e-17 |
| C6 | Her modul ablasyonla acilip kapanabiliyor (P2-FR-06) | **GECTI** | strength_produces_deviatoric=OK; strength_produces_plastic_work=OK; porosity_crushes_alpha=OK; no_porosity_alpha_stays_1=OK; gravity_adds_potential=OK |
| C7 | G0/G1 testleri hala geciyor (regresyon yok) | **GECTI** | pytest cikis=0; G0 altin hash + G1 sok testleri dahil tum paket |

## SONUC: G2 GECTI — FAZ 3 baslayabilir

> Benchmark gecmeyen modulun iddiasi yapilmaz; iddia daraltilir ama bilim bukulmez.

---

## Kosu kunyesi (bu dosya elle duzenlenmemistir; kaynak SLURM ciktisidir)

- SLURM is kimligi: **1426596**
- Bolum / dugum: `kolyoz-cuda` / `kolyoz23` (NVIDIA H100 80GB HBM3)
- Depo commit: `a3ecd2e`
- Ortam: Python 3.10.15, NumPy 1.26.4, warp 1.15.0, CUDA Toolkit 12.9
- pytest: **360 gecti**, 0 kaldi, 14:02
- Is duvar saati (G1+G2): 41:22, cikis kodu 0:0
- Ham cikti: `g12_1426596.out`, metrikler: `gate_runs/g2_truba_1426596/g2_metrics.json`

### C2 hakkinda not (ADR-0015)

Taylor bar enerji defteri bu kosuda **%0,083**; esik %1,5. Onceki durum
%13,95 idi. Farki yaratan sey yogunlugun toplama (summation) yerine
sureklilik denklemiyle tasinmasidir; ayrinti ve ablasyon tablosu
[ADR-0015](../adr/ADR-0015-sureklilik-yogunlugu.md) icindedir.

Bagimsiz dogrulama: `L/L0 = 0.731` literatur bandinin (0.60-0.80) icinde ve
`Y0` iki katina cikarilinca 0.824'e yukseliyor — yani daha yuksek akma
gerilmesi daha az kisalma veriyor, beklenen yon. Enerji olcutu ile sekil
olcutu ayni duzeltmeyle birlikte saglaniyor.
