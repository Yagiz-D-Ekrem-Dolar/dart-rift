# ADR-0010 — Warp kernel'lerinde tipli sayaçlar; ruff UP018 istisnası

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P1-FR-01; DR-RIFT-P0 §7.2 (statik analiz CI katmanı)

## Bağlam
Warp kernel'lerinde hash-grid gezinmesi şu kalıbı kullanır:

```python
q = wp.hash_grid_query(grid, x32[i], radius32)
j = int(0)                       # <-- TIPLI tanim zorunlu
while wp.hash_grid_query_next(q, j):
    ...
```

`hash_grid_query_next` ikinci parametreyi **referansla** (`int&`) alır ve her
yinelemede günceller. Warp'ın kod üreticisi, değişkenin C++ tarafında `int`
olarak bildirilmesi için `int(0)` biçimindeki **tipli** tanımı bekler.

Ruff'ın `UP018` kuralı (*unnecessary-int-call*) bunu "gereksiz çağrı" sayıp
`j = 0`'a indirger. Bu Python tarafında eşdeğerdir; Warp tarafında değildir.
`ruff check --fix` çalıştırıldığında beş dosyada on tanım sessizce değişti ve
tüm GPU/CPU kernel derlemeleri şu hatayla düştü:

```
error: no matching function for call to 'hash_grid_query_next'
CPU kernel build failed with error code -1
```

Belirti yanıltıcıydı: hata `density` modülünde görünüyordu, oysa `density`
dosyasına hiç dokunulmamıştı — bozulma otomatik düzeltmeden geliyordu.
Warp'ın varsayılan hata mesajı derleyici çıktısını yutar; kök neden ancak
`wp.config.verbose = True` ile görülebildi.

## Değerlendirilen seçenekler
1. **Satır satır `# noqa: UP018`:** on satırda tekrar; yeni kernel yazan
   kişinin unutması çok kolay ve unutulduğunda hata yine sessizce döner.
2. **UP kural ailesini tamamen kapatmak:** projenin geri kalanında değerli
   modernleştirme uyarılarını kaybederiz.
3. **Dizin bazlı istisna (seçilen).**

## Karar
`pyproject.toml` içinde dizin bazlı istisna tanımlanır:

```toml
[tool.ruff.lint.per-file-ignores]
"src/dartrift/warp_core/*.py" = ["UP018"]
```

Gerekçe kuralın yanına yazılır. `warp_core/` dışındaki tüm kodda UP018 etkin
kalır. Warp kernel'lerinde sayaç/indeks değişkenleri **her zaman** tipli
tanımlanır (`j = int(0)`).

## Sonuçlar
- (+) `ruff check --fix` artık kernel'leri bozamaz.
- (+) Hata sınıfı bir kez ve merkezî olarak kapatıldı.
- (−) `warp_core/` içinde gerçekten gereksiz bir `int()` çağrısı yakalanmaz.
  Kabul edildi: bu dizinde `int()` çağrıları kasıtlıdır.

## Ders (yöntemsel)
Bir otomatik düzeltme aracı, yalnızca **Python semantiğini** bilir; gömülü bir
dilin (Warp kernel DSL'i) tip sözleşmesini bilmez. Derleme hatasının işaret
ettiği dosya ile hatanın **kaynağı** farklı olabilir; `git diff` bu durumda
hata mesajından daha güvenilir bir tanı aracıdır.

## İlgili testler
Tüm GPU/Warp testleri (`test_neighbors.py`, `test_sph_cross.py`,
`test_solid_cross.py`) bu regresyonu anında yakalar — kernel derlenemezse
hepsi düşer.
