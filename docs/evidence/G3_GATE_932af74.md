# G3 kapısı — eksikler kapatıldıktan sonraki kanıt

**Kanıt commit'i:** `932af74`
**Makine:** TRUBA / kolyoz3 — NVIDIA H100 80GB HBM3
**İş:** SLURM 1445937 · **Tarih:** 2026-08-02
**Ham rapor:** `gate_runs/g3_truba_932af74_1445937/G3_report.md`

> Bu koşu, [`G3_GATE_8916f42.md`](G3_GATE_8916f42.md)'den sonra kapatılan
> eksikleri içerir: **Grady-Kipp hasar modeli** (ADR-0027), **blok
> yerleştirme düzeltmesi**, `volume`/`area` toplama determinizmi.

---

## Sonuç

| kapı | sonuç | çıkış kodu |
|---|---|---|
| **G3** | **KISMİ** — kanıtlanabilir kriterlerin **hepsi geçti**, C7 **KANITLANAMADI** | 3 |
| G0 | GEÇTİ | 0 |
| G1 | GEÇTİ | 0 |
| G2 | GEÇTİ | 0 |

Dördü de aynı işte, aynı commit'te, temiz git ağacıyla arka arkaya koşuldu.

**605 test geçti / 0 kaldı** (önceki 571'den +34), kapsam **%97,0**
(4066 ifade, 122 kapsanmayan).

Hasar modülleri: `damage_gradykipp.py` **%100**, `damage_ref.py` **%96,6**.

---

## Önceki koşuya göre değişenler

| # | değişiklik | önce | sonra |
|---|---|---|---|
| C2 | blok kesri (hedef 0,30) | 0,263 — **DOYMUŞ** | **0,303 — doyma yok** |
| C6 | sahne karması | `1c6f2a10…` | `6d6f1d10…` (altın yenilendi, eski `history`de) |
| — | test sayısı | 571 | **605** |
| — | hasar modeli | yok (`D = 0`) | **var** (ADR-0027) |

Diğer kriterlerin ölçülen sayıları değişmedi.

---

## Kriterler

| # | Kriter | Sonuç | Ölçülen |
|---|---|---|---|
| C1 | Şekil-mesh hattı | **GEÇTİ** | kenar-manifold ✓; hacim hatası %0,217; bölünmeyle %3,38 → %0,217 |
| C2 | Moloz yığını | **GEÇTİ** | N=8842; yoğunluk sapması %0,210; iç koordinasyon **12,00**; **blok kesri 0,303** (hedef 0,30, doyma yok); determinizm ✓ |
| C3 | Settling | **GEÇTİ** | KE_son/E_bağ = 4,958e-12 (eşik 1e-3); t=0'da maks \|a_SPH\| = **0,0 tam** |
| C4 | Mermi | **GEÇTİ** | 3 çözünürlük; kütle hatası 5,9e-16; momentum 4,0e-14 |
| C5 | Gözlenebilirler | **GEÇTİ** | β geri kazanımı 3,0e-16; momentum defteri 9,0e-13; duyarlılık %7,30 |
| C6 | Determinizm + regresyon | **GEÇTİ** | karma **`6d6f1d10eaff64e2…`**; farklı tohum farklı sahne ✓ |
| C7 | Veri manifestosu (PDS) | **KANITLANAMADI** | gerçek PDS ürünleri bu ortamda yok |

---

## Bu turda kapatılan eksikler

| eksik | kapanış | kayıt |
|---|---|---|
| Hasar/kırılma modeli (`D = 0`) | Grady-Kipp + Weibull; 32 test; çekme dayanımı ≈ 32 MPa (bazalt bandı) | **ADR-0027** |
| Sahne makineler arası determinizmi | Işın dejenereliği (**2,5°** normal sapması) + centroid toplama sırası | **ADR-0025** |
| `volume`/`area` latent riski | fsum'a çevrildi; karma **değişmedi**, yani bedava kapandı | ADR-0025 |
| Blok kesri hedefe ulaşmıyordu | Büyükten küçüğe yerleştirme: 0,2672 → **0,3034**, deneme 20000 → **2048** | EKSIKLER §4 |
| Uzun koşu kararlılığı | **30 000 adım**, hata birebir sabit (log-log eğim **0,000**); çarpma kayması `O(dt)` | **ADR-0028** |
| RNG kilidinin fazla geniş olması | "Ekleme" ile "değiştirme" ayrıldı | EKSIKLER §6 |

## Açık kalan iki madde

- **C7 / PDS verisi** — paket belirlendi (`urn:nasa:pds:dart_shapemodel::1.0`),
  erişim ölçüldü ve var, indirme betiği hazır. Eksik olan tek şey **indirme
  onayı**. Bkz. `data_manifest/GEREKEN_URUNLER.md`.
- **Mermi çözünürlüğü** — DART mermisini çözmek **1,72e9 parçacık** ister,
  fizibil sınırın 153 katı. FAZ 4 yerel incelme gerektirir; sayılar ve karar
  **ADR-0026**'da. "Gereken simüle süre" sorusu buna bağlı olduğu için
  birlikte taşınıyor.
