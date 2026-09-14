# Bitiş 3 — durum (2026-09-14 akşam)

Bu belge elle yazıldı ve **keşif** sonuçlarını içeriyor. Kilitli karar
`scripts/bitis3_raporu.py` ile TRUBA'daki JSON'lardan otomatik üretilecek
(`kampanya/BITIS3-TASLAK.md`, iş `1561432`).

## 1. Kilitli olarak kanıtlananlar

| | sonuç | kaynak |
|---|---|---|
| Sayısal tutarlılık | `ara` akma kipi Δt bağımlılığını kaldırıyor (J1); A80 kesmesi ve A83 tabanı patlamaları gideriyor (K83: V2 NÖTR) | SONUC-M-N-P-J-T §1, §2c |
| Ayırt edilebilirlik | kesmeli 48 θ havuzu: `Y₀` ve `f` görünür (N) | §2d |
| Kalibre çıkarım (kaba, 24 ms, sentetik gözlem) | zaman örnekli vektörle posterior dış doğrulamada **`Y₀` ve `f`'yi çözüyor**, `α_b`'yi çözmüyor | §2d |
| Kalibre çıkarım (orta, 24 ms) | P-v4 GP ve P-v4b kuadratik: **İKİ EKSEN** (`Y₀`, `f`) | Pv4o |
| Çözünürlük | mutlak gözlenebilirler **yakınsamıyor** (M); `Y₀` kontrastı dayanıklı, `α_b`/`f` değil (M2) | §1, §2c |
| Zaman | `β` 0,1–0,2 s'de platoya ulaşıyor (T orta, Tkt kaba) | S_T, S_Tot |

## 2. Gerçek DART gözlemi — keşif (Protokol D kuralları, 24 ms)

Gözlenen `β` depodaki arayüzden sahnenin kendi hedef kütlesiyle:
**`3,12 ± 0,34`**.

| havuz | model `β` aralığı (önsel boyunca) | kapsama |
|---|---|---|
| kaba-72 | `1,25 – 1,85` | **ÖNSEL DIŞI (YUKARI), +5,2σ** |
| orta-72 | `1,27 – 1,72` | **ÖNSEL DIŞI (YUKARI), +6,2σ** |

![β erişilebilirlik](sekil/beta_erisim_kesif_24ms.png)

Plato anında `β − 1` 24 ms'dekinin `~1,26` katı (T orta: `0,65 → 0,82`).
O çarpanla en büyük model değeri `β − 1 ≈ 0,85 × 1,26 ≈ 1,07`, yani
`β ≈ 2,1` — gözlem bandının `2σ` alt ucunun (`2,44 = 3,12 − 2·0,34`) altında.
(İlk yazımda çarpanı `β`'ya uygulayıp `~2,3` yazmıştım; düzeltildi.)

**Okuma:** mevcut ileri model (yerçekimsiz, `Y₀ ≥ 1e3 Pa`, `μ_f = 0,6`,
yığın `1800 kg/m³`), önsel boyunca DART'ın momentum aktarımını
üretmiyor. Bu, iç yapı posteriorunun gerçek gözlemle **henüz**
kurulamayacağı anlamına geliyor — sentetik çıkarım zinciri çalışıyor,
model–gözlem köprüsü eksik.

## 3. Koşan / bekleyen kilitli deneyler

| | soru | iş |
|---|---|---|
| Q1 `Mt` | plato anında üç çözünürlükte yakınsama | `1561193` |
| Q2/Q3 | plato anında kaba/orta posterior | `1561195` / `1561197` |
| Q4 | ince-72 havuzu | `1561191` |
| Q5 | blok sahasında plato posterioru | `1561239` |
| Q6 | plato anında kontrast dayanıklılığı | `1561241` |
| **U** | hangi model bileşeni `β`'yı gözleme taşıyor (Y₀ < 1e3, μ_f, gözenek, yoğunluk) | `1561438` |
| **D** | plato anında kilitli gözlem kapsaması + posterior | `1561432` |
| **HT** | kilitli Hera krater ön kaydı | `1561443` |

## 4. Bitiş 3'e kalan

1. D kilitli yargısı (plato anı). Önsel içindeyse → gerçek gözlemle
   posterior. Dışındaysa →
2. U hangi bileşeni gösterirse onunla **ADR + önsel/model genişletme**,
   N/P havuzlarının genişletilmiş önselde yeniden koşulması.
3. Q1'e göre üretim çözünürlüğü; çözünürlük terimi (Mt) posteriora eklenir.
4. HT ön kaydının depoya commit'lenmesi.
