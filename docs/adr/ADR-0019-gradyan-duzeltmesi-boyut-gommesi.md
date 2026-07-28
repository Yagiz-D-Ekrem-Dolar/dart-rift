# ADR-0019: Gradyan düzeltmesinin tekillik kontrolü `dim × dim` alt-bloğunda yapılır

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-29
- **Bağlam:** P2-FR-01, P2-VR-03; G2 kapısı C2 (elastik dalga)
- **İlgili:** [ADR-0009](ADR-0009-kernel-gradyan-duzeltmesi.md)

## Sorun

Denetim sırasında `state.grad_correction_used` alanının **kaydedildiği ama
hiçbir yerde denetlenmediği** görüldü — ne testte, ne kapıda, ne raporda.
Denetlenmeyen bir tanı, sessizce yanlış olabilir.

Ölçüldü:

| Senaryo | Düzeltme uygulanan parçacık |
|---|---|
| 3B küre (rijit dönme, N=912) | **%100** |
| 1B çubuk (elastik dalga, N=240) | **%0** |

Yani Randles-Libersky düzeltmesi (ADR-0009) **1B senaryolarında hiç
çalışmıyordu**.

## Kök neden

`_embed3` tüm çift büyüklüklerini 3B'ye gömer. `dim = 1` iken
`B = Σ_j V_j (x_j−x_i) ⊗ ∇W` matrisinin yalnızca `[0,0]` bileşeni sıfırdan
farklıdır; y ve z satırları **özdeş sıfırdır**. Dolayısıyla:

```
det(B_3x3) = 0   (her zaman, her parçacık için)
```

Kod ise tam 3×3 determinantına bakıp `|det| > 1e-6` şartını arıyordu. Şart
hiçbir zaman sağlanmıyor, düzeltme atlanıyor ve düzeltmesiz `l_raw`
kullanılıyordu.

Kritik ayrıntı: 1B'de **anlamlı olan bileşen gayet iyi koşulluydu** —
ölçülen `B[0,0]` medyanı **0,9951** (iyi örneklemede ~1 beklenir). Yani
matris tekil değildi; onu tekil gösteren şey **boyut gömmesiydi**. Tekillik
testi, olmayan bir tekilliği raporluyordu.

## Karar

Tekillik kontrolü ve ters alma yalnızca anlamlı `dim × dim` alt-bloğuna
uygulanır:

```python
d = state.dim
b_sub = b_mat[:, :d, :d]
ok = np.abs(np.linalg.det(b_sub)) > 1.0e-6
state.L[ok, :, :d] = l_raw[ok][:, :, :d] @ np.linalg.inv(b_sub[ok])
```

`dim = 3` için bu, önceki davranışa **birebir** indirgenir.

## Sonuç

Düzeltme oranı 1B'de %0 → **%100**; 3B'de %100 (değişmedi).

Elastik dalga hatası (P2-VR-03, eşik %3):

| res | önce | sonra |
|---|---|---|
| 150 | %9,2417 | %9,1252 |
| 300 | %5,4898 | %5,3644 |
| 400 | %4,3185 | %4,1880 |
| 600 | **%2,9563** | **%2,8281** |

Kapı marjı 1,01× → **1,06×**. Bu bir eşik ayarı değil: düzeltme zaten
uygulanması gereken yerde uygulanmaya başladı.

Rijit dönme (3B) hatası %1,6585 → %1,6585 — **değişmedi**, alt-blok
değişikliğinin `dim=3` için etkisiz olduğunu doğruluyor.

## GPU tarafı

`WarpSolid3D` yalnızca 3B'dir; orada `wp.determinant(b_mat)` doğru çalışır ve
değişiklik gerekmez. GPU çekirdeğinin CPU referansından farklı bir dal
seçmesi durumunda **CPU↔GPU çapraz kontrolü (1e-8) başarısız olurdu** —
dolayısıyla dal uyumu zaten korunuyor; ayrıca bir GPU tanısı eklenmedi.

## Sonuçlar

- (+) 1B katı senaryolarında hız gradyanı artık doğrusal alanları tam yeniden
  üretiyor; ADR-0009'un vaadi bu senaryolarda da geçerli.
- (+) Elastik dalga marjı genişledi.
- (−) Bu, 1B sonuçlarının önceki kanıt raporlarındakinden farklı olduğu
  anlamına gelir; G2 C2 sayısı %2,96 → %2,83.

## Ders

Tanı alanı üretmek yetmez; **denetlenmeyen tanı, olmayan tanıdır.**
`grad_correction_used` doğru hesaplanıyordu ve doğru cevabı veriyordu (%0) —
kimse bakmadığı için hata iki faz boyunca görünmedi. Testler eklendi:
`tests/test_rigid_rotation.py::TestGradientCorrectionIsActuallyApplied`
hem 1B hem 3B'de oranın 1,0 olduğunu sabitler.
