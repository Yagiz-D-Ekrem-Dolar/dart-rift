"""Aşama-1'in ince parçacıklarını aşama-2'nin kaba kafesine **aktar**.

ADR-0043 §5'in *"mevcut değil"* dediği adım. Kilitlenmesi için
gereken şey bu operatörün **var olması** değil, korunum hatasının
**ölçülmüş** olması (§7 madde 2).

## Neden naif ortalama reddedildi

ADR-0043 §5 açıkça yazıyor: *"ince parçacıkları grupla, ortalamasını
al"* momentumu **korumaz**. KAYIT-027 aynı tuzağı ölçmüştü: C
yaklaşımının ara değerlemesi momentumu `7,5e-03` **sistematik**
kaybediyordu. Bu modül o hatayı tekrarlamamak için yazıldı.

## Operatör

Her ince parçacık **en yakın** kaba bölgeye atanır. Atama bir
**bölüntüdür** (her parçacık tam bir gruba), korunumun temeli bu.

| büyüklük | kural | korunur mu |
|---|---|---|
| kütle | `m_k = Σ m_i` | **tam** (bölüntü) |
| momentum | `v_k = Σ m_i v_i / m_k` | **tam** (tanım gereği) |
| iç enerji | `e_k = (Σ m_i e_i + ½ Σ m_i \\|v_i − v_k\\|²) / m_k` | **tam** |
| konum | kütle merkezi | — |
| açısal momentum | — | **HAYIR**, artık ölçülür |

> Açısal momentum kaybını `|L₀|`'a bölmek **merkezi çarpmada
> anlamsız**: net `L₀ ≈ 0` olduğu için oran `%70 000` gibi çıkıyor ve
> hiçbir şey söylemiyor. Okunması gereken
> `acisal_momentum_kayip_olcekli` — paydası ulaşılabilir en büyük
> değer, `Σ mᵢ|xᵢ||vᵢ|`.

### Korunumun **görmediği** şey: atama mesafesi

Üç korunum yasası da tam olsa bile kütle **uzağa** taşınmış olabilir:
bir parçacık komşu olmayan bir siteye atanırsa toplamlar tutar ama
madde ışınlanmıştır. `korunum["atama_mesafe_max"]` bunu ayrıca
raporlar; `s_kaba`'yı çok aşıyorsa aktarım geometrik olarak bozuktur.

### Enerjinin püf noktası

Hızları ortalamak kinetik enerji **kaybettirir**: `½Σm_i|v_i|² ≥
½m_k|v_k|²`. Kayıp tam olarak grup içi hız **saçılımının** kinetik
enerjisidir. Onu `e_k`'ye eklemek toplam enerjiyi **tam** korur.

> Bu fiziksel olarak da doğru yön: çözülemeyen alt-ölçek hız saçılımı
> ısıya döner. Ama bir **seçimdir** ve sonucu var: kaba parçacık
> **ısınır**, basıncı artar. `korunum["ice_donen_kinetik_oran"]` bunu
> raporlar; sıfır değilse aktarım termodinamik olarak nötr değildir.

### Açısal momentum neden korunamıyor

`Σ m_i x_i × v_i = m_k x_km × v_k + Σ m_i δx_i × δv_i`. İkinci terim
grubun **kendi dönüşü** ve tek bir parçacıkla temsil edilemez. Kaba
tanecikleştirmenin kaçınılmaz kaybı; **iddia edilmiyor, ölçülüyor**.
"""
from __future__ import annotations

import numpy as np

__all__ = ["coarsen_to_sites", "korunum_raporu", "sites_from_cloud",
           "komsu_sagligi"]


def _en_yakin_site(x: np.ndarray, siteler: np.ndarray,
                   parca: int = 4096) -> np.ndarray:
    """Her `x` için en yakın site indeksi. Parçalı — bellek patlamasın.

    `refine_scene_local`'ın `412 TiB` dersi: `N×M×3` bir dizi asla
    topluca kurulmaz.
    """
    out = np.empty(len(x), dtype=np.int64)
    for b in range(0, len(x), parca):
        d = np.linalg.norm(x[b:b + parca, None, :] - siteler[None, :, :],
                           axis=2)
        out[b:b + parca] = np.argmin(d, axis=1)      # eşitlikte EN KÜÇÜK indeks
    return out


def coarsen_to_sites(x, v, m, e, siteler, alpha0=None, Y0=None,
                     is_boulder=None, mermi_kesri=None) -> dict:
    """İnce parçacıkları `siteler`e **korunumlu** aktar.

    Boş kalan siteler **düşürülür** — parçacığı olmayan bir siteye
    kütle uydurmak kütleyi bozardı.

    `alpha0`/`Y0` kütle-ağırlıklı ortalanır. Bunlar korunum yasasına
    **tabi değil**; yaklaşım olduğu `korunum` sözlüğünde işaretli.

    ## `mermi_kesri` — neden bayrak değil **kesir**

    `is_boulder` bir bayrak ve kütle çoğunluğuyla karara bağlanıyor;
    orada bu doğru, çünkü blokluk bir malzeme kimliği.

    Mermi için bayrak **yetmiyor**. Kabalaştırma mermi ve hedef
    maddesini aynı siteye karıştırabiliyor ve karışım kaçınılmaz:
    `λ₁ = 19` çekirdeği `λ₂ = 2` ızgarasına inerken bir sitenin içinde
    ikisi birlikte bulunur. Bayrak o siteyi *"tamamı mermi"* ya da
    *"tamamı hedef"* yapardı ve momentum ayrıştırması **yanlış**
    olurdu.

    Kesir kütle-ağırlıklı taşındığı için toplam mermi kütlesi **tam**
    korunur: `Σ m_k f_k = Σ m_i f_i`. Bu bir yaklaşım değil, pasif
    skalerin doğru aktarımı.

    ### Bu alan neden gerekliydi

    Aktarımdan sonra `is_impactor` hiçbir parçacıkta korunmuyordu
    (`two_stage` bunu bilerek yapıyor) ve `hedef = ~is_impactor`
    **her yerde `True`** oluyordu. Sonuç: `β`'nın kaçan `28`
    parçacığı *"hedef ejektası"* olarak etiketleniyordu, oysa toplam
    kütleleri `579,40 kg` — merminin kendisi — ve parçacık kütleleri
    `0,72–55,75 kg` iken hedef parçacıklarının medyanı `3,73e5 kg`.

    > Kimlik kütleden **çıkarılabiliyordu** ama taşınmıyordu. `β`'yı
    > *"mermi geri sekmesi"* ile *"hedef ejektası"* arasında ayırmak
    > bu alan olmadan mümkün değil (rapor A17).
    """
    x = np.asarray(x, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    e = np.asarray(e, dtype=np.float64)
    siteler = np.asarray(siteler, dtype=np.float64)
    if len(siteler) == 0:
        raise ValueError("site listesi boş — aktarılacak hedef yok")
    if not (len(x) == len(v) == len(m) == len(e)):
        raise ValueError(f"uzunluklar uyuşmuyor: x={len(x)} v={len(v)} "
                         f"m={len(m)} e={len(e)}")
    if len(x) == 0:
        raise ValueError("aktarılacak ince parçacık yok")
    if np.any(m <= 0.0):
        raise ValueError("kütleler pozitif olmalı")

    idx = _en_yakin_site(x, siteler)
    ns = len(siteler)

    # --- KUTLE: atama bir BOLUNTU oldugu icin TAM.
    m_k = np.bincount(idx, weights=m, minlength=ns)
    dolu = m_k > 0.0
    if not np.any(dolu):
        raise ValueError("hiçbir site parçacık almadı")

    # --- MOMENTUM: once toplanir, SONRA bolunur. Tersi hataya acik.
    p_k = np.stack([np.bincount(idx, weights=m * v[:, d], minlength=ns)
                    for d in range(3)], axis=1)
    xm_k = np.stack([np.bincount(idx, weights=m * x[:, d], minlength=ns)
                     for d in range(3)], axis=1)
    me_k = np.bincount(idx, weights=m * e, minlength=ns)

    md = m_k[dolu][:, None]
    v_k = p_k[dolu] / md
    x_k = xm_k[dolu] / md

    # --- ENERJI: ortalamada KAYBOLAN kinetigi ic enerjiye ekle.
    # dv = v_i - v_k(grubu); kayip = 1/2 sum m_i |dv|^2.
    harita = -np.ones(ns, dtype=np.int64)
    harita[dolu] = np.arange(int(dolu.sum()))
    dv = v - v_k[harita[idx]]
    sacilim = 0.5 * np.bincount(idx, weights=m * np.einsum("ij,ij->i", dv, dv),
                                minlength=ns)[dolu]
    e_k = (me_k[dolu] + sacilim) / m_k[dolu]

    out: dict = {"x": x_k, "v": v_k, "m": m_k[dolu], "e": e_k,
                 "site_idx": np.flatnonzero(dolu), "atama": idx}
    for ad, dizi in (("alpha0", alpha0), ("Y0", Y0)):
        if dizi is not None:
            w = np.bincount(idx, weights=m * np.asarray(dizi, np.float64),
                            minlength=ns)
            out[ad] = w[dolu] / m_k[dolu]
    if is_boulder is not None:
        # Kutle COGUNLUGU blok mu? Ortalama alinamaz, bu bir bayrak.
        b = np.bincount(idx, weights=m * np.asarray(is_boulder, np.float64),
                        minlength=ns)
        out["is_boulder"] = (b[dolu] / m_k[dolu]) > 0.5
    if mermi_kesri is not None:
        f = np.asarray(mermi_kesri, dtype=np.float64)
        if len(f) != len(m):
            raise ValueError(f"mermi_kesri uzunlugu {len(f)} != {len(m)}")
        if np.any(f < 0.0) or np.any(f > 1.0):
            raise ValueError("mermi_kesri [0,1] araliginda olmali")
        w = np.bincount(idx, weights=m * f, minlength=ns)
        out["mermi_kesri"] = w[dolu] / m_k[dolu]
        # Toplam mermi kutlesi TAM korunmali -- kesir pasif skaler.
        # (`korunum` sozlugu asagida yaziliyor; bu alan ust duzeyde
        #  tutuluyor ki oranin uzerine yazilmasin.)
        onceki = float((m * f).sum())
        sonraki = float((out["m"] * out["mermi_kesri"]).sum())
        out["mermi_kutle_hatasi"] = (abs(sonraki - onceki)
                                     / max(onceki, 1e-300))

    # ATAMA MESAFESI: korunum tam olsa bile kutle UZAGA tasinmis olabilir.
    # Bir parcacik komsu olmayan bir siteye atandiysa aktarim maddeyi
    # ISINLIYOR demektir ve korunum bunu GORMEZ -- ayri bir tani gerekli.
    d_atama = np.linalg.norm(x - siteler[idx], axis=1)
    out["korunum"] = korunum_raporu(x, v, m, e, x_k, v_k, out["m"], e_k,
                                    sacilim)
    out["korunum"]["atama_mesafe_max"] = float(d_atama.max())
    out["korunum"]["atama_mesafe_ort"] = float(
        np.average(d_atama, weights=m))
    out["korunum"]["n_giren"] = int(len(x))
    out["korunum"]["n_cikan"] = int(dolu.sum())
    out["korunum"]["n_bos_site"] = int(ns - dolu.sum())
    out["korunum"]["grup_en_buyuk"] = int(np.bincount(idx, minlength=ns).max())
    out["korunum"]["alpha0_Y0_yaklasim"] = True
    return out


def korunum_raporu(x, v, m, e, x_k, v_k, m_k, e_k, sacilim) -> dict:
    """Aktarımın **korunum hatası** — üçü ayrı ayrı (ADR-0043 §5).

    Göreli hata; payda büyüklüğün kendisi (sıfıra bölünme korumalı).
    Momentum ve açısal momentum **vektör**, normları alınıyor.
    """
    def _gor(a, b):
        payda = max(abs(a), 1e-300)
        return float(abs(b - a) / payda)

    def _gor_vek(a, b):
        payda = max(float(np.linalg.norm(a)), 1e-300)
        return float(np.linalg.norm(b - a) / payda)

    M0, M1 = float(m.sum()), float(m_k.sum())
    P0 = (m[:, None] * v).sum(axis=0)
    P1 = (m_k[:, None] * v_k).sum(axis=0)
    # Enerji: ic + kinetik. Toplam korunmali.
    E0 = float((m * (e + 0.5 * np.einsum("ij,ij->i", v, v))).sum())
    E1 = float((m_k * (e_k + 0.5 * np.einsum("ij,ij->i", v_k, v_k))).sum())
    L0 = (m[:, None] * np.cross(x, v)).sum(axis=0)
    L1 = (m_k[:, None] * np.cross(x_k, v_k)).sum(axis=0)
    K0 = float((0.5 * m * np.einsum("ij,ij->i", v, v)).sum())
    # `|L0|`'a bolmek MERKEZI carpmada anlamsiz: net acisal momentum ~0
    # oldugu icin gorece hata %70000 gibi cikiyor ve hicbir sey soylemiyor.
    # Anlamli payda ULASILABILIR en buyuk deger: sum m_i |x_i| |v_i|.
    L_olcek = float((m * np.linalg.norm(x, axis=1)
                     * np.linalg.norm(v, axis=1)).sum())
    return {
        "kutle_hata": _gor(M0, M1),
        "momentum_hata": _gor_vek(P0, P1),
        "enerji_hata": _gor(E0, E1),
        # Bu KORUNMUYOR; esik degil, TANIDIR.
        "acisal_momentum_hata": _gor_vek(L0, L1),
        # ASIL okunmasi gereken: kayip, ULASILABILIR olcege gore.
        "acisal_momentum_kayip_olcekli": float(
            np.linalg.norm(L1 - L0) / max(L_olcek, 1e-300)),
        "acisal_momentum_olcek": L_olcek,
        "ice_donen_kinetik_oran": float(sacilim.sum() / max(K0, 1e-300)),
        "kutle_giren": M0, "kutle_cikan": M1,
        "enerji_giren": E0, "enerji_cikan": E1,
    }


# --------------------------------------------------------------------------
# LAGRANGE'CI hedef site uretimi (ADR-0043 §7 madde 5)
# --------------------------------------------------------------------------

def sites_from_cloud(x, s_hedef: float, paketleme: str = "fcc") -> np.ndarray:
    """`t₁` anındaki **mevcut** bulutun üzerine hedef kafes otur.

    ## Neden gerekli

    Euler'ci sürüm — hedef siteleri aşama-2'nin **başlangıç** kafesinden
    almak — ölçüldü ve **düştü** (ADR-0043 §4c):

    | `t₁` | atama mesafesi |
    |---|---|
    | `1e-3 s` | `0,97` hücre |
    | `4,77e-3 s` (ölçülen `t₁`) | **`4,35` hücre** |
    | `1e-2 s` | **`10,16` hücre = 35,6 m** |

    Sebep basit: hedef siteler sabit duruyor, **madde gidiyor**. `t₁`'e
    kadar ince bölgenin maddesi `r_iç`'in çok dışına çıkıyor ve aktarım
    onu geri **ışınlıyor**. Korunum bunu görmüyor; toplamlar tutuyor.

    ## Yapılan

    Bulut, kenarı `a` olan bir kübik ızgaraya bölünür; **dolu** hücrelerin
    merkezleri site olur. Böylece **her** parçacık kendi hücresinin
    merkezine `≤ a√3/2` uzaklıkta kalır — atama mesafesi **yapı gereği**
    sınırlı.

    ## `a` neden `s_hedef` değil

    Aşama-2 FCC ve parçacık hacmi `s³/√2`. Kübik ızgarada hücre başına bir
    parçacık düşer, hacim `a³`. Aynı parçacık hacmi için:

        a³ = s³/√2   →   a = s / 2^(1/6) ≈ 0,8909 · s

    Yani aktarılan parçacıklar aşama-2'nin parçacıklarıyla **aynı hacmi**
    temsil eder. `s_hedef` doğrudan kullanılsaydı `%41` daha büyük
    hacimler çıkardı ve kütle-yoğunluk tutarlılığı bozulurdu.

    Returns
    -------
    (M, 3) site konumları. Belirlenimci: hücre indeksine göre sıralı.
    """
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != 3:
        raise ValueError(f"x (N,3) olmalı, {x.shape} geldi")
    if len(x) == 0:
        raise ValueError("bulut boş — site üretilemez")
    if not np.all(np.isfinite(x)):
        raise ValueError("bulutta sonlu olmayan konum var")
    if s_hedef <= 0.0:
        raise ValueError(f"s_hedef pozitif olmalı, {s_hedef} geldi")
    if paketleme not in ("fcc", "kubik"):
        raise ValueError(f"paketleme 'fcc' ya da 'kubik' olmalı, "
                         f"{paketleme!r} geldi")
    a = s_hedef / 2.0 ** (1.0 / 6.0) if paketleme == "fcc" else s_hedef

    kok = x.min(axis=0)
    hucre = np.floor((x - kok[None, :]) / a).astype(np.int64)
    # BELIRLENIMCI benzersizlestirme: satirlari sirali dondurur.
    tekil = np.unique(hucre, axis=0)
    return kok[None, :] + (tekil + 0.5) * a


def komsu_sagligi(x_k, h: float, destek_over_h: float = 2.0,
                  cevre=None) -> dict:
    """Kabalaştırılmış kümede **komşu sayısı** yeterli mi.

    ## Neden ayrı bir kontrol

    Korunum ve atama mesafesi *"madde doğru yerde ve doğru miktarda mı"*
    diye soruyor. Ama aşama-2 bu parçacıkları **SPH ile** ilerletecek ve
    SPH'nin çalışması için her parçacığın **yeterli komşusu** olmalı.

    Aktarım tam da maddenin **genişlediği** anda yapılıyor
    (`t₁ = 4,77e-3 s`'de bulut `r_iç`'in dışına taşmış durumda). Genişleyen
    bir bulutta `s₂` aralıklı hücrelerin çoğu **kenar** hücresi olur ve
    kenardaki parçacığın komşusu azdır.

    > Aşama-2 parçacıkları `h = 2·s₂` ile geliyor (ADR-0041). Düzgün bir
    > FCC kafeste `2h = 4·s₂` yarıçapı içinde `~250` komşu var. Aktarılan
    > kümede bu sayı **çok** düşerse yoğunluk toplamı bozulur ve
    > `ρ` sistematik olarak **düşük** çıkar.

    Ölçülen: `2h` destek yarıçapı içindeki komşu sayısının dağılımı.
    Bir eşik **konmuyor** — bu bir tanı; eşiği ADR yazarı koyar.

    Parameters
    ----------
    cevre
        Aktarılan kümenin **etrafındaki** parçacıklar (aşama-2'nin geri
        kalanı). Verilmezse komşular **yalnızca `x_k` içinde** sayılır
        ve sonuç **kötümser** olur.

        İlk sürümde bu parametre yoktu ve ön uçuşta `komşu medyan = 27`,
        `<30 oranı = 1,000` çıktı — yani *"her aktarılan parçacık
        komşusuz"*. **Yanıltıcıydı:** birleşik sahnede o parçacıkların
        aşama-2 komşuları da var. Ölçüm birleşik bulut üzerinde
        yapılmalı, aktarılan **alt kümesi** için raporlanmalı.
    """
    x_k = np.asarray(x_k, dtype=np.float64)
    if x_k.ndim != 2 or x_k.shape[1] != 3:
        raise ValueError(f"x_k (M,3) olmalı, {x_k.shape} geldi")
    if len(x_k) == 0:
        raise ValueError("boş küme — komşu sayılamaz")
    if h <= 0.0:
        raise ValueError(f"h pozitif olmalı, {h} geldi")
    destek = destek_over_h * h
    # KOMSULAR BIRLESIK BULUTTA sayilir; istatistik `x_k` icin verilir.
    tum = x_k if cevre is None else np.vstack(
        [x_k, np.asarray(cevre, dtype=np.float64)])

    # PARCALI (kural: N x M x 3 asla parcasiz).
    n, nt = len(x_k), len(tum)
    sayi = np.zeros(n, dtype=np.int64)
    blok = max(1, (1 << 22) // max(nt, 1))
    for b in range(0, n, blok):
        d = np.linalg.norm(x_k[b:b + blok, None, :] - tum[None, :, :], axis=2)
        sayi[b:b + blok] = np.count_nonzero(d < destek, axis=1) - 1  # kendisi
    return {
        "n": int(n), "n_cevre": int(nt - n), "destek": float(destek),
        "komsu_ort": float(sayi.mean()),
        "komsu_medyan": float(np.median(sayi)),
        "komsu_min": int(sayi.min()),
        "komsu_p10": float(np.percentile(sayi, 10)),
        # SPH'de yogunluk toplami icin pratik alt sinir ~30-50; altinda
        # kalan parcaciklarin `rho`'su sistematik DUSUK cikar.
        "yalniz_oran": float(np.mean(sayi < 30)),
        "cok_yalniz_oran": float(np.mean(sayi < 10)),
    }
