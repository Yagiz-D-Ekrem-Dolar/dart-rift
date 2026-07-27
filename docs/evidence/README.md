# docs/evidence/

Kapi kosularinin **degistirilmemis** ciktilari. Her kanit dosyasi, hangi
makinede ve hangi SLURM isinde uretildigini basliginda tasir.

| Dosya | Kapi | Kosu | Sonuc |
|-------|------|------|-------|
| **`G0_report_truba_1425656.md`** | **G0 + §12** | **palamut4 / A100, job 1425656 — GECERLI KANIT** | **8/8 GECTI + kirmizi takim 6/6 TEMIZ, 219 test, kapsam %97.1, temiz git agaci** |
| `G0_report_truba_1425590.md` | G0 + §12 | kolyoz19 / H100, job 1425590 — *asildi* | 8/8 GECTI + 6/6 TEMIZ, 210 test, kapsam %97.4 |
| `G0_report_truba_1425495.md` | G0 | kolyoz19 / H100, job 1425495 — *asildi* | 8/8 GECTI, 185 test, kapsam %97.2 |
| `manifest_truba_1425495.yaml` | G0 | job 1425495 | Ek A tam; config gomulu DEGIL (sonradan giderildi) |

Uc kanit da gercek kosulardir ve hicbiri sahte degildi; her turda yapilan
oz-denetim yeni kusurlar buldugu icin kanit yenilendi. Toplam bes kusur
bulundu ve kapatildi (ayrintilar: `docs/defter/KAYIT-002` ve `KAYIT-003`).

**Uc GPU mimarisinde bit-esit roundtrip:** sm_80 (A100, job 1425656),
sm_90 (H100, job 1425590), sm_86 (yerel RTX 3050). Altin hash iki isletim
sisteminde ayni.

**Hangisi gecerli:** `1425590`. Onceki kanit (`1425495`) silinmedi, cunku sahte
degildi — o kosuda kapinin sekiz kriteri de gercekten geciyordu. Ancak teslim
oncesi oz-denetim uc kusur buldu (sessiz config sapmasi, manifestin kosuyu tek
basina yeniden urete­memesi, §12 kirmizi-takim listesinin hic isletilmemis
olmasi). Kusurlar giderilip kanit yenilendi. Iki dosyanin birlikte durmasi,
kusurun ne zaman bulundugunu ve nasil kapatildigini izlenebilir kilar.

## Kapi kosusu nasil uretilir

| Kapi | Betik | GPU sarti |
|------|-------|-----------|
| G0 | `scripts/run_g0_gate.py` | CPU<->GPU roundtrip icin CUDA |
| G1 | `scripts/run_g1_gate.py` | Sedov 3B icin CUDA (zorunlu) |
| G2 | `scripts/run_g2_gate.py` | Taylor bar icin CUDA (zorunlu) |

TRUBA'da ucu birden: `sbatch --exclude=kolyoz13,palamut5,palamut6 slurm/faz12_gates.sh`

Uc kapi kosucusu da CUDA bulunmayan makinede **GECTI iddia etmez**: raporu
"ON-KONTROL (KAPI DEGIL)" basligiyla uretir ve exit 2 doner.

## Kural

- Kanitlar sonradan duzenlenmez. Bir kosu asilirsa yenisi eklenir, eskisi
  silinmez; hangisinin gecerli oldugu bu tabloda belirtilir.
- Basarisiz kosular da kayitlidir (bkz. gecerli kanit dosyasinin sonundaki
  altyapi arizasi tablosu ve `docs/defter/`).
- Kanit uretmeyen bir modul icin basari iddia edilmez.
- Donanim/altyapi arizasi ile kapi basarisizligi ayri raporlanir: SLURM betigi
  arizali dugumde EX_TEMPFAIL (75) ile cikar, bu bir kapi sonucu degildir.

## Kanit yeniden uretimi

```bash
# TRUBA giris dugumu
cd /arf/scratch/<grup>/driftclaude/dart-rift
sbatch slurm/faz0_g0_gate.sh
# cikti: gate_runs/g0_truba_<JOBID>/{G0_report.md,manifest.yaml,pytest_full.log,coverage.json}
```

Yerel (GPU'suz) dogrulama G0'i **gecirmez ve gectigini iddia etmez**: C3
kriteri gercek bir CUDA cihazi ister. CUDA bulunmayan bir makinede kapi
kosucusu C3'u "KANITLANAMADI" isaretler, raporu "ON-KONTROL (KAPI DEGIL)"
basligiyla uretir ve exit 2 doner. Bilincli on kontrol icin:

```bash
python scripts/run_g0_gate.py --allow-no-gpu --run-dir /tmp/onkontrol
```

Bu mod da hicbir kosulda "G0 GECTI" yazmaz. Davranis, gercek bir GPU'suz
ortamda (GitHub CI runner) her push'ta dogrulanir.

## Kuyruk notu

Kanit kosusu `-C H100` ile kolyoz kuyruguna ayarlidir. `palamut-cuda` (A100)
uzerinde kosarken kisit komut satirindan gecersiz kilinir:

```bash
sbatch -p palamut-cuda -C palamut --exclude=palamut5 slurm/faz0_g0_gate.sh
```
