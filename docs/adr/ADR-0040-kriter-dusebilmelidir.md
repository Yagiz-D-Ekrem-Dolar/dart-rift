# ADR-0040 — Bir kriter, düşebileceği bir dünya olmadan kanıt değildir

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** G1 C7 (P1-FR-07 zaman adımı kısıt logu); K15, K19, K20
- **İlgili:** ADR-0036 (yanlı örneklem), ADR-0037 (yanlış beklenti)

## Bulgu

Üç ayrı yerde, bir kriter **düşemeyecek** biçimde yazılmıştı:

| # | yer | koşul | neden düşemez |
|---|---|---|---|
| K15 | `coordination_interior_mean` | `mean(cn[cn >= median(cn)])` | örneklem, ölçülen büyüklükle seçiliyor |
| K19-B | RT11 | `"X" if "X" in doc else "Y"` | eşik, aranan metinden seçiliyor |
| K20 | G1 C7 | `\|a + b − 100\| < 1e-9` | `a = 100·k/n`, `b = 100·(n−k)/n` — özdeşlik |

Üçü de "geçti" raporluyordu ve üçü de **hiçbir şey sınamıyordu**.

## Karar

Bir kriter yazılırken **düşme senaryosu** açıkça düşünülür ve mümkünse
kod yorumunda yazılır: *"bu koşul şu durumda düşer: …"*

Uygulanan somut kural üçlüsü:

1. **Örneklem, ölçülen büyüklükten bağımsız seçilmeli** (ADR-0036).
2. **Eşik, karşılaştırılan veriden türetilmemeli** — türetiliyorsa
   *bağımsız bir taban* ölçülmeli (ADR-0039'daki yanlılık tabanı gibi).
3. **Özdeşlikler kriter olamaz.** Cebirsel olarak zorunlu bir eşitlik,
   yalnızca *yapısal* bir doğrulamadır; kanıt olarak sayılmaz.

Ayrıca her "ayrışıyor / çalışıyor / yakınsıyor" iddiası bir **pozitif kontrol**
ister: sistemin gerçekten *ayıramadığı* bir durumda kriter düşmeli
(ADR-0039'daki %10 büzüşme kontrolü gibi).

## G1 C7'ye uygulanışı

Özdeşlik yerine düşebilecek şartlar:
- gerekli alanların tamamı var, `n_steps > 0`,
- yüzdeler `[0, 100]` aralığında,
- `0 < dt_min ≤ dt_max < ∞`,
- **`dt_max > dt_min`** — sabit `dt`'de kısıt-yüzdesi logu bilgi taşımaz;
  P1-FR-07'nin amacı budur.

## Ders

> **Bir koşulun düşebileceği bir dünya var mı?** Yoksa o koşul kanıt değil,
> yalnızca bir özdeşliğin yeniden yazımıdır.
