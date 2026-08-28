"""KDK (Kick-Drift-Kick) leapfrog kernel'leri (P1-FR-06).

Enerji, momentum formuyla tutarli guncellenir: her kick yarim adimda hem v
hem u ayni degerlendirmenin (a, du/dt) sonuclariyla ilerletilir. Donmus
(active=0) sinir parcaciklari integre edilmez ama komsu olarak katilir.
"""

from __future__ import annotations

import warp as wp

F = wp.float64
V3 = wp.vec3d


@wp.kernel
def kick_v_3d(
    v: wp.array(dtype=V3),
    a: wp.array(dtype=V3),
    active: wp.array(dtype=wp.uint8),
    half_dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        v[i] = v[i] + half_dt * a[i]


@wp.kernel
def kick_u_3d(
    u: wp.array(dtype=F),
    dudt: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    half_dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        u[i] = u[i] + half_dt * dudt[i]


@wp.kernel
def kick_u_3d_tabanli(
    u: wp.array(dtype=F),
    dudt: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    kirpilan: wp.array(dtype=F),
    half_dt: F,
):
    """`kick_u_3d` + **iç enerji tabanı** ve kırpılanın DEFTERI.

    ## Neden (rapor A21)

    `tillotson_p` basıncı hesaplarken `u = max(u_in, 0)` diyor, yani
    negatif `u`'yu **sıfır sayıyor**; ama durum değişkeni hiçbir yerde
    kırpılmıyordu. Ölçüldü (`t = 0,2 s`): hedef parçacıklarının
    **`%44,5`'inde `u < 0`**, tek aşamalı kolda tutulan enerji gelenin
    **`%2,76`**'sı.

    Sonuç: defter (`Σ m u`) ile dinamiğin gördüğü enerji **ayrışıyor**,
    ve negatife düşmüş bir parçacık sonradan ısıtılınca önce
    "borcunu" kapatıyor — şok cephesinin arkası olması gerekenden
    uzun soğuk kalıyor.

    ## Kırpılan enerji **atılmıyor, sayılıyor**

    Sessizce kırpmak bir kaçak kaynağını başkasıyla değiştirmek olurdu.
    `kirpilan[i]` parçacık başına biriktirilir; çağıran taraf
    `Σ m·kirpilan` ile ne kadar enerjinin tabana çarptığını
    **raporlayabilir**. Sıfırdan farklıysa bu bir uyarıdır: `dt` ya da
    yapay viskozite fazla.
    """
    i = wp.tid()
    if active[i] != wp.uint8(0):
        yeni = u[i] + half_dt * dudt[i]
        if yeni < F(0.0):
            kirpilan[i] = kirpilan[i] - yeni      # pozitif birikir
            yeni = F(0.0)
        u[i] = yeni


@wp.kernel
def drift_3d(
    x: wp.array(dtype=V3),
    v: wp.array(dtype=V3),
    active: wp.array(dtype=wp.uint8),
    dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        x[i] = x[i] + dt * v[i]


@wp.kernel
def kick_v_1d(
    v: wp.array(dtype=F),
    a: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    half_dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        v[i] = v[i] + half_dt * a[i]


@wp.kernel
def kick_u_1d(
    u: wp.array(dtype=F),
    dudt: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    half_dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        u[i] = u[i] + half_dt * dudt[i]


@wp.kernel
def drift_1d(
    x: wp.array(dtype=F),
    v: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        x[i] = x[i] + dt * v[i]


@wp.kernel
def accumulate_1d(
    target: wp.array(dtype=F),
    rate: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        target[i] = target[i] + dt * rate[i]


@wp.kernel
def continuity_rate_3d(
    rho: wp.array(dtype=F),
    divv: wp.array(dtype=F),
    drhodt: wp.array(dtype=F),
):
    """drho/dt = -rho div v (ADR-0015). Yalnizca HIZI yazar, rho'yu ILERLETMEZ.

    Hiz, alan degerlendirmesi sirasinda DONDURULUR ve tekmelerde
    `accumulate_scalar_3d` ile uygulanir; boylece rho tam olarak u ve S ile
    ayni trapez yolundan gecer (ADR-0007). Bu ayrim onemli: hizi tekme aninda
    `rho*divv` diye yeniden hesaplamak, ikinci yarim tekmede GUNCELLENMIS
    rho'yu kullanir ve CPU referansindan dt*divv (~1e-5) mertebesinde
    SISTEMATIK olarak ayrilir. Capraz kontrol bunu 200 adimda 3.6e-8'lik
    sapma olarak yakaladi (sirf toplama sirasi etkisi 1.6e-13 iken).
    """
    i = wp.tid()
    drhodt[i] = -rho[i] * divv[i]


@wp.kernel
def accumulate_scalar_3d(
    target: wp.array(dtype=F),
    rate: wp.array(dtype=F),
    active: wp.array(dtype=wp.uint8),
    dt: F,
):
    i = wp.tid()
    if active[i] != wp.uint8(0):
        target[i] = target[i] + dt * rate[i]


@wp.kernel
def damp_velocity_3d(
    v: wp.array(dtype=V3),
    active: wp.array(dtype=wp.uint8),
    factor: F,
):
    """Hiz sonumleme: v <- factor * v  (FAZ 3 settling, P3-FR-05).

    Moloz yigini uretildikten sonra parcaciklar denge konumunda DEGILDIR;
    oz-yercekimi altinda yerlesirken istenmeyen kinetik enerji birikir. Bu
    enerji sondurulmezse carpma senaryosu, mermiden gelmeyen bir hareketle
    baslar ve beta olcumu kirlenir.

    Sonumleme CARPANLA yapilir (kuvvet olarak degil): deterministiktir,
    zaman adimindan bagimsizdir ve enerji defterinde ayrik bir kalem olarak
    izlenebilir.
    """
    i = wp.tid()
    if active[i] != wp.uint8(0):
        v[i] = factor * v[i]
