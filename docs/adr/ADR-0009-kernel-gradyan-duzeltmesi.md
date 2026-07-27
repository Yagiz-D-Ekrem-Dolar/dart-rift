# ADR-0009 — Hız gradyanı için Randles-Libersky düzeltmesi (yalnızca gerilme)

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P2-FR-01, P2-VR-01; DR-RIFT-P2 §2.1, §5.1

## Bağlam
Şartname §5.1, deviatorik gerilme evrimini `gv = velocity_gradient(i)` ile
başlatır ve objektifliği zorunlu kılar (P2-VR-01: *rijit dönme yapay gerilme
üretmemelidir*). Düz SPH gradyan tahmini

    L_i = (1/ρ_i) Σ_j m_j (v_j − v_i) ⊗ ∇W_ij

kernel toplamının **birinci mertebeden tutarsızlığı** nedeniyle lineer hız
alanlarını tam yeniden üretmez. Rijit dönme (v = ω × r) tam da lineer bir
alandır: düzgün kafeste, iç bölgede, 90° dönme sonunda ölçülen sapma
‖S − R S₀ Rᵀ‖ / ‖S₀‖ = **%9,7** çıktı (kabul eşiği %3).

Hata kaynağı Jaumann formülasyonu değil, ona giren `L`'dir.

## Değerlendirilen seçenekler
1. **Eşiği gevşetmek** (%10'a çıkarmak): şartnamenin "~0 yapay gerilme"
   ifadesini boşaltır; reddedildi (bilim bükülmez, hedef daraltılır).
2. **Çözünürlüğü artırmak:** hata yavaş azalır ve her koşuyu pahalılaştırır;
   kök nedeni çözmez.
3. **Randles-Libersky (Bonet-Lok) kernel gradyan düzeltmesi (seçilen)** —
   şartnamenin referans mimarisi Schäfer et al. (2016, A&A 590 A19) de bunu
   kullanır.

## Karar
Gerilme evrimine giren hız gradyanı düzeltilir:

    B_i = Σ_j V_j (x_j − x_i) ⊗ ∇W_ij ,   V_j = m_j/ρ_j
    L_i = [ Σ_j V_j (v_j − v_i) ⊗ ∇W_ij ] · B_i⁻¹

Lineer alan v = A·x için pay tam olarak A·B verir, dolayısıyla L = A **tam**
elde edilir. `|det B| ≤ 1e-6` olan parçacıklarda (serbest yüzey, yetersiz
komşu) düzeltmesiz forma düşülür ve bu durum `grad_correction_used`
bayrağıyla raporlanır.

**Kapsam sınırı (kritik):** Düzeltme YALNIZCA gerilme evrimine giren `L` için
uygulanır. Yapay viskozitenin `div v` ve `curl v` büyüklükleri FAZ 1'deki
ayrıklaştırmayla **birebir aynı** kalır:

    div v_i  = (1/ρ_i) Σ_j m_j (v_j − v_i)·∇W_ij
    curl v_i = (1/ρ_i) Σ_j m_j (v_j − v_i)×∇W_ij

Aksi hâlde Balsara faktörü değişir ve katı çözücü, tüm modüller kapalıyken
bile FAZ 1 hidrodinamiğine indirgenmez. Bu tuzağa geliştirme sırasında **iki
kez** düşüldü; `test_solid_cross.py::TestReductionToPhase1` her ikisini de
yakaladı ve artık kalıcı bekçidir.

## Sonuçlar
- (+) Rijit dönme sapması %9,7 → eşik altına indi; von Mises invaryantı korunuyor.
- (+) Jaumann terimleri kapatıldığında hata O(1)'e fırlıyor (ablasyon kanıtı),
  yani test gerçekten objektifliği ölçüyor.
- (+) FAZ 1 davranışı bit düzeyinde korunuyor.
- (−) Parçacık başına bir 3×3 matris tersi (GPU'da `wp.inverse`). Kabul edildi.
- (−) `trace(L_düzeltilmiş) ≠ div v_AV`. Bu bilinçlidir: deviatorik ayrıştırma
  düzeltilmiş L'nin kendi izini kullanır, AV kendi `div v`'sini.

## İlgili testler
`tests/test_rigid_rotation.py`, `tests/test_solid_cross.py`,
`tests/test_elastic_wave.py`
