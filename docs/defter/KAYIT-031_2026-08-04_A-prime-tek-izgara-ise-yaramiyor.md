# KAYIT-031 — A′-1: tek ızgarayla A′ **işe yaramıyor** (2026-08-04)

**Kapsam:** FAZ 4.2 son kefe · **Durum:** ölçüldü — **A′ çok seviyeli komşu
arama gerektiriyor**
**Öncül:** [KAYIT-030](KAYIT-030_2026-08-04_D2-tek-parametreli-kalibrasyon-yetmiyor.md),
ADR-0041 §5

---

## 0. Kalan tek kefe

KAYIT-030'dan sonra **A′ öne geçmişti**: D'nin kalibrasyonu tek parametreyle
yapılamıyor, C momentumu sistematik kaybediyor, A çözemiyor. Ama A′'nın
**mimari bedeli hiç ölçülmemişti** — kararın diğer kefesi boştu.

Bu kayıt o kefeyi dolduruyor. **Ve terazi devrildi.**

---

## 1. Düğüm: hash-grid **tek** destek yarıçapı alıyor

Kod okundu:

```
warp_core/hash_grid.py:42    def build(self, x64, support: float) -> float:
warp_core/hash_grid.py:47        self.grid.build(points=self.x32, radius=radius32)
warp_core/density.py:26      q = wp.hash_grid_query(grid, x32[i], radius32)
warp_core/forces.py:54       q = wp.hash_grid_query(grid, x32[i], radius32)
```

Izgara **tek bir** destek yarıçapıyla kurulur; sorgular da tek bir
`radius32` kullanır.

Parçacık başına `h` ile ızgara **en büyük** desteğe (`2·h_maks`) göre
kurulmak **zorundadır** — yoksa kaba parçacıklar komşularını kaçırır. Her
parçacık sonra kendi `2·h_i`'sine göre **eler**.

> **İnce parçacıklar gereğinden çok aday tarar.** Bu bir tahmin değil,
> ölçülebilir bir geometri sorusudur.

### `h`'nin skaler geçtiği yerler (sayıldı)

| dosya | site |
|---|---|
| `warp_core/solver.py` | 11 |
| `warp_core/solver_solid.py` | 11 |
| `warp_core/kernel_fn.py` | 9 |
| `warp_core/forces.py` | 5 |
| `warp_core/density.py` | 4 |
| `warp_core/solid_stress.py` | 2 |
| `warp_core/timestep.py` | 2 |
| `cpu_reference/sph_ref.py` | 12 |
| `cpu_reference/solid_ref.py` | 12 |
| **toplam** | **68** |

Bunlar **mekanik** değişikliklerdir. Asıl sorun aşağıdaki.

---

## 2. Ölçüm — israf

Bir ince parçacık `2·h_maks` içinde kaç aday görüyor, kaçı kendi `2·h_i`'si
içinde kalıyor? (Kenar etkisi dışlandı — D1 kuralı.)

| λ | `h` oranı | **israf (ince)** | beklenen `(h_maks/h_i)³` | israf (kaba) | genel |
|---|---|---|---|---|---|
| **1,00** | 1,000 | **1,000** | 1,00 | 1,000 | 1,000 |
| 1,26 | 1,260 | 2,065 | 2,00 | 1,000 | 1,315 |
| 1,59 | 1,590 | 3,973 | 4,02 | 1,000 | 2,301 |
| 2,00 | 2,000 | **7,581** | 8,00 | 1,000 | **5,132** |

**Boşluk kontrolü tam geçti:** `λ = 1`'de israf **1,000** — tek `h` varken
hiçbir israf yok. Ölçüm doğru kurulmuş.

Ölçülen israf **küp yasasını** izliyor (7,58 vs 8,00). Kaba parçacıklarda
israf yok (1,000) — beklenen, çünkü küresel destek zaten onlarınki.

---

## 3. Asıl soru: tasarruf israfı **karşılıyor mu**?

A′ her yeri inceltmemek için seçilir. **Kazancı parçacık sayısıdır; bedeli
tek ızgarada arama israfıdır.**

```
is(A')          = N(A')        × ortalama_israf
is(tümü_ince)   = N(tümü_ince) × 1,0
```

| λ | kütle oranı | `N(A′)` | `N(tümü ince)` | **tasarruf** | **israf** | **NET** |
|---|---|---|---|---|---|---|
| 1,26 | 2:1 | 4 189 | 7 939 | 1,90× | 1,32× | **0,694** |
| 1,59 | 4:1 | 4 503 | 15 952 | 3,54× | 2,30× | **0,650** |
| 2,00 | 8:1 | 5 301 | 31 748 | 5,99× | 5,13× | **0,857** |
| **2,52** | **16:1** | 6 719 | 63 508 | 9,45× | **10,06×** | **1,065** |

### Okuma

> **Tasarruf doğrusal, israf küpsel büyüyor.** İkisi 8:1 ile 16:1 arasında
> kesişiyor.

- 2:1 ve 4:1'de A′ ~%30–35 kazandırıyor — **mütevazı**.
- 8:1'de kazanç yalnızca **%14**.
- **16:1'de A′ her yeri inceltmekten `%6,5` DAHA PAHALI.**

Ve ADR-0026 DART için **153×** çözünürlük istiyor — 16:1'in çok ötesi.

> **Tek ızgarayla A′, DART'ın ihtiyaç duyduğu oranlarda hiçbir şey
> kazandırmıyor; tersine kaybettiriyor.**

---

## 4. Sonuç: A′ **çok seviyeli komşu arama** gerektiriyor

A′'nın mimari bedeli, sanılandan büyük:

| bileşen | durum |
|---|---|
| parçacık başına `h` (68 site) | mekanik |
| `Ω` (grad-h) düzeltmesi | bilinen formül, ek çekirdek |
| parçacık başına CFL | mekanik |
| **çok seviyeli komşu arama** | **yeni mimari** — bu ölçümle **zorunlu** hâle geldi |
| CPU referansının aynısı | çapraz kontrol için zorunlu |

Sonuncusu bir "iyileştirme" değil, **ön koşuldur**: onsuz A′ maliyeti
düşürmüyor, artırıyor.

---

## 5. Karar tablosunun son hâli — **her seçeneğin ölçülmüş bir bedeli var**

| # | mermiyi çözer | ölçülmüş bedel |
|---|---|---|
| ~~A~~ | **hayır** | — (elendi: çözünürlük artmıyor) |
| **A′** | evet | arayüz 3,2–6,5× gürültü + **çok seviyeli ızgara zorunlu** (tek ızgarada 16:1'de net **kayıp**) |
| ~~B~~ | A′ ile | = A′ |
| **C** | evet | momentum **7,5e-03 sistematik** (A/A′ `1e-16`) + MLS + korunum düzeltmesi |
| **D** | **atlar** | model-form **%5–7**, tek parametreyle **kalibre edilemiyor** (`KE/E` %14,5–18,0 ayrışıyor) |

**Hiçbir seçenek ucuz değil.** Bu, kararın *tercih* değil *takas* olduğunu
gösteriyor — ve her takasın fiyatı artık **ölçülmüş**.

### Bu, ADR-0041'i nasıl etkiliyor

Öneri **kilitlenmemişti** ve doğru olan buydu. Şimdi:

- **A′** hâlâ en az **model-form hatası** olan seçenek (mermiyi gerçekten
  çözer) — ama bedeli **çok seviyeli ızgara**yı da içeriyor.
- **D** en ucuzu ama gözlenebilirlerinden birini **%18'e kadar** yanlış
  bırakıyor.
- **C** momentumu bozuyor ve düzeltmesi ölçülmedi.

> Karar artık *"hangisi doğru"* değil, *"hangi hatayı kabul ediyoruz ve
> neyi ödemeye razıyız"* sorusudur. Bu **proje sahibinin** kararıdır ve
> ADR-0041 bu yüzden **ÖNERİLDİ** durumunda kalmalıdır.

---

## 6. Sırada

| # | iş | neden |
|---|---|---|
| A′-2 | çok seviyeli ızgara **prototipi** ve israfın `1,0`'a düşüp düşmediği | A′'nın bedelini kesinleştirir |
| D-3 | **iki parametreli** kaynak terimi (yarıçap + kinetik/termal bölüşüm) | tek parametre yetmedi |
| — | ADR-0041 §5 boşluk 3 (mukavemetli malzeme) | hâlâ açık |

---

## 7. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| mimari bedel **tahmin edilmez, sayılır** | §1 — 68 site |
| bir maliyet iddiası **ölçülür** | §2 — israf, küp yasasıyla uyumlu |
| kazanç ve bedel **birlikte** değerlendirilir | §3 — net oran |
| boşluk kontrolü: `λ=1`'de israf **tam 1,0** | §2 |
| kenar etkisi dışlanır (D1) | §2 |
| karar *tercih* değil *takas*sa, öyle yazılır | §5 |
