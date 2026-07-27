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

## EK KISIT (28.07.2026): kütüphane sürümü de tabana bağlıdır

Bu ADR yalnızca Python **söz dizimini** 3.10'a sabitliyordu; kütüphane API'leri
kapsam dışı kalmıştı. Bu boşluk gerçek bir kapı arızasına yol açtı.

Merkezî modül `apps/truba-ai/gpu-2024.0` şunu sağlar:

| | TRUBA (hedef) | yerel geliştirme |
|---|---|---|
| Python | 3.10.15 | 3.12 |
| NumPy | **1.26.4** | 2.x |

`np.trapz` bir kullanım dışı bırakma uyarısı verdiği için `np.trapezoid`'a
çevrilmişti. Ancak `np.trapezoid` **NumPy 2.0** ile geldi; 1.26.4'te yoktur.
Test yerelde geçti, TRUBA'da `AttributeError` verdi ve G1 kapısında **C1 ile
C6'nın ikisini birden düşürdü** (koşu 1426017): her iki ölçüt de `tests_ok`
şartına bağlıydı, dolayısıyla kütle sapması 0,00e+00 olmasına rağmen C1
"KALDI" göründü.

**Kural:** Hedef taban NumPy 1.26.4'tür. NumPy 2.0+ ile gelen API'ler
(`trapezoid`, `concat`, `vecdot`, `bitwise_count`, `permute_dims`, …)
kullanılamaz. Kaçınılmazsa `getattr(np, "yeni", None) or np.eski` biçiminde
sürümden bağımsız bir köprü yazılır (`tests/test_kernel_fn.py::_trapz`).

**Ders:** Yerelde yeşil olan bir paket, hedef ortamda yeşil olduğu anlamına
gelmez. Kapı kanıtı bu yüzden TRUBA'da üretilir — bu olayda mekanizma
amaçlandığı gibi çalıştı ve hatayı yakaladı.

## İlgili testler
CI matrisi (`.github/workflows/ci.yml`), TRUBA G0 kapı koşusu (SLURM logu),
`tests/test_kernel_fn.py` (sürümden bağımsız yamuk integrali)
