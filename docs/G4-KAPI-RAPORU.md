# G4 kapı raporu

**Sonuç:** **GEÇİLEMEDİ**

- **koşulmayan ölçütler:** C1, C2, C3
- **düşen ölçütler:** A1

> Kısmi geçiş yoktur. Bir ölçüt koşulmadıysa **geçmemiş** sayılır.

## G4-A — mermi çözülüyor — GEÇMEDİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| A1 | mermi çapı / yerel aralık | `>= 2` | `0.214638` | **DUSTU** |
| A2 | `r_ince / R_mermi` | `>= 3` | `66.5573` | **GECTI** |
| A3 | kaba/ince ek yerinde kütle sapması | `< 0.005` | `0.000348021` | **GECTI** |

## G4-B — gözlenebilirler yakınsıyor — GEÇTİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| B1 | ardışık çözünürlükte `β` farkı | `< 0.1` | `0.000842672` | **GECTI** |
| B2 | `β` durulmuş (1 = evet) | `>= 1` | `1` | **GECTI** |
| B3 | A′, ince kola tek `h`'den yakın (1 = evet) | `>= 1` | `1` | **GECTI** |
| B4 | enerji sapması log-log eğim | `< 1` | `-0.00373753` | **GECTI** |

## G4-C — parametreler geri bulunuyor — GEÇMEDİ

| # | ölçüt | eşik | ölçülen | durum |
|---|---|---|---|---|
| C1 | parametre kapsaması (3/3) | `>= 1` | `—` | **KOSULMADI** |
| C2 | en dar bant / önsel | `< 0.5` | `—` | **KOSULMADI** |
| C3 | gürültüyle genişleme (1 = evet) | `>= 1` | `—` | **KOSULMADI** |

## Tanılar — **ölçüt değil**

> Bunlar ölçüldü ama G4'ün geçme koşulu **değil**. Ölçütler ölçümden önce yazıldı ve sonradan eklenmiyor (ADR-0040); bilgi ise gizlenmiyor.

| büyüklük | ölçülen | yorum |
|---|---|---|
| `β_bound` baştan sona sabit mi kaldı | `0` | `1` ise B2 **yazılmaz** — sabit seride `durulmuş` boş bir kanıttır (sıkıntı 33) |
| A′ dikişinde en yakın komşu / ince aralık | `0.652114` | 0,5'in altı gözden geçirme gerektirir (KAYIT-039 §2'de ölçülen: 0,6521) |
| FAZ 4.4 kolları aynı `t_sim`'e ulaştı mı | `1` | `0` ise B1 ve B3 **yazılmaz** — farklı `t`'deki `β`'lar yakınsama ölçmez (sıkıntı A6) |
| A′'nın parçacık tasarrufu (her yeri inceltmeye göre) | `6.87227` | yüksek olması iyi; ölçülen 6,87× (s = 7,0/3,5, r_iç = 25) |

## Koşullu kabuller

> Kapı geçse **bile** bunlar açık kalır.

1. ADR-0041 ve ADR-0042 küp geometrisinde ölçüldü, DART geometrisinde değil (KAYIT-035, KAYIT-037).
2. Boşluk 3 `λ = 2` (8:1) oranında kapandı; ADR-0026 DART için çok daha yüksek oran istiyor.
3. B1 eşiği (`%10`) bilinçli olarak gevşek; ana ürün henüz `±0,1` doğrulukta değil (G4-OLCUTLERI §3).
