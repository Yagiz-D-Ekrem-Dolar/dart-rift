# Protokol L sonucu — üç eksenli duyarlılık pilotu

**Tarih:** 2026-09-13 · **İşler:** L `1559064` (12 görev, 36 nokta), rapor
`1559092`, ayrıntı `1559093`, geometri `1559095` — hepsi `egitimg16u4`,
NVIDIA H200. **Ölçüt:** [`PROTOKOL-L-DUYARLILIK.md`](truba/PROTOKOL-L-DUYARLILIK.md),
koşudan önce commit'lendi.

---

## 1. Kilitli yargı

| kol | geçerli (S11) | tekil değerler | düşen gözlem | **yargı** |
|---|---|---|---|---|
| **L_ara_kirpik** | 18/18 | 0,959 · 0,440 · 0,369 | — | **HİÇBİR YÖN** |
| **L_son_uretim** | **0/18** (kuvvet anı `q/Y ≤ 1,6e4`) | 16,99 · 4,20 · 0,384 | `β`, `M_ej`, `P_ej`, `θ_ej` (sabit `β = 1`) | **İKİ YÖN** |

Türev tekrarı: ara kolunda `log10_Y0` (`0,576`) ve `f_boulder`
(`1,795`) **gürültüde**; üretim kolunda hepsi `< 0,17`.

> **Bu kombinasyon protokolün önceden yazılmış yorum tablosunda (§7)
> YOK.** Tabloda yalnız "ara kolu en az üretim kolu kadar yön verir"
> durumları vardı. Aşağıdaki açıklama **koşudan sonra** yapıldı ve
> öyle etiketleniyor.

## 2. Neden — koşudan SONRA yapılan ölçüm (betimleyici)

### 2.1 Ara kolunda gözlemler iki kümeye ayrılıyor

| rejim | krater derinliği | `β` | kazılan hacim | `dV_sıkışma` | ejekta açısı | `μ` |
|---|---:|---:|---:|---:|---:|---:|
| **KAZI** (7 nokta) | 2,2–2,4 m | **1,47–1,54** | 22–24 m³ | +13…+19 m³ | ~179° | 0,34–0,37 |
| **SIKIŞMA** (11 nokta) | 1,3–1,5 m | **1,02–1,05** | 6,5–8,5 m³ | −3…+3 m³ | ~150° | 0,47–0,52 |

Altı merkez gerçekleşmesinden 4'ü KAZI, 2'si SIKIŞMA. Aynı tohumda `α_b`
ya da `Y₀` değişince rejim **değişmiyor**; `f` değişince **değişebiliyor**
(v2 yerleştirici farklı bir blok dizilimi çiziyor).

### 2.2 Rejimi çarpma noktası altındaki blok belirliyor

| rejim | çarpma noktasına en yakın blok parçacığı | 1 m içi blok kütle payı | 2 m içi |
|---|---:|---:|---:|
| SIKIŞMA (11) | **0,00 – 0,35 m** | 0,77 – 1,00 | 0,72 – 0,93 |
| ara durum (1, `β = 1,27`) | 0,93 m | 0,04 | 0,38 |
| KAZI (6) | **2,20 – 7,47 m** | 0 | 0 |

Ayrım **kusursuz ve mesafeyle tekdüze**: mermi bir bloğa çarparsa
`β − 1 ≈ 0,03`, matrise çarparsa `≈ 0,5` (**~17×**).

### 2.3 Üretim kolunun "İKİ YÖN"ü neden yanıltıcı

Üretim sahnesinde bloklar 14–42 m ve 144 sahnenin hiçbirinde çarpma
noktasının 6 m çevresinde blok yok (uzman). Çarpma sahası **her
tohumda saf matris** → gerçekleşme gürültüsü yapay olarak küçük
(`σ_d = 7 mm`) → tekil değerler şişiyor. Ayrıca kol sayısal olarak
geçersiz (A72). En zayıf yön ağırlıkla blok eksenleri:
`(α_b, log Y₀, f) = (−0,78, 0,08, −0,62)`.

## 3. Ne öğrendik

1. Fiziksel boyutlu bloklar ve çekmesiz matrisle, **24 ms'deki momentum
   aktarımını istatistiksel iç yapı parametreleri değil, çarpma
   noktasındaki yerel blok dizilimi yönetiyor.**
2. Rastgele bir çarpma sahasıyla yapılan duyarlılık ölçümü, parametre
   etkisini bu ikili anahtarın gürültüsüne gömüyor.
3. Uzmanın önerisi doğrudan uygulanabilir: *"Çarpma noktasında bilinen
   yüzey bloklarını koşullayın; bilinmeyen iç yapıyı rastgeleleştirin."*
   DART'ın çarpma sahası DRACO görüntülerinde var.

## 4. Sınırlar

- Kaba merdiven, `t = 24 ms` anlık görüntü; enerji sapması `−%2,6`.
- Mermi `h/s ≈ 10` (A78) — iki kolda da; rejimlerin büyüklüğünü
  etkileyebilir, ayrımı açıklamaz (ayrım geometride).
- 18 nokta, iki türev tohumu, altı merkez gerçekleşmesi.

## 5. Sonraki deney (L2)

Çarpma sahası **koşullanmış** iki senaryo (matrise çarpma / bloğa
çarpma), iç yapı rastgele, mermi kendi `h`'siyle (A78); aynı kilitli
tekil değer ölçütü.
