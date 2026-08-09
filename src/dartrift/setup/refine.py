"""A′'yı **DART sahnesine** bağla: çarpma noktası çevresinde yerel incelme.

## Neden gerekli

ADR-0026'nın kapattığı sorun şuydu: DART mermisi (~1,3 m) hedefin
çözünürlüğünden (`spacing` ~7 m) **küçük**. `measure_longrun` bunu zaten
raporluyor:

```
mermi cozunurlugu: ... HEDEF aralagina gore X parcacik/cap
UYARI: mermi hedef cozunurlugunun altinda — erken zamanli
       baglanma COZULMEMIS (ADR-0026)
```

Her yeri inceltmek `λ³` kat parçacık demek. A′ (ADR-0041) tam da bunun
için seçildi: **yalnızca çarpma bölgesi** incelir ve `h` **parçacık
başına** taşınır.

KAYIT-037 ölçtü ki bu, tam malzeme modelinde incelme kazancının
**%67,1**'ini veriyor; yalnızca parçacık eklemek (tek `h`) **%9,1**.

## Yapılan şey

İki sahne kurulur — biri `spacing`, biri `spacing/λ` — ve çarpma noktası
çevresinde `r_ince` yarıçaplı bir küre içinde **ince** sahnenin hedef
parçacıkları, dışında **kaba** sahnenin hedef parçacıkları kullanılır.
Mermi her zaman **ince** sahneden gelir (asıl amaç onu çözmek).

`h` parçacık başına: ince bölgede `2·spacing/λ`, kaba bölgede `2·spacing`.

## Bilerek yapılmayan

**Kütle korunumu tam değildir.** İki farklı kafes aynı küreyi farklı
döşer; sınırda küçük bir kütle uyuşmazlığı kalır. Ölçülüyor ve
`diagnostics`'e yazılıyor — gizlenmiyor. KAYIT-036'da aynı büyüklük küp
geometrisinde `%0,073` çıkmıştı.
"""
from __future__ import annotations

import numpy as np

__all__ = ["refine_scene", "refine_scene_local",
           "refine_scene_ucseviye", "RefinedScene"]

#: Tam ince sahnenin parçacık sayısı `mesh_hacmi / V_p` ile orantılı;
#: sabit `1,0` çünkü `particle_volume` zaten FCC paketlemeyi taşıyor.
INCE_TUM_SAHNE_C = 1.0


class RefinedScene:
    """`Scene` ile aynı alanlar + **parçacık başına `h`**.

    Ayrı bir sınıf, `Scene`'in değişmezlerini (tek `spacing`) bozmamak
    için: bu nesnenin **iki** aralığı var ve `spacing` tek başına
    anlamlı değil.
    """

    __slots__ = ("x", "v", "m", "alpha0", "Y0", "h", "is_impactor",
                 "is_boulder", "is_fine", "spacing_coarse", "spacing_fine",
                 "target_radius", "impact_point", "impact_direction",
                 "surface_normal", "diagnostics")

    def __init__(self, **kw):
        for k in self.__slots__:
            setattr(self, k, kw[k])

    @property
    def n(self) -> int:
        return len(self.m)

    @property
    def n_target(self) -> int:
        return int(np.count_nonzero(~self.is_impactor))

    @property
    def target_mass(self) -> float:
        return float(np.sum(self.m[~self.is_impactor]))

    @property
    def impactor_momentum(self) -> np.ndarray:
        s = self.is_impactor
        return np.sum(self.m[s, None] * self.v[s], axis=0)


def _dikis_kalitesi(x, mp, r_ince: float, s_kaba: float,
                    s_ince: float) -> dict:
    """Dikişte parçacıklar birbirine **ne kadar** yaklaşıyor?

    ## Neden ölçülmeli

    İki farklı aralıklı kafes küresel bir sınırda buluşuyor. Sınır
    hiçbir kafesin düğümlerine oturmadığı için **ikisinin de kendi
    aralığından daha yakın** çiftler oluşabilir. Çok yakın bir çift SPH'de
    büyük bir itme kuvveti ve yerel bir yoğunluk sıçraması demektir.

    Ölçüldü (`s = 7,0/3,5`, `r_iç = 25`, kuşakta 699 parçacık):

    | bölge | en yakın komşu (min) | ortanca |
    |---|---|---|
    | ince iç (`d < 20`) | 3,5000 | 3,5000 |
    | **dikiş kuşağı** | **2,2824** | 3,5000 |
    | kaba dış (`d > 32`) | 7,0000 | 7,0000 |

    Yani dikişte en yakın yaklaşma ince aralığın **`%65`**'i. Tehlikeli
    değil (`h_ince = 2·s = 7 m`, yani düzleştirme uzunluğunun üçte biri)
    ama **sıfır da değil** ve gizlenmemeli.

    Dönen `en_yakin_oran` bu sayıdır: `min(d) / s_ince`. `0,5`'in altına
    inerse kurulum gözden geçirilmelidir — o noktada çift, ince kafesin
    komşu mesafesinin yarısından yakındır.
    """
    d = np.linalg.norm(x - np.asarray(mp)[None, :], axis=1)
    kus = (d > r_ince - s_kaba) & (d < r_ince + s_kaba)
    n = int(kus.sum())
    if n < 2:
        return {"n_kusak": n, "en_yakin": float("nan"),
                "en_yakin_oran": float("nan"),
                "not": "dikiş kuşağında 2'den az parçacık — ölçülemedi"}
    xk = x[kus]
    # PARCALI O(n^2). Onceki surum tek seferde `n x n x 3` kuruyordu ve
    # yorumu *"kusak kucuk (yuzlerce)"* diyordu -- bu varsayim `lam = 2`'de
    # dogruydu, `lam = 19` + `r_ince = 9 m`'de **cokuyor**:
    #     n = 40 597  ->  40 597 x 40 597 x 3 x 8 B = 36,8 GiB  (patladi)
    # Ucuncu kez ayni kalip (bkz. `refine_scene_local` §4 ve `coarsen`).
    # Blok satir sayisi bellege gore secilir; sonuc DEGISMEZ.
    blok = max(1, (1 << 22) // max(len(xk), 1))
    en_yakin = np.inf
    for b in range(0, len(xk), blok):
        D = np.linalg.norm(xk[b:b + blok, None, :] - xk[None, :, :], axis=2)
        # Kosegen (i == j) haric tutulur: satir k'nin kosegeni sutun b+k.
        k = np.arange(D.shape[0])
        D[k, b + k] = np.inf
        en_yakin = min(en_yakin, float(D.min()))
    return {"n_kusak": n, "en_yakin": en_yakin,
            "en_yakin_oran": en_yakin / max(s_ince, 1e-300),
            "s_ince": s_ince, "kusak": [r_ince - s_kaba, r_ince + s_kaba]}


def refine_scene(kaba, ince, r_ince: float) -> RefinedScene:
    """Kaba ve ince sahneyi **çarpma noktası çevresinde** birleştir.

    Parameters
    ----------
    kaba, ince
        `build_scene` çıktıları. **Aynı** tohum, şekil ve mermi ile,
        yalnızca `spacing` farklı kurulmuş olmalıdır.
    r_ince
        İnce bölgenin yarıçapı [m], çarpma noktasından ölçülür.

    Notes
    -----
    Mermi her zaman **ince** sahneden alınır — A′'nın varlık nedeni onu
    çözmek. Kaba sahnenin mermisi atılır.
    """
    if r_ince <= 0.0:
        raise ValueError(f"r_ince pozitif olmalı, {r_ince} geldi")
    if not (ince.spacing < kaba.spacing):
        raise ValueError(
            f"ince aralık kabadan küçük olmalı: {ince.spacing} vs {kaba.spacing}")
    lam = kaba.spacing / ince.spacing
    # Iki sahne AYNI carpma noktasini gormeli; yoksa birlestirme anlamsiz.
    kayma = float(np.linalg.norm(np.asarray(kaba.impact_point)
                                 - np.asarray(ince.impact_point)))
    if kayma > kaba.spacing:
        raise ValueError(
            f"iki sahnenin çarpma noktası {kayma:.3f} m ayrı "
            f"(kaba aralık {kaba.spacing}); aynı tohum/şekil kullanılmalı")

    mp = np.asarray(ince.impact_point, dtype=np.float64)
    k_hedef = ~kaba.is_impactor
    i_hedef = ~ince.is_impactor
    d_kaba = np.linalg.norm(kaba.x - mp[None, :], axis=1)
    d_ince = np.linalg.norm(ince.x - mp[None, :], axis=1)

    sec_kaba = k_hedef & (d_kaba >= r_ince)
    sec_ince = i_hedef & (d_ince < r_ince)
    sec_mermi = ince.is_impactor
    if not np.any(sec_ince):
        raise ValueError(f"ince bölge boş: r_ince={r_ince} çok küçük")
    if not np.any(sec_kaba):
        raise ValueError(f"kaba bölge boş: r_ince={r_ince} hedefi kaplıyor")

    def _al(ad):
        return np.concatenate([getattr(ince, ad)[sec_ince],
                               getattr(kaba, ad)[sec_kaba],
                               getattr(ince, ad)[sec_mermi]])

    n_i, n_k = int(sec_ince.sum()), int(sec_kaba.sum())
    n_m = int(sec_mermi.sum())
    h = np.concatenate([
        np.full(n_i, 2.0 * ince.spacing),
        np.full(n_k, 2.0 * kaba.spacing),
        np.full(n_m, 2.0 * ince.spacing),
    ])
    is_fine = np.concatenate([np.ones(n_i, bool), np.zeros(n_k, bool),
                              np.ones(n_m, bool)])
    is_imp = np.concatenate([np.zeros(n_i + n_k, bool), np.ones(n_m, bool)])

    # KUTLE UYUSMAZLIGI: iki kafes ayni kureyi farkli doser. Olculur, yazilir.
    m_yeni = float(np.sum(_al("m")[~is_imp]))
    m_kaba = float(np.sum(kaba.m[k_hedef]))
    sapma = abs(m_yeni - m_kaba) / m_kaba

    x_yeni = _al("x")
    dikis = _dikis_kalitesi(x_yeni[~is_imp], mp, r_ince,
                            float(kaba.spacing), float(ince.spacing))

    return RefinedScene(
        x=_al("x"), v=_al("v"), m=_al("m"), alpha0=_al("alpha0"),
        Y0=_al("Y0"), h=h, is_impactor=is_imp, is_boulder=_al("is_boulder"),
        is_fine=is_fine,
        spacing_coarse=float(kaba.spacing), spacing_fine=float(ince.spacing),
        target_radius=float(kaba.target_radius),
        impact_point=mp, impact_direction=np.asarray(ince.impact_direction),
        surface_normal=np.asarray(ince.surface_normal),
        diagnostics={
            "lam": float(lam), "kutle_orani": float(lam ** 3),
            "r_ince": float(r_ince),
            "n_ince": n_i, "n_kaba": n_k, "n_mermi": n_m,
            "n_toplam": n_i + n_k + n_m,
            # Her yeri inceltseydik kac parcacik olurdu?
            "n_tumu_ince": int(np.count_nonzero(i_hedef)) + n_m,
            "tasarruf": float((int(np.count_nonzero(i_hedef)) + n_m)
                              / max(n_i + n_k + n_m, 1)),
            "hedef_kutle_sapmasi": sapma,
            # DIKIS KALITESI: iki kafesin bulustugu yerde parcaciklar
            # birbirine ne kadar yaklasiyor? Olculur, varsayilmaz.
            "dikis": dikis,
            "dikis_en_yakin_oran": dikis["en_yakin_oran"],
            "h_min": float(h.min()), "h_max": float(h.max()),
        },
    )


def refine_scene_local(kaba, mesh, r_ince: float, lam: float,
                       rho0_solid: float = 2700.0) -> RefinedScene:
    """A′ — ince bölgeyi **yerel** kur, tam ince sahne kurma.

    ## Neden gerekli: `refine_scene` yüksek `λ`'da **çalışamıyor**

    `refine_scene` iki **tam** sahne kurup birleştiriyor. Ölçüldü
    (`R = 82 m`, FCC):

    | `λ` | `s_ince` | tam ince sahne `N` | bellek |
    |---|---|---|---|
    | 2 | 3,500 m | 76 180 | 0,02 GB |
    | 6 | 1,167 m | 2 056 860 | 0,62 GB |
    | **19** | **0,368 m** | **65 314 837** | **19,6 GB** |

    ADR-0043 `λ ≈ 19` öneriyor ve orada `refine_scene` **kurulamaz** —
    oysa gerçekten gereken `r_iç = 3 m` içinde **~1400** parçacık.
    Yani `%99,998`'i kurulup atılıyordu.

    ## Yapılan

    İnce kafes yalnızca çarpma noktası çevresindeki **kutuda** kuruluyor
    (`lattice_points`), sonra iki süzgeçten geçiyor: mesh'in **içinde**
    (`inside_points`) ve `r_iç` **içinde**.

    ## `α₀` ve `Y₀` en yakın kaba parçacıktan alınıyor

    Moloz yığınında bunlar parçacık başına (matris vs kaya bloğu). İnce
    bölgeye tekdüze matris değeri vermek **kaya bloklarını silerdi** ve
    `f_boulder` çıkarımın parametrelerinden biri. En yakın komşudan
    örneklemek yapıyı korur.

    > Bu bir **yaklaşımdır**: blok sınırları ince kafeste kaba kafesin
    > çözünürlüğünde kalır. Ölçülmedi; `diagnostics`'e yazılıyor.
    """
    from .rubble_generator import lattice_points, particle_volume
    from .shape_mesh import inside_points

    if lam <= 1.0:
        raise ValueError(f"lam > 1 olmalı, {lam} geldi")
    if r_ince <= 0.0:
        raise ValueError(f"r_ince pozitif olmalı, {r_ince} geldi")
    s_kaba = float(kaba.spacing)
    s_ince = s_kaba / float(lam)
    mp = np.asarray(kaba.impact_point, dtype=np.float64)

    # KORUMA KAFESTEN ONCE GELIR. Ilk surumde `r_ince` dogrulamasi kafes
    # KURULDUKTAN SONRA yapiliyordu; `r_ince = 1e4` verince numpy
    # "412 TiB ayrilamiyor" diyordu -- anlasilmaz ve gec. Kendi testim
    # yakaladi.
    R = float(kaba.target_radius)
    if r_ince > 2.0 * R:
        raise ValueError(
            f"r_ince ({r_ince} m) hedef çapından ({2 * R} m) büyük — "
            f"ince bölge bütün cismi kaplar, kaba bölge boş kalır")
    # Kafes nokta sayisi ONCEDEN kestirilir; kutu kupu / hucre hacmi.
    kenar = 2.0 * (r_ince + 2.0 * s_ince)
    tahmini = 4.0 * (kenar / (s_ince * np.sqrt(2.0))) ** 3      # FCC: 4 baz
    if tahmini > 5.0e7:
        raise ValueError(
            f"yerel kafes çok büyük olurdu: ~{tahmini:.3g} nokta "
            f"(r_ince={r_ince}, s_ince={s_ince:.4g}). r_ince'i küçültün.")

    # 1) YEREL kafes: yalnizca carpma noktasi cevresindeki kutu.
    pay = 2.0 * s_ince
    lo, hi = mp - (r_ince + pay), mp + (r_ince + pay)
    pts = lattice_points(lo, hi, s_ince, "fcc")
    if len(pts) == 0:
        raise ValueError("yerel kafes boş — r_ince çok küçük olabilir")
    # 2) Iki suzgec: mesh ICINDE ve r_ince ICINDE.
    d = np.linalg.norm(pts - mp[None, :], axis=1)
    pts = pts[d < r_ince]
    if len(pts) == 0:
        raise ValueError(f"r_ince={r_ince} içinde kafes noktası yok")
    x_i = pts[inside_points(mesh, pts)]
    if len(x_i) == 0:
        raise ValueError("ince bölge mesh'in tamamen dışında")

    # 3) Kaba taraf: hedefin r_ince DISINDA kalanlari.
    k_hedef = ~kaba.is_impactor
    d_kaba = np.linalg.norm(kaba.x - mp[None, :], axis=1)
    sec_kaba = k_hedef & (d_kaba >= r_ince)
    if not np.any(sec_kaba):
        raise ValueError(f"kaba bölge boş: r_ince={r_ince} hedefi kaplıyor")
    # CIKARILAN kaba parcaciklar: kabalastirmanin DOGAL hedef siteleri
    # (ADR-0043 §5). Burada saklanmazsa tuketici ayni secimi yeniden
    # yazmak zorunda kalir -- raporun iki kez yakaladigi kalip.
    cikarilan_x = kaba.x[k_hedef & (d_kaba < r_ince)].copy()

    # 4) alpha0/Y0: EN YAKIN kaba parcaciktan (kaya bloku yapisini korur).
    #
    # PARCALI. Onceki surum `x_i[:, None, :] - hedef_x[None, :, :]` ile
    # N_ince x N_kaba x 3 bir dizi kuruyordu -- `412 TiB` kusurunun aynisi,
    # yalnizca daha yavas patliyor:
    #     r_ince = 3 m  ->  1 524 x  9 544 x 3 x 8 B = 0,35 GB   (gecer)
    #     r_ince = 6 m  -> 12 210 x  9 544 x 3 x 8 B = 2,8  GB   (10,5 s)
    #     r_ince = 9 m  -> ~41 000 x 9 544 x 3 x 8 B = 9,4  GB   (patlar)
    # `r_ince`'i buyutmek ADR-0043 icin gerekli oldugundan bu bir engeldi.
    hedef_x = kaba.x[k_hedef]
    idx = np.empty(len(x_i), dtype=np.int64)
    for b in range(0, len(x_i), 2048):
        idx[b:b + 2048] = np.argmin(np.linalg.norm(
            x_i[b:b + 2048, None, :] - hedef_x[None, :, :], axis=2), axis=1)
    a0_i = kaba.alpha0[k_hedef][idx]
    y0_i = kaba.Y0[k_hedef][idx]
    blok_i = kaba.is_boulder[k_hedef][idx]

    # 5) Kutle YEREL hucre hacminden (ADR-0030).
    # `alpha0` parcacik basina: m = rho_yigin * V_p = (rho0/alpha0) * V_p
    m_i = (rho0_solid / a0_i) * particle_volume(s_ince, "fcc")

    # 6) Mermi KABA sahneden -- kendi ayriklastirmasi `n_impactor`'a bagli,
    #    `spacing`'e DEGIL, yani iki sahnede AYNI.
    sec_mermi = kaba.is_impactor
    n_i, n_k, n_m = len(x_i), int(sec_kaba.sum()), int(sec_mermi.sum())

    def _kat(ince_deger, ad):
        return np.concatenate([ince_deger, getattr(kaba, ad)[sec_kaba],
                               getattr(kaba, ad)[sec_mermi]])

    x = _kat(x_i, "x")
    v = _kat(np.zeros_like(x_i), "v")
    m = _kat(m_i, "m")
    alpha0 = _kat(a0_i, "alpha0")
    Y0 = _kat(y0_i, "Y0")
    is_boulder = _kat(blok_i, "is_boulder")
    h = np.concatenate([np.full(n_i, 2.0 * s_ince),
                        np.full(n_k, 2.0 * s_kaba),
                        np.full(n_m, 2.0 * s_ince)])
    is_fine = np.concatenate([np.ones(n_i, bool), np.zeros(n_k, bool),
                              np.ones(n_m, bool)])
    is_imp = np.concatenate([np.zeros(n_i + n_k, bool), np.ones(n_m, bool)])

    m_yeni = float(np.sum(m[~is_imp]))
    m_kaba = float(np.sum(kaba.m[k_hedef]))
    dikis = _dikis_kalitesi(x[~is_imp], mp, r_ince, s_kaba, s_ince)
    n_tumu_ince = int(round(INCE_TUM_SAHNE_C * (kaba.mesh_volume
                                                / particle_volume(s_ince, "fcc"))))
    return RefinedScene(
        x=x, v=v, m=m, alpha0=alpha0, Y0=Y0, h=h, is_impactor=is_imp,
        is_boulder=is_boulder, is_fine=is_fine,
        spacing_coarse=s_kaba, spacing_fine=s_ince,
        target_radius=float(kaba.target_radius), impact_point=mp,
        impact_direction=np.asarray(kaba.impact_direction),
        surface_normal=np.asarray(kaba.surface_normal),
        diagnostics={
            "yerel_kurulum": True, "lam": float(lam),
            "kutle_orani": float(lam) ** 3, "r_ince": float(r_ince),
            "n_ince": n_i, "n_kaba": n_k, "n_mermi": n_m,
            "n_toplam": n_i + n_k + n_m,
            "n_tumu_ince": n_tumu_ince,
            "tasarruf": float(n_tumu_ince / max(n_i + n_k + n_m, 1)),
            "hedef_kutle_sapmasi": abs(m_yeni - m_kaba) / m_kaba,
            "dikis": dikis,
            "dikis_en_yakin_oran": dikis["en_yakin_oran"],
            "h_min": float(h.min()), "h_max": float(h.max()),
            # YAKLASIM: blok sinirlari ince kafeste KABA cozunurlukte kalir.
            "blok_sinirlari_kaba_cozunurlukte": True,
            # Kabalastirmanin hedef siteleri (ADR-0043 §5).
            "cikarilan_kaba_x": cikarilan_x,
            "n_cikarilan_kaba": int(len(cikarilan_x)),
        },
    )


def refine_scene_ucseviye(kaba, mesh, r1: float, lam1: float,
                          r2: float, lam2: float,
                          rho0_solid: float = 2700.0) -> RefinedScene:
    """**Üç seviyeli** sahne — ADR-0043 §4f'nin gerektirdiği kurulum.

    ## Neden iki seviye yetmiyor

    İki seviyeli aşama-1 (`λ=19`, `r_iç=3 m`) ile FAZ 4.8 koştu ve
    **momentum kapanışı `0,690`** verdi. Ölçüldü: `t₁ = 4,767e-3 s`'de

    | bölge | momentum |
    |---|---|
    | ince (`r < 3 m`) — aktarılan | **`0,310`** |
    | kaba — **atılan** | **`0,690`** |

    Bozulma `t₁`'de `~35–48 m`'ye yayılmış; `r_iç = 3 m` bunun onda
    biri. Aktarım aşama-1'in kaba bölgesini atıyordu çünkü orada
    aşama-1 (`7 m`) aşama-2'den (`3,5 m`) **daha kaba** — kabadan
    inceye geçiş iyi tanımlı değil.

    ## Yapılan

    ```
    r < r1        lam1  (mermi cozulmus)
    r1 < r < r2   lam2  (asama-2 ile AYNI aralik)
    r > r2        kaba  (degismemis)
    ```

    Böylece aktarım yalnızca `r < r1`'i kabalaştırır; `r1 < r < r2`
    aşama-2'yle **birebir aynı çözünürlükte** olduğu için kopyalanır
    ve **hiçbir momentum atılmaz**.

    `dt` zaten `lam1` çekirdeğinden geliyor, yani eklenen orta seviye
    zaman adımını **değiştirmiyor**; yalnızca parçacık sayısını artırıyor.
    """
    from .rubble_generator import lattice_points, particle_volume
    from .shape_mesh import inside_points

    if not (0.0 < r1 < r2):
        raise ValueError(f"0 < r1 < r2 gerekir; r1={r1}, r2={r2} geldi")
    if lam1 <= lam2:
        raise ValueError(f"lam1 > lam2 gerekir (ic bolge DAHA ince); "
                         f"lam1={lam1}, lam2={lam2} geldi")

    # 1) TABAN: iki seviyeli sahne (lam2, r2). Bu, ASAMA-2 ile ayni
    #    cozunurlugu `r2` icinde zaten kuruyor.
    taban = refine_scene_local(kaba, mesh, r_ince=r2, lam=lam2,
                               rho0_solid=rho0_solid)
    s1 = float(kaba.spacing) / float(lam1)
    mp = np.asarray(kaba.impact_point, dtype=np.float64)

    # 2) Cekirdegi (r < r1) SIL ve lam1 kafesiyle yeniden kur.
    #    Mermi DOKUNULMAZ: kendi ayriklastirmasi var.
    imp = np.asarray(taban.is_impactor, dtype=bool)
    d_t = np.linalg.norm(np.asarray(taban.x) - mp[None, :], axis=1)
    silinen = (~imp) & (d_t < r1)
    tut = ~silinen

    pay = 2.0 * s1
    pts = lattice_points(mp - (r1 + pay), mp + (r1 + pay), s1, "fcc")
    if len(pts) == 0:
        raise ValueError("çekirdek kafesi boş — r1 çok küçük olabilir")
    pts = pts[np.linalg.norm(pts - mp[None, :], axis=1) < r1]
    if len(pts) == 0:
        raise ValueError(f"r1={r1} içinde kafes noktası yok")
    x_c = pts[inside_points(mesh, pts)]
    if len(x_c) == 0:
        raise ValueError("çekirdek mesh'in tamamen dışında")

    # 3) alpha0/Y0 en yakin KABA parcaciktan (kaya bloku yapisi korunsun).
    #    PARCALI -- `N x M x 3` asla parcasiz kurulmaz.
    k_hedef = ~np.asarray(kaba.is_impactor, dtype=bool)
    hedef_x = np.asarray(kaba.x)[k_hedef]
    idx = np.empty(len(x_c), dtype=np.int64)
    for b in range(0, len(x_c), 2048):
        idx[b:b + 2048] = np.argmin(np.linalg.norm(
            x_c[b:b + 2048, None, :] - hedef_x[None, :, :], axis=2), axis=1)
    a0_c = np.asarray(kaba.alpha0)[k_hedef][idx]
    y0_c = np.asarray(kaba.Y0)[k_hedef][idx]
    blok_c = np.asarray(kaba.is_boulder)[k_hedef][idx]
    m_c = (rho0_solid / a0_c) * particle_volume(s1, "fcc")

    n_c = len(x_c)

    def _kat(cekirdek, ad):
        return np.concatenate([cekirdek, np.asarray(getattr(taban, ad))[tut]])

    x = _kat(x_c, "x")
    v = _kat(np.zeros_like(x_c), "v")
    m = _kat(m_c, "m")
    alpha0 = _kat(a0_c, "alpha0")
    Y0 = _kat(y0_c, "Y0")
    is_boulder = _kat(blok_c, "is_boulder")
    is_imp = np.concatenate([np.zeros(n_c, bool), imp[tut]])
    # Mermi `lam1` cozunurlugunde olmali (A1 orada saglaniyor).
    h_taban = np.asarray(taban.h)[tut].copy()
    h_taban[imp[tut]] = 2.0 * s1
    h = np.concatenate([np.full(n_c, 2.0 * s1), h_taban])
    # `is_fine` = EN INCE seviye (cekirdek + mermi) -- aktarilacak kume.
    is_fine = np.concatenate([np.ones(n_c, bool), imp[tut]])

    m_yeni = float(np.sum(m[~is_imp]))
    m_kaba = float(np.sum(np.asarray(kaba.m)[k_hedef]))
    tani = dict(taban.diagnostics)
    tani.update({
        "ucseviye": True, "r1": float(r1), "lam1": float(lam1),
        "r2": float(r2), "lam2": float(lam2),
        "s1": s1, "s2": float(taban.spacing_fine),
        "n_cekirdek": n_c, "n_orta_ve_kaba": int(tut.sum()),
        "n_silinen": int(silinen.sum()), "n_toplam": len(m),
        "hedef_kutle_sapmasi": abs(m_yeni - m_kaba) / m_kaba,
        "h_min": float(h.min()), "h_max": float(h.max()),
    })
    return RefinedScene(
        x=x, v=v, m=m, alpha0=alpha0, Y0=Y0, h=h, is_impactor=is_imp,
        is_boulder=is_boulder, is_fine=is_fine,
        spacing_coarse=float(kaba.spacing), spacing_fine=s1,
        target_radius=float(kaba.target_radius), impact_point=mp,
        impact_direction=np.asarray(kaba.impact_direction),
        surface_normal=np.asarray(kaba.surface_normal),
        diagnostics=tani)
