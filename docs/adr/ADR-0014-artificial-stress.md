# ADR-0014 — Çekme kararsızlığı için Monaghan yapay gerilmesi

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-28
- **İlgili gereksinim:** P2-VR-02, P2-VR-06; DR-RIFT-P1 §9, DR-RIFT-P2 §9

## Bağlam
Her iki faz şartnamesi de "tensile instability"yi adıyla risk olarak listeler
ve azaltımını şöyle verir: **Wendland kernel + (FAZ 2'de) artificial stress**.
Wendland C2 uygulandı, artificial stress ertelendi. Serbest yüzeyli Taylor
çarpma testi bu ertelemenin bedelini gösterdi.

## Ölçüm
Ayırt edici test (aynı kurulum, yalnızca malzeme modeli değişiyor):

| Vaka | Enerji hatası | Son iç enerji |
|------|---------------|---------------|
| Akma yok (Y₀ = 10¹²) | %4,08 | 139 J |
| **Dayanım tamamen kapalı** | **%10,36** | 61 J |
| EPP (Y₀ = 4·10⁸) | %7,66 | 340 J |
| Düşük hız (v = 20 m/s) | **%413** | **−282 J** |

İki gözlem birlikte kaynağı belirledi: hata dayanım **kapalıyken daha büyük**
(yani return mapping veya Jaumann kaynaklı değil) ve düşük hızda iç enerji
**negatife** düşüyor — fiziksel olarak imkânsız. Lineer EOS'ta serbest yüzeyde
kernel eksikliği ρ < ρ₀ verir, bu da P < 0 (çekme) üretir; çekme altında SPH
parçacıkları kümelenir ve enerji defteri patlar.

Komşu sayısını 74 → 268'e çıkarmak (ADR-0013) durumu **kötüleştirdi**
(%7,66 → %15,7): daha geniş destek, serbest yüzeyde daha fazla kernel
eksikliği demektir. Bu, iki düzeltmenin birbirine bağlı olduğunu gösterdi —
yüksek komşu sayısı Sedov için zorunlu, ama serbest yüzeyli senaryolarda
yapay gerilme olmadan kullanılamaz.

## Karar
Monaghan (2000) yapay gerilmesi eklendi:

    R_i  = −ε · P_i / ρ_i²          (yalnızca P_i < 0; aksi hâlde 0)
    f_ij = W(r_ij) / W(Δp),         Δp = ortalama parçacık aralığı
    a_i += −Σ_j m_j (R_i + R_j) · f_ij^n · ∇W_ij

Varsayılan ε = 0,3 ve n = 4. Modül **config'ten açılıp kapanır**
(`physics.artificial_stress`), varsayılanı kapalıdır; yalnızca serbest yüzeyli
senaryolarda (Taylor) varsayılan olarak açılır. Ablasyon P2-FR-06 uyarınca
mümkündür.

**Enerji tutarlılığı:** Yapay gerilme sanal bir kuvvettir, ama yaptığı iş
`du/dt`'ye **aynı çift terimiyle** girer. Aksi hâlde momentum korunur ama
enerji korunmaz — bu, ADR-0007'de yapay viskozite için kurulan aynı
sözleşmedir: *bir kuvvet terimi eklendiğinde işi de aynı anda eklenir.*

## Sonuçlar
- (+) Çekme bölgesinde parçacık kümelenmesi bastırılır; negatif iç enerji
  ortadan kalkar.
- (+) Yüksek komşu sayısı (ADR-0013) artık serbest yüzeyli senaryolarda da
  kullanılabilir.
- (−) Yapay gerilme fiziksel değil **sayısal** bir düzeltmedir; ε ve n
  ayarlanabilir parametrelerdir ve her koşuda raporlanır (yapay viskozite
  α/β ile aynı dürüstlük kuralı).
- (−) Çekme dayanımının gerçek fiziği (hasar/kırılma) bu fazda yoktur;
  D = 0 sabittir (DR-RIFT-P2 §1.3, STRETCH).

## İlgili testler
`tests/test_taylor_bar.py` (artificial stress ablasyonu dahil),
`scripts/run_g2_gate.py` (C2)
