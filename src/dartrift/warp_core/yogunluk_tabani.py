"""A83 — süreklilik yoğunluğuna genleşme tabanı.

## Neden

`--dayanim-kesme` (A80) açıkken de 48 kaba noktanın 5'i patladı; hepsi
yüksek blok kesri (`f ≈ 0,45–0,48`) ve neredeyse katı bloklu (`α_b ≈
1,02–1,08`) köşede — orada yığın yoğunluğunu korumak için matris çok
gözenekli türetiliyor (`α ≈ 2,2`). `PatlamaGozlemcisi` (N2 θ #6, adım
8 425): dayanımı kesilmiş (`S = 0`), basıncı kırpılmış (`P = 0`) bir
matris parçacığı 230 m/s ile ayrılıyor ve süreklilik yoğunluğu **tam
sıfıra** iniyor. SPH hız diverjansı `1/ρ_i` ile ölçeklendiği için yapay
viskozite terimi `dt`'yi sıfıra indiriyor; zaman `12,915 ms`'de donuyor,
sonra `nan`.

## Ne yapar

Her süreklilik yarım adımından sonra `ρ_i ≥ η_taban · ρ₀ / α_i`
(`η = ρα/ρ₀`, A80 ile aynı genleşme ölçüsü). `η_taban = 0,01`: katı
eşdeğer yoğunluğun `%1`'i, yani hacmi `100` kattan fazla büyümüş —
fiilen boşlukta uçan — madde. Kütle değişmez; yalnız bu parçacığın hacim
kestirimi sınırlanır. Kaç parçacığa dokunulduğu sayılır.
"""
from __future__ import annotations

import warp as wp

F = wp.float64


@wp.kernel
def yogunluk_tabani_k(
    rho: wp.array(dtype=F),
    alpha: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    rho0: F,
    eta_taban: F,
    tabanda: wp.array(dtype=wp.uint8),
):
    i = wp.tid()
    # `tabanda` burada SIFIRLANMAZ: adimin iki yarim adiminin ikisinde de
    # isaretlenebilir; cozucu adim BASINDA sifirlar (ilk surum her yarim
    # adimda sifirliyordu ve ikinci yarim adim ilk kirpmayi siliyordu).
    if active[i] == wp.uint8(0):
        return
    alt = eta_taban * rho0 / wp.max(alpha[i], F(1.0))
    if rho[i] < alt:
        rho[i] = alt
        tabanda[i] = wp.uint8(1)
