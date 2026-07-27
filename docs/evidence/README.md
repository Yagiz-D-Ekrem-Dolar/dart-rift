# docs/evidence/

Kapi kosularinin **degistirilmemis** ciktilari. Her kanit dosyasi, hangi
makinede ve hangi SLURM isinde uretildigini basliginda tasir.

| Dosya | Kapi | Kosu | Sonuc |
|-------|------|------|-------|
| **`G0_report_truba_1425590.md`** | **G0 + §12** | **kolyoz19 / H100, job 1425590 — GECERLI KANIT** | **8/8 GECTI + kirmizi takim 6/6 TEMIZ, 210 test, kapsam %97.4, temiz git agaci** |
| `G0_report_truba_1425495.md` | G0 | kolyoz19 / H100, job 1425495 — *asildi* | 8/8 GECTI, 185 test, kapsam %97.2 |
| `manifest_truba_1425495.yaml` | G0 | job 1425495 | Ek A tam; config gomulu DEGIL (sonradan giderildi) |

**Hangisi gecerli:** `1425590`. Onceki kanit (`1425495`) silinmedi, cunku sahte
degildi — o kosuda kapinin sekiz kriteri de gercekten geciyordu. Ancak teslim
oncesi oz-denetim uc kusur buldu (sessiz config sapmasi, manifestin kosuyu tek
basina yeniden urete­memesi, §12 kirmizi-takim listesinin hic isletilmemis
olmasi). Kusurlar giderilip kanit yenilendi. Iki dosyanin birlikte durmasi,
kusurun ne zaman bulundugunu ve nasil kapatildigini izlenebilir kilar.

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

Yerel (GPU'suz) dogrulama G0'i tam gecirmez: C3 kriteri gercek CUDA cihazi
ister. `--require-gpu` bayragi, GPU roundtrip atlanirsa kapiyi bilincli olarak
GECEMEDI sayar.
