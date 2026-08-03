# ADR-0033 — "Yığın yoğunluğu" iki farklı şeydir; ikisi de isimlendirildi

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-03
- **Bağlam:** FAZ 3 moloz yığını, G3 C2
- **İlgili:** ADR-0030 (kütle gözeneklilikten türer), ADR-0031, ADR-0032

## Sorun

`RubblePile` iki farklı büyüklüğü aynı adla taşıyordu:

| tanım | formül | ne sorusuna yanıt |
|---|---|---|
| A | `sum(m) / V_mesh` | *kalıbın* hacmine göre yoğunluk |
| B | `sum(m) / (N·V_p)` | *ayrıklaştırılmış cismin* gerçek yoğunluğu |

İkisinin oranı **tam olarak dolum oranıdır** — FCC kafesi düzensiz bir sınıra
tam oturmaz. Ölçüldü:

| şekil | N | dolum | A (mesh) | B (dolu) | A sapma |
|---|---|---|---|---|---|
| ikosfer r=100 s=9 | 8103 | 0,9993 | 1798,80 | 1800,00 | −%0,07 |
| ikosfer r=60 s=8 | 2448 | 0,9881 | 1778,51 | 1800,00 | **−%1,19** |
| elipsoit 120×100×85 | 17555 | 0,9987 | 1797,65 | 1800,00 | −%0,13 |
| ikosfer r=82 s=7 | 9544 | 1,0044 | 1807,98 | 1800,00 | **+%0,44** |

Bu bir **kusur değil** — iki ayrı sorunun iki ayrı yanıtı. Kusur olan, hangisinin
kullanıldığının **belirsiz** olmasıydı: `test_bulk_density_recovered` `rel=0.05`
bandıyla ayrımı yutuyordu.

## Sessiz tutarsızlık

Daha somut bir sonuç: `settle_pile` bağlanma enerjisini

```python
m_tot  = sum(m)                                    # AYRIKLASTIRILMIS kütle
r_eff  = (3 V_mesh / 4π)^(1/3)                     # KALIP yarıçapı
e_bind = binding_energy(m_tot, r_eff)
```

diye hesaplıyordu — **kütle bir hacim tanımından, yarıçap diğerinden**.
Fark yarıçapta `dolum^(1/3)` (ölçülen −%0,4 … +%0,15), enerjide onun tersi.
Küçük, ama isimsiz.

## Karar

1. `RubblePile.bulk_density` **kalıp** tanımıdır (A) ve belgesinde ikisinin
   farkı ölçülmüş sayılarla yazılıdır.
2. `diagnostics["bulk_density_achieved"]` **ayrıklaştırılmış** tanımdır (B) ve
   ADR-0030 hedefi **tam** tutturur.
3. `diagnostics["bulk_density_over_mesh"]` A'yı ayrıca raporlar.
4. Yeni: `RubblePile.discretised_volume` = `N·V_p` ve
   `RubblePile.discretised_radius` — **ayrıklaştırılmış cismin** hacmi ve
   yarıçapı.
5. `settle_pile` artık `pile.discretised_radius` kullanır: **kütle ile yarıçap
   aynı hacim tanımından gelir.**

Kavramsal duruş: **ayrıklaştırılmış cismin hacmi N·V_p'dir, V_mesh değil.**
Mesh yalnızca bir kalıptır; parçacıkların kapladığı hacim gerçek cisimdir.

## Yapısal önlem

`TestBulkDensityDefinitions`:
- B hedefi **tam** tutturur (`rel=1e-12`),
- `A = B × dolum_oranı` **kapalı-form** ilişkisi toleranssız kilitlenir,
- `discretised_radius` mesh yarıçapından **farklı** olmalı — aksi halde bu
  ayrım boş bir doğru olurdu.

## Ders

Bu, K7/K10/K11 deseninin daha yumuşak bir biçimi: **aynı ad iki büyüklüğü
taşıyordu.** Öncekilerde iki yer *ayrışabiliyordu*; burada iki yer *zaten
farklıydı* ve fark bir test toleransının içinde saklanıyordu.

Kural genişletildi: **bir ad iki farklı hesabı taşıyorsa, ikisi de ayrı ayrı
adlandırılmalı ve aralarındaki ilişki kapalı formda kilitlenmeli** — "yaklaşık
eşit" bir tolerans bandı, ayrımı gizlemenin en kolay yoludur.
