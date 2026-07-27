# ADR-0012 — Plastik iş `u`'ya eklenmez; Taylor testinde simetri düzlemi

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-28
- **İlgili gereksinim:** P2-FR-02, P2-VR-02, P2-VR-06; DR-RIFT-P2 §5.2

## Bağlam
Şartname §5.2 sözde-kodu return mapping'i şöyle bitirir:

```
S_new[i] = f*S_new[i]                  # akma yuzeyine cek
u[i] += plastic_work(dS)/rho[i]        # plastik is -> ic enerji
```

Bu, iç enerjinin **yalnızca** hidrostatik PdV işiyle güncellendiği bir
formülasyonda doğrudur. Bizim SPH ayrıklaştırmamızda ise iç enerji **tam
gerilme tensörünün** işiyle ilerletilir (DR-RIFT-P2 §4.1'in `T = -P·I + S`
formu):

    du_i/dt = −½ Σ_j m_j v_ij · ((T_i + T_j)·∇W_ij) + AV terimi

Deviatorik işin tamamı bu terimin içindedir. Plastik işi ayrıca `u`'ya eklemek
aynı enerjiyi ikinci kez saymaktır.

## Ölçüm
Taylor bar (bakır, v = 200 m/s, Y₀ = 400 MPa, N = 2×1295):

| Büyüklük | Ölçülen | Fiziksel sınır |
|----------|---------|----------------|
| Başlangıç kinetik enerji | 352 J | — |
| Biriken "plastik iş" | **1001 J** | ≤ 352 J |
| Toplam enerji hatası | **%288** | < %1,5 |

Plastik iş, sistemin sahip olduğu tüm kinetik enerjinin üç katı çıkıyordu —
tek başına yeterli bir imkânsızlık kanıtı.

## Karar
1. **`return_mapping` `u`'yu değiştirmez.** S'yi akma yüzeyine projekte eder
   ve plastik iş yoğunluğunu **yalnızca tanı olarak** döndürür. Depolanmış
   elastik deviatorik enerjinin ısıya dönüşmesi, `u` sabit kalırken gerçekleşen
   bir **iç dağılım** değişikliğidir; `u` toplam gerilme işini zaten taşır.
2. Plastik iş `plastic_cum` olarak enerji panosunda **ayrı satır** hâlinde
   raporlanır (toplam enerjiye eklenmeden) — modülün çalıştığının göstergesi
   olarak değerini korur.
3. **Taylor testi simetrik çarpma kurulumuna geçirildi.** Rijit duvar donmuş
   parçacık katmanıyla modellendiğinde çubuk parçacıkları duvara gömülüyor,
   aşırı basınç üretiyordu. z = 0 simetri düzlemi aynı sınır koşulunu
   (v_z = 0, kayma serbest) yapay parçacık olmadan sağlar ve tüm parçacıklar
   aktif kaldığı için enerji korunumu gerçekten ölçülebilir.

Bu, şartname sözde-kodundan **bilinçli ve gerekçeli** bir sapmadır; ADR-0008
(P-α sıkışma işi) ile aynı hata sınıfına aittir: *bir enerji katkısını, onu
zaten içeren bir terimin yanına ikinci kez eklemek.*

## Sonuçlar
- (+) Enerji defteri kapanıyor; P2-VR-06 anlamlı hâle geliyor.
- (+) Plastik iş göstergesi korunuyor (ablasyonda "dayanım açık → plastik iş
  pozitif" kontrolü hâlâ çalışıyor).
- (−) Plastik ısınmanın `u` üzerinden EOS'a geri beslenmesi bu fazda yoktur;
  barotropik test EOS'unda P zaten `u`'ya bağlı değildir. Tillotson ile
  çalışan üretim koşularında bu bağ `dudt` üzerinden kurulur.

## Ders (yöntemsel)
Aynı hata sınıfı iki ayrı modülde (porozite, dayanım) ortaya çıktı. Ortak
kalıp: **şartname sözde-kodu bir katkıyı açıkça eklerken, bizim
ayrıklaştırmamız onu zaten içeriyordu.** Sözde-kodu birebir kopyalamak yerine
"bu terim benim formülasyonumda zaten var mı?" diye sormak gerekiyor. Enerji
defterini her modül için ayrı ayrı denetleyen bir test (bütçe kapanışı) bu
sınıfı yakalayan en ucuz araçtır.

## İlgili testler
`tests/test_taylor_bar.py::test_energy_ledger_closes`,
`tests/test_ablation.py`, `tests/test_cold_collapse.py`
