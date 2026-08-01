# ADR-0024 — Yerçekimi ölçek kararı: settling, ağaç yenileme ve fazlara göre yerçekimi

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-01
- **Bağlam:** FAZ 3, P3-FR-05 (settling), P3-VR-01 (başlangıç KE eşiği)
- **İlgili:** ADR-0015 (süreklilik yoğunluğu), ADR-0021 (Barnes-Hut ağaç maliyeti,
  üç seçenek açık bırakılmıştı), ADR-0022/0023 (porozite başlangıç durumu)

## Karar verilmesi gereken şey

ADR-0021, Barnes-Hut ağacının CPU'da Python'da kurulduğunu ve büyük N'de baskın
kalem olduğunu ölçmüş, üç seçeneği **açık bırakmıştı**. P3-FR-05 "hedef öz-yerçekimi
altında düşük-sönümlü settling'e alınır" diyor. Settling = uzun koşu + yerçekimi,
yani seçim burada yapılmak zorundaydı.

Karar tahminle değil ölçümle verildi.

## Ölçümler

Kurulum: ikosfer R=80 m, aralık 7 m, N=8842, bazalt Tillotson + P-α (α₀=1.6) +
Lundborg dayanım, süreklilik yoğunluğu, Barnes-Hut θ=0.5, FP64, H100 değil yerel GPU.
Ölçüm betiği ve ham çıktı: `docs/evidence/ADR-0024-olcumler.txt`.

### (1) Başlangıç durumu zaten dengede

| büyüklük | değer |
|---|---|
| maks \|a_SPH\| (t=0) | **0.0 — tam olarak sıfır** |
| maks \|P\| | 0.0 Pa |
| maks \|S\| | 0.0 Pa |
| ρ aralığı | [1687.500000, 1687.500000] = ρ₀/α₀ |
| maks \|a_yerçekimi\| | 3.902194e-05 m/s² |

Süreklilik modunda ρ = ρ₀/α₀ ile başlatıldığı için (ADR-0022) P = P_katı(ρα,u)/α = 0
ve S = 0; dolayısıyla SPH kuvveti **özdeş olarak sıfırdır**. t=0'da dengesiz tek
kuvvet yerçekimidir. Serbest yüzeyde bile sıfır — çünkü sıfır basınç alanının
gradyanı sıfırdır.

### (2) Yerçekimi hangi zaman ölçeğinde iş yapar?

Serbest düşme süresi yalnızca yoğunluğa bağlıdır, boyuttan bağımsızdır:
t_ff = √(3π/(32Gρ)) = **1566 s**.

| cisim | R [m] | dt_CFL [s] | bir t_ff kaç adım |
|---|---|---|---|
| test | 80 | 8.535e-04 | 1.83e+06 |
| **Dimorphos** | 82 | 1.219e-04 | **1.28e+07** |
| Didymos | 390 | 4.877e-04 | 3.21e+06 |

Zaman adımı elastik ses hızıyla (c_uzunlamasına = 4100.6 m/s) sınırlıdır, yerçekimi
zaman ölçeğiyle değil. **Yerçekimsel oturmayı açık integrasyonla çözmek bu fazda
hesaplanabilir değildir** — DART çözünürlüğünde tek bir serbest düşme süresi 13
milyon adım eder.

### (3) Zaten oturacak bir şey var mı?

Merkez litostatik basınç P = (2π/3)Gρ²R²:

| cisim | P_lito [Pa] | P_lito / Y₀ (Y₀=1e4 Pa) |
|---|---|---|
| test | 2.899 | 2.90e-04 |
| **Dimorphos** | **3.045** | **3.05e-04** |
| Didymos | 68.89 | 6.89e-03 |

Yerçekiminin ürettiği gerilme, kohezyonun **3300 katı altındadır**. Yığın
yerçekimiyle değil **dayanımla** tutulur; oturacak bir şey yoktur.

> **Sınır durum, işaretlenerek bırakılıyor:** Şartname Ek A, Y₀ taramasını
> 0.1–1000 Pa aralığında istiyor. Y₀ ≲ 3 Pa örneklendiğinde P_lito > Y₀ olur ve
> yığın gerçekten oturur. FAZ 5 topluluğunda bu koşullar ayrıca işaretlenmeli;
> bu ADR onları kapsamıyor.

### (4) Ağaç bayatlaması: hata adım sayısına değil, **sürüklenmeye** bağlı

`maks|g| = 3.9022e-05 m/s²` ile normalize edildi. (Yerel \|g\|'ye bölmek merkeze
yakın parçacıklarda 0/0'a gider ve hatayı yapay büyütür — ilk denememde %14.8
"hata" böyle çıkmıştı, ölçüm değil normalizasyon hatasıydı.)

| K | sürüklenme [m] | sürüklenme/aralık | maks Δg/g_maks | ort Δg/g_maks |
|---|---|---|---|---|
| 1 | 4.27e-05 | 6.10e-06 | 9.2028e-03 | 2.3768e-03 |
| 10 | 4.27e-04 | 6.10e-05 | 9.2743e-03 | 2.3976e-03 |
| 100 | 4.27e-03 | 6.10e-04 | 9.4925e-03 | 2.4060e-03 |
| 1000 | 4.27e-02 | 6.10e-03 | 9.5878e-03 | 2.4161e-03 |
| — | 4.27e-01 | 6.10e-02 | 9.6019e-03 | 2.4612e-03 |
| — | 4.27e+01 | 6.10e+00 | **5.4255e+00** | 9.5368e-02 |

Okunan: K=1'de bile %0.92 var — bu **bayatlama değil**, θ=0.5 Barnes-Hut'ın kendi
tabanı. K 1000 kat artarken hata %0.92 → %0.96; sürüklenme aralığın %6'sını
aşmadığı sürece bayatlamanın katkısı taban gürültüsünün içinde kalıyor. Sürüklenme
6 aralığa çıktığında hata %542'ye fırlıyor — kullanılamaz.

**Sonuç: doğru denetim değişkeni K değil, aralığa göre sürüklenmedir.**

### (5) Maliyet

| N | yerçekimli değerlendirme | yerçekimsiz | ağaç payı |
|---|---|---|---|
| 2000 | 0.0594 s | 0.0003 s | %99.5 |
| 8842 | 0.2107 s | 0.0004 s | **%99.8** |

### (6) Settling penceresi (P3-VR-01)

E_bağ = (3/5)GM²/R = 7.464230e+06 J, eşik = 1e-3·E_bağ = 7.464230e+03 J.

| K | adım | t [s] | KE_son [J] | KE/E_bağ | eşik altı |
|---|---|---|---|---|---|
| 1 | 200 | 6.0320e-02 | 3.6211e-06 | **4.8512e-13** | evet |
| 100 | 200 | 6.0320e-02 | 3.6213e-06 | 4.8516e-13 | evet |

K=1 ile K=100 arasındaki fark 6e-05 bağıl — (4)'teki sonucun bağımsız doğrulaması.

## Karar

1. **Settling, "oturtma" değil "denge sınaması" olarak tanımlanır.** Başlangıç
   durumu ρ = ρ₀/α₀ ile kurulduğu için SPH kuvveti özdeş sıfırdır; modül bunu
   ölçer ve sapmayı raporlar. P3-VR-01 sağlanır (9 mertebe pay), fakat **settling
   KE'yi düşürdüğü için değil, KE zaten sıfır olduğu için**. Bu ayrım
   `settling.py` başlığında ve `SettleResult.diagnostics` içinde açıkça yazılıdır.

2. **Yerçekimsel oturma açıkça KAPSAM DIŞI bırakılır**, gerekçesi ölçülmüş
   hesaplanabilirlik sınırıdır (1.28e7 adım/t_ff) ve fiziksel olarak gereksizliğidir
   (P_lito/Y₀ = 3.05e-04). Bu bir eksiklik değil, gerekçeli bir sınırlamadır ve
   G3 kanıt paketinde bu haliyle raporlanır.

3. **Ağaç yenileme aralığı K korunur ama denetlenir.** Varsayılan K=1 (tam
   doğruluk, yaklaşıklık yok). K>1 seçildiğinde çözücü, global maksimum hızla
   birikmiş sürüklenme üst sınırını izler; `gravity_drift_tol` (varsayılan 0.25·h)
   aşıldığında sayacı artırır ve `budgets()` bunu
   `gravity_tree_drift_max_over_h` / `gravity_tree_drift_exceeded` olarak
   raporlar. İzleme yalnızca K>1'de açılır — K=1'de her adım v'yi CPU'ya çekmek
   boş maliyettir.

4. **Fazlara göre yerçekimi:** şok/krater fazında (~1–10 s) yerçekiminin ürettiği
   yer değiştirme parçacık aralığının 2.0e-05–2.0e-03 katıdır (DART çözünürlüğü),
   yani ihmal edilebilir. Ejekta/geç fazda kaçış hızı 8.37 cm/s mertebesindedir ve
   yerçekimi **belirleyicidir**. Bu ayrım FAZ 4'te faz başına yerçekimi ayarını
   meşrulaştırır; sayıları burada kayıtlıdır.

## Reddedilen seçenekler

- **Ağacı GPU'da kurmak (ADR-0021 seçenek 2).** Ağaç %99.8 pay alıyor, yani kazanç
  büyük. Ama şu an *gerek yok*: settling kapsam dışı, şok fazında yerçekimi
  ihmal edilebilir. FAZ 4'te ejekta fazı uzun koşarsa bu seçenek yeniden açılır.
  Şimdi yapmak, ölçülmemiş bir ihtiyaca kod yazmak olurdu.
- **Sabit K'yi büyütüp denetimsiz bırakmak.** (4) gösteriyor ki hata sürüklenmeye
  bağlı; hızlar mermi hızına (6145 m/s) çıktığında K=1'de bile adım başına
  sürüklenme 0.75 aralığa ulaşır. Denetimsiz K, sessizce %542 hatanın kapısını
  açardı.
- **Settling'i sönümlemeyle "yakınsadı" ilan edip geçmek.** KE eşiğin 9 mertebe
  altında çıkıyor; bunu settling'in başarısı diye sunmak ölçümün söylemediği bir
  şeyi iddia etmek olurdu (RULES.txt: başarısız/çalışmamış bir şey için başarı
  iddia edilmez).
