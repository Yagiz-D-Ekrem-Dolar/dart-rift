# docs/evidence/

Kapi kosularinin **degistirilmemis** ciktilari. Her kanit dosyasi, hangi
makinede ve hangi SLURM isinde uretildigini basliginda tasir.

| Dosya | Kapi | Kosu | Sonuc |
|-------|------|------|-------|
| `G0_report_truba_1425495.md` | G0 | TRUBA kolyoz19 / H100, job 1425495 | 8/8 GECTI, 185 test, kapsam %97.2 |
| `manifest_truba_1425495.yaml` | G0 | ayni kosu | Ek A alan tamligi dogrulandi |

## Kural

- Kanitlar sonradan duzenlenmez. Bir kosu yanlissa yenisi eklenir, eskisi
  silinmez; hangisinin gecerli oldugu bu tabloda belirtilir.
- Basarisiz kosular da kayitlidir (bkz. `G0_report_truba_1425495.md` sonundaki
  tablo ve `docs/defter/`).
- Kanit uretmeyen bir modul icin basari iddia edilmez.

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
