# ADR-0007 — Enerji güncellemesi: KDK içinde tam trapez (iki değerlendirme)

- **Durum:** Kabul edildi (kilitli)
- **Tarih:** 2026-07-27
- **İlgili gereksinim:** P1-FR-06, P1-VR-03; DR-RIFT-P1 §2.3, §5.4

## Bağlam
Şartname §5.4 sözde-kodu KDK leapfrog'u şöyle yazar:

```
v_half = v + 0.5*dt*a
x_new  = x + dt*v_half
(yeniden: density, eos, forces -> a_new)
v_new  = v_half + 0.5*dt*a_new
u_new  = u + dt*dudt        # enerji, momentum formuyla tutarli
```

`u_new = u + dt*dudt` satırındaki `dudt`'nin **hangi durumda** değerlendirildiği
belirtilmemiştir. Üç aday denendi ve izole gaz bulutunda (N=300, t=0.3) toplam
enerji hatası ölçüldü:

| Şema | `dudt` nerede | CFL 0.3 | CFL 0.15 | CFL 0.075 |
|------|---------------|---------|----------|-----------|
| A: iki yarım kick, eski önbellek | (xₙ,vₙ) ve (xₙ₊₁,v_half) | **1,19 %** | 0,58 % | 0,29 % |
| B′: tek tam adım, zaman-merkezli | (xₙ₊₁, v_half) | 0,20 % | 0,10 % | 0,05 % |
| **B: tam trapez (seçilen)** | (xₙ,vₙ) ve (xₙ₊₁,vₙ₊₁) | **0,022 %** | 0,0065 % | 0,0022 % |

Şema A, P1-VR-03'ün %0,5 eşiğini CFL=0,3'te **geçemiyordu** ve hata dt ile
yalnızca birinci mertebeden azalıyordu — yani sistematik bir tutarsızlıktı,
sayısal gürültü değil.

## Değerlendirilen seçenekler
1. **CFL'i küçültmek** (A şeması + cfl≈0,05): eşiği geçerdi ama maliyeti 6×
   artırır ve kök nedeni gizler. Reddedildi.
2. **Şema B′** (tek ek değerlendirme): eşiği geçer, ucuzdur; ama `u` ile `v`
   farklı zaman noktalarında güncellenir, enerji formu momentum formuyla tam
   simetrik olmaz.
3. **Şema B — tam trapez (seçilen).**

## Karar
`u` (ve FAZ 2'de `S`) **tam trapezle** ilerletilir: yarısı adım başındaki
D(xₙ,vₙ) oranıyla, yarısı adım sonundaki D(xₙ₊₁,vₙ₊₁) oranıyla. Bu, adım başına
**iki** çift değerlendirmesi gerektirir:

```
kick_v(dt/2); kick_u(dt/2)        # D(x_n, v_n)
drift(dt)
eval()        # (x_n+1, v_half) -> kick2 icin a
kick_v(dt/2)
eval()        # (x_n+1, v_n+1)  -> tutarli onbellek
kick_u(dt/2)                       # D(x_n+1, v_n+1)
```

İkinci değerlendirme boşa gitmez: bir sonraki adımın ilk kick'i için
(x,v)-tutarlı `a`/`dudt` önbelleğini kurar. `kick_v` ve `kick_u` bu yüzden
**ayrı kernel'lerdir** (`warp_core/integrator.py`).

## Sonuçlar
- (+) Enerji hatası %0,5 eşiğinin ~20 katı altında; dt ile ikinci mertebeden
  azalıyor (0,022 → 0,0065 → 0,0022: her yarılamada ~3×).
- (+) Momentum korunumu etkilenmez (antisimetri kuvvet formundan gelir):
  ölçülen 1,4e-17 — makine hassasiyeti.
- (−) Adım başına iki kuvvet değerlendirmesi: ~2× maliyet. FAZ 1'in ilkesi
  "önce doğruluk" olduğu için kabul edildi; performans FAZ 1 kapsamı dışı.
- CPU referansı ve Warp çözücüsü **aynı** sırayı uygular; `test_sph_cross`
  bit-yakınlığı sınar.

## İlgili testler
`tests/test_conservation.py`, `tests/test_sod.py::test_energy_conservation`,
`tests/test_sph_cross.py`
