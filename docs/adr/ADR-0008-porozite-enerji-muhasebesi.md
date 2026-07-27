# ADR-0008 — P-α sıkışma işi çift sayılmaz; enerji PdV teriminden gelir

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P2-FR-04, P2-VR-04, P2-VR-06; DR-RIFT-P2 §2.4, §5.3

## Bağlam
Şartname §5.3 sözde-kodu porozite güncellemesini şöyle yazar:

```
alpha_new = ...
u[i] += compaction_work(alpha[i], alpha_new)/rho[i]   # sikisma isi -> ic enerji
alpha[i] = alpha_new
```

Bu satır, nokta (0-B) modellerinde doğrudur: orada `u`'yu değiştiren başka bir
mekanizma yoktur. Ancak SPH'de iç enerji zaten çiftler-arası PdV işiyle
güncellenir:

    du_i/dt = −½ Σ_j m_j v_ij · ((T_i + T_j)·∇W_ij) + AV terimi

P-α modelinde basınç `P = P_katı(ρ·α, u) / α` üzerinden hesaplandığı için,
gözenek çökerken yapılan iş **bu terimin içinde zaten vardır**: α düştükçe
efektif basınç ve dolayısıyla PdV işi değişir. Sıkışma işini ayrıca `u`'ya
eklemek aynı enerjiyi **iki kez** saymak olur ve fiziksel olmayan ısınma
üretir (P2 §9'daki "Porozite enerji hatası — nonfiziksel ısınma" riski).

## Değerlendirilen seçenekler
1. **Sözde-kodu birebir uygulamak** (`u += w/ρ`): şartnameye harfiyen uyar ama
   enerji defterini bozar; izole koşuda toplam enerji artar.
2. **PdV'yi kapatıp yalnızca crush işini eklemek:** SPH'nin termodinamiğini
   kırar; şok ısınması kaybolur.
3. **Sıkışma işini PdV'ye bırakmak (seçilen):** `porosity_update` yalnızca α'yı
   günceller; normalize edilmiş iş `P·Δα/α` **tanı amaçlı** döndürülür ve
   `u`'ya eklenmez.

## Karar
`compute_porosity` yalnızca distansiyonu günceller (α ↓, α ≥ 1, geri genleşme
yok). Sıkışma enerjisi çift-terimli PdV işinden gelir. `porosity_update()`
ikinci dönüş değeri olarak normalize işi verir; bu değer **yalnızca**
nokta-model testlerinde (monotonluk, pozitiflik) ve ablasyon raporunda
kullanılır, enerji defterine girmez.

Bu, şartnamenin sözde-kodundan bilinçli bir sapmadır ve Ana Plan'ın "sessiz
değişiklik yasak" kuralı gereği bu ADR ile kayıt altındadır. Sapma
şartnamenin **amacına** (enerji doğru muhasebe edilsin) uyar, harfine değil.

## Sonuçlar
- (+) İzole koşuda enerji defteri kapanıyor (P2-VR-06).
- (+) Porozitenin fiziksel etkisi yine ölçülebilir: aynı çarpmada porozite
  açıkken şok tepe basıncı düşüyor ve şok geçen bölgede α eziliyor —
  `test_crush_curve.py::TestPorousPlateAblation` bunu sayıyla gösterir.
- (−) Nokta-model "sıkışma işi" ile SPH enerji defteri arasındaki bağ dolaylı;
  bu yüzden ikisi ayrı test edilir.

## İlgili testler
`tests/test_crush_curve.py`, `tests/test_ablation.py`,
`tests/test_cold_collapse.py`
