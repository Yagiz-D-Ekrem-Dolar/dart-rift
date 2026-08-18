# Katkı

DART-RIFT bir **kanıt** deposu. Kod ikinci sırada: birinci sırada
"hangi sayı ölçüldü, hangi koşulda, ve neyi kanıtlıyor" var. Aşağıdaki
kurallar bundan türüyor.

## Kurulum

```bash
pip install -e ".[dev,gpu]"
pre-commit install
```

CI'ın kullandığı **sabit** araç zinciriyle çalışmak isterseniz:

```bash
pip install -c constraints-ci.txt -e ".[dev,gpu]"
```

> `constraints-ci.txt` ile `pyproject.toml` farklı işler yapıyor:
> `pyproject.toml` **alt** sınır (paket neyle çalışır), `constraints-ci.txt`
> **üst** sınır (CI neyle ölçtü). Aynı ağaç ruff 0.15 ile 191, 0.16 ile
> 183 hata veriyordu — bu yüzden lint aracının sürümü kanıdın parçası.

## Testleri koşmak

```bash
pytest tests -m "not gpu"
```

| komut | ne yapar | süre |
|---|---|---|
| `pytest tests -m "not gpu"` | GPU'suz her şey | ~2,5 sa (yerel) |
| `pytest tests/test_determinism_golden.py -q` | ADR-0004 altın hash | saniyeler |
| `pytest tests -m gpu` | CUDA gerektirir | |
| `ruff check src tests scripts` | statik analiz | saniyeler |

> Tam takım **uzun**. "Sessizce ölüyor" sanılan şey genelde zaman
> aşımıdır; arka planda koşturup çıktıyı dosyaya yazın.

## Kapılar

Her faz bir **kapı** ile kapanır (`G0`…`G4`). Kapı koşucuları
`scripts/run_g*_gate.py` altında.

> **GPU'suz bir ortamda hiçbir kapı "GEÇTİ" diyemez** ve bu CI'da ayrı
> bir job ile sınanıyor (`gates`). Koşucu GPU bulamazsa çıkış kodu `2`
> döndürür ve rapora `KANITLANAMADI` yazar. Bu koruma, kanıtın
> tamamının dayandığı kuraldır: *test geçilmediyse iddia edilmez.*

## Değiştirilemeyen kurallar (`RULES.txt`)

1. **Tarih, saat, sonuç uydurulmaz.** Kayıt yoksa "kayıt bulunamadı"
   yazılır.
2. **Testini geçemeyen modül için başarı iddia edilmez.**
3. **Kilitli bir karara sessiz değişiklik yapılmaz** — ADR gerekir.
4. **Yanlış çıkan bir iddia silinmez, notla düzeltilir.** Deponun
   değeri, nerede yanıldığının izlenebilir olmasında.

## Ölçüt önden yazılır

Bir ölçüm koşmadan önce, hangi sonucun neyi kanıtlayacağı **yazılı
olmalı** (SLURM betiğinin başına, ADR'ye veya kayıt defterine). Veriyi
gördükten sonra ölçüt seçmek, ölçümü kanıt olmaktan çıkarır.

## Çalışma noktasını kapsamayan aralıkta yargı kurulmaz

Bu depoda en sık tekrarlanan hata (KAYIT-029'un dersi): bir büyüklüğün
nasıl davrandığı, ilgilenilen çalışma noktasını **içermeyen** bir
aralıkta ölçülerek söylenemez. Şimdiye kadar `r_dep/r_şok`,
`r_iç/r_dış` ve `Y0`'da üç kez düşüldü.

## GPU değişiklikleri

Warp çekirdeği değiştirdiyseniz **CPU↔GPU çapraz kontrolü** koşmalı:
her çekirdeğin Warp'tan bağımsız bir NumPy FP64 referansı var
(`tests/test_sph_cross.py`, `tests/test_solid_cross.py`) ve ikisi
`< 1e-8` sapmayla eşleşmeli. Satır kapsamı GPU çekirdeklerini
ölçemez — doğrulayan şey bu çapraz kontroldür.

## Kod stili

`ruff check src tests scripts` temiz olmalı; `scripts/` dahil.

> Araştırma betikleri **birinci sınıf koddur**: bu depoda kanıt üreten
> şey onlar. `scripts/` için ayrı ve gevşek bir politika yok.

Belge yoğunluğu bilinçli: modül ve fonksiyon başlıkları *ne yapıldığını*
değil **neden öyle yapıldığını** ve daha önce neyin yanlış gittiğini
anlatır.

## Kayıt defteri

Anlamlı her ölçüm `docs/defter/KAYIT-NNN_<tarih>_<konu>.md` altına
yazılır ve `docs/FAZ*-SIKINTI-RAPORU.md` açık/kapalı sıkıntıları
izler. Bir testin bunları saydığını unutmayın:
`tests/test_sikinti_raporu.py`.
