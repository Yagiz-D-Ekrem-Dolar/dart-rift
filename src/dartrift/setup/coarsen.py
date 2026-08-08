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

__all__ = ["coarsen_to_sites", "korunum_raporu"]


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
                     is_boulder=None) -> dict:
    """İnce parçacıkları `siteler`e **korunumlu** aktar.

    Boş kalan siteler **düşürülür** — parçacığı olmayan bir siteye
    kütle uydurmak kütleyi bozardı.

    `alpha0`/`Y0` kütle-ağırlıklı ortalanır. Bunlar korunum yasasına
    **tabi değil**; yaklaşım olduğu `korunum` sözlüğünde işaretli.
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

    out["korunum"] = korunum_raporu(x, v, m, e, x_k, v_k, out["m"], e_k,
                                    sacilim)
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
    return {
        "kutle_hata": _gor(M0, M1),
        "momentum_hata": _gor_vek(P0, P1),
        "enerji_hata": _gor(E0, E1),
        # Bu KORUNMUYOR; esik degil, TANIDIR.
        "acisal_momentum_hata": _gor_vek(L0, L1),
        "ice_donen_kinetik_oran": float(sacilim.sum() / max(K0, 1e-300)),
        "kutle_giren": M0, "kutle_cikan": M1,
        "enerji_giren": E0, "enerji_cikan": E1,
    }
