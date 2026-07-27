# ADR-0004 — RNG mimarisi: SeedSequence + eleman-tohumlu shard-değişmezliği

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P0-FR-04

## Bağlam
Ensemble üretimi (FAZ 5) yüzlerce koşuya, koşu içi örnekleme milyonlarca
parçacığa dağılacak. Paralel bölünme (shard) sayısı değiştiğinde sonuç
değişirse determinizm ve yeniden-üretilebilirlik kaybolur.

## Değerlendirilen seçenekler
1. Tek global `Generator`, sıralı çekim: shard sayısına ve çekim sırasına
   bağımlı; paralelde kırılır.
2. Shard-başına `seed + shard_id`: shard sayısı değişince tüm örnekler değişir.
3. **Eleman-tohumlu spawn (seçilen):** `SeedSequence(root, spawn_key=(akış, eleman))`.

## Karar
- Kök tohum: `config.random_seed` (tek kaynak).
- Adlandırılmış akışlar **kilitli** kimliklerle: `particles=0`, `material=1`,
  `realization=2`. Bu eşleme değiştirilemez; değişiklik altın hash'leri kırar
  ve yeni ADR gerektirir.
- Shard-değişmez örnekleme: her eleman `spawn_key=(akış_id, eleman_indeksi)`
  ile kendi generatorünü kurar; sonuç yalnızca (kök, akış, indeks)'e bağlıdır.
- Toplu çekim (`stream_generator`) hızlıdır ama çekim-sırası bağımlıdır;
  yalnızca shard'lanmayan bağlamlarda kullanılır (docstring'de uyarılır).
- Altın senaryo yalnızca PCG64 uniform (tamsayı-tabanlı) çekimler kullanır;
  libm'e bağımlı dağılımlar (normal/exp) platformlar arası bit-eşitliği
  garanti etmediğinden altın yoldan dışlanmıştır.

## Sonuçlar
- (+) `n_shards ∈ {1,2,3,5,7,101}` için bit-eşit sonuç (test edildi).
- (+) Windows/Linux arası aynı altın hash.
- (−) Eleman-başına SeedSequence kurulumu toplu çekimden yavaştır; FAZ 5'te
  gerekirse vektörleştirilmiş spawn ile optimize edilir (ayrı ADR).

## İlgili testler
`tests/test_rng.py` (tamamı), `tests/test_determinism_golden.py`
