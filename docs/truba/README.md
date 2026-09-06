# TRUBA koşu artefaktları

Bu dizin, TRUBA'da **gerçekten koşan** ölçüt belgelerinin ve slurm
betiklerinin kopyalarıdır. Dosyalar `/arf/scratch/egitimg16u1/
driftclaude/` altındaki kopyalarla **md5 eşleşir**; yani burada
okunan şey orada koşan şeydir.

## Protokoller — mekanizma ve çıkarım kampanyaları (2026-09)

Bu altı belge projenin bilimsel sonuçlarını üreten kampanyaların
**yargı kurallarıdır** ve hepsi **koşudan önce** commit'lendi.

| protokol | iş | soru | sonuç |
|---|---|---|---|
| `PROTOKOL-E1-ERKEN.md` | `1548148` | Şok gerçekten oluşuyor mu | zirve `t = 8,61e-05 s` — **ilk canlı gözlem** |
| `PROTOKOL-E2-CEKME.md` | `1548148` | Kazıyı **ne** durduruyor | **matris çekmesi**; `Δβ` `7,7×`, `v_r` işaret değiştiriyor |
| `PROTOKOL-F-AV.md` | `1548149` | AV etkisi çözünürlükte yaşıyor mu | **SONUÇSUZ** — monotonluk ölçülemedi |
| `PROTOKOL-G-AYIRT.md` | `1548352` | Gözlenebilir `θ`'yı ayırt ediyor mu | **AYIRT EDİYOR** — `F = 1006`, `Y₀` ile `ρ = −0,94` |
| `PROTOKOL-H-KRATER.md` | `1548525` | Krater derinliği çözünürlüğe dayanıklı mı | **KORUNMUYOR** — `%72` kayma |
| `PROTOKOL-I-GECIS.md` | `1548550` | Geçiş noktası `x₀` dayanıklı mı | **koşuyor** |

Sonuç belgeleri: [`SONUC-E-F-MEKANIZMA.md`](../SONUC-E-F-MEKANIZMA.md),
[`SONUC-G-H-AYIRT.md`](../SONUC-G-H-AYIRT.md),
[`SONUC-R-YAKINSAMA.md`](../SONUC-R-YAKINSAMA.md).
Toplu bakış: [`BULGULAR.md`](../BULGULAR.md).

> Her protokolün yargı tablosu, sonucu **görmeden** yazıldı ve
> betikleriyle birlikte sınavlandı (`test_av_raporu.py`,
> `test_ayirt_raporu.py`, `test_gecis_raporu.py`). Ölçüt üç kez
> beni **durdurdu**: `β` için `OKUNMAZ`, F için `SONUÇSUZ`,
> E1 için *"çözücü kusuru"*.

## Eski ölçüt belgeleri

| dosya | ne |
|---|---|
| `OLCUT-gercek-moloz-yigini.md` | iş `1515196`'nın ölçütü — koşudan **önce** yazıldı |
| `is_A17.slurm` | iş `1515196` — ortam sınavı + zayıf hedef kolu |
| `OLCUT-krater-cozunurlugu.md` | iş `1515233`'ün ölçütü — koşudan **önce** yazıldı |
| `is_C_krater.slurm` | iş `1515233` — `λ₂ = 4` krater inceltmesi |

## Neden burada duruyorlar

Ölçüt belgeleri TRUBA'da kalsaydı, çalışma alanı bir daha
erişilemez olduğunda (bu **bir kez oldu**: `egitimg16u4`) koşuların
neye göre yargılandığı kaybolurdu. Kanıt deposunda ölçüt, sonucun
kendisi kadar korunur.

## Çalışma alanı

Ortam kurulumu ve kuyruk kuralları için `DEVAM.md` §1b.
