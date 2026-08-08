# G4 kapı raporu

**Sonuç:** **GEÇİLEMEDİ**

- **koşulmayan ölçütler:** A1, A2, A3, B1, B2, B3, B4, C1, C2, C3

> Kısmi geçiş yoktur. Bir ölçüt koşulmadıysa **geçmemiş** sayılır.

## G4-A — mermi çözülüyor — GEÇMEDİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| A1 | mermi çapı / yerel aralık | `>= 2` | `—` | **KOSULMADI** |
| A2 | `r_ince / R_mermi` | `>= 3` | `—` | **KOSULMADI** |
| A3 | kaba/ince ek yerinde kütle sapması | `< 0.005` | `—` | **KOSULMADI** |

## G4-B — gözlenebilirler yakınsıyor — GEÇMEDİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| B1 | ardışık çözünürlükte `β` farkı | `< 0.1` | `—` | **KOSULMADI** |
| B2 | `β` durulmuş (1 = evet) | `>= 1` | `—` | **KOSULMADI** |
| B3 | A′, ince kola tek `h`'den yakın (1 = evet) | `>= 1` | `—` | **KOSULMADI** |
| B4 | enerji sapması log-log eğim | `< 1` | `—` | **KOSULMADI** |

## G4-C — parametreler geri bulunuyor — GEÇMEDİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| C1 | parametre kapsaması (3/3) *(kuru kip — sayılmaz)* | `>= 1` | `—` | **KOSULMADI** |
| C2 | en dar bant / önsel *(kuru kip — sayılmaz)* | `< 0.5` | `—` | **KOSULMADI** |
| C3 | gürültüyle genişleme (1 = evet) *(kuru kip — sayılmaz)* | `>= 1` | `—` | **KOSULMADI** |

## Koşullu kabuller

> Kapı geçse **bile** bunlar açık kalır.

1. ADR-0041 ve ADR-0042 küp geometrisinde ölçüldü, DART geometrisinde değil (KAYIT-035, KAYIT-037).
2. Boşluk 3 `λ = 2` (8:1) oranında kapandı; ADR-0026 DART için çok daha yüksek oran istiyor.
3. B1 eşiği (`%10`) bilinçli olarak gevşek; ana ürün henüz `±0,1` doğrulukta değil (G4-OLCUTLERI §3).
