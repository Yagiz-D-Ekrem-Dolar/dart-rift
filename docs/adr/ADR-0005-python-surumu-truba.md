# ADR-0005 — Python sürümü: 3.10 taban (TRUBA merkezî modül kısıtı)

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-27
- **İlgili karar:** Ana Plan Karar 2 ("NVIDIA Warp + Python 3.11+")

## Bağlam
Ana Plan uygulama yığınını "Python 3.11+" olarak kilitler. Ancak TRUBA
kullanım kuralları `/arf` dosya sistemine conda/pip kurulumunu yasaklar ve
merkezî modül kullanımını zorunlu kılar. ARF-ACC'deki merkezî AI modülü
(`apps/truba-ai/gpu-2024.0`) **Python 3.10.15** sağlar.

## Değerlendirilen seçenekler
1. `/arf`'a kendi 3.11 ortamını kurmak: TRUBA kuralı ihlali (yüz binlerce inode).
2. Apptainer konteyneri ile 3.11: mümkün ama FAZ 0 için ölçüsüz operasyonel yük.
3. **Tabanı 3.10'a çekmek (seçilen):** kod 3.10+ uyumlu yazılır; CI 3.10 ve
   3.12 matrisinde test eder.

## Karar
`requires-python = ">=3.10"`. 3.11+'a özgü sözdizimi kullanılmaz. CI matrisi
{3.10, 3.12} ile hem TRUBA hem güncel yerel ortam temsil edilir. Ana Plan'daki
"3.11+" ifadesinden bu sapma, işlevsel hiçbir kilitli kararı (Warp, HDF5,
determinizm) değiştirmez; kaynak kısıtı kaynaklıdır ve bu ADR ile kayıt altındadır.

## Sonuçlar
- (+) TRUBA merkezî modülüyle kurulumsuz çalışma; kural ihlali yok.
- (+) warp-lang wheel'i job-yerel diske (`$TMPDIR`) açılır; `/arf` kirletilmez.
- (−) 3.11 `tomllib`/`Self` gibi kolaylıklar kullanılamaz (FAZ 0'da gerek yok).

## İlgili testler
CI matrisi (`.github/workflows/ci.yml`), TRUBA G0 kapı koşusu (SLURM logu)
