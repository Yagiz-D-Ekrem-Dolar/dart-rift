"""Patlama tanısı — koşu `nan`'a gittiğinde **ilk bozulan** parçacıkları yakala.

## Neden (rapor A80)

Protokol M'nin `kaba t5` noktası (`α_b = 1,15`, `Y₀ = 1e4 Pa`, `f = 0,45`,
sahne `20260906`) üretim yapılandırmasında *"kosu PATLADI adim 16000,
t = nan"* ile düştü. `ileri_kosu_merdiven` sonluluğu `azami_adim // 200 =
2000` adımda bir sınıyor: patlamanın **ne zaman** ve **nerede** başladığı
kayıp. Aynı yapılandırma N/N2/No'da 144 noktada koşuyor; kaynağı
bilinmeyen bir patlama posterioru sessizce seyreltir (P, `%90` sonlu
kesir eşiği).

## Ne yapar

`ileri_kosu_merdiven(..., adim_gozlemcisi=PatlamaGozlemcisi(dizin))`.
Her `her` adımda alanlar okunur; sonluysa bir **halka tampona** (son
`halka` anlık görüntü) konur. İlk sonlu olmayan görüntüde:

- bozulan parçacıklar (hangi alan, kaç tane, mermi mi, konum, `h`),
- onların tampondaki **zaman serisi** (`ρ, u, P, c_s, α, |S|, |v|, h`),
- küresel özet serisi (`min ρ`, `max |v|`, `min c_s²`, `dt`),
- son iyi ve ilk bozuk tam durum (`npz`)

yazılır ve koşu `RuntimeError` ile durdurulur. Fiziğe **dokunmaz**:
gözlemci yalnız okur.
"""
from __future__ import annotations

import json
from collections import deque
from pathlib import Path

import numpy as np

__all__ = ["PatlamaGozlemcisi", "PatlamaYakalandi"]

ALANLAR = ("x", "v", "u", "rho", "P", "cs", "alpha", "S", "h")


class PatlamaYakalandi(RuntimeError):
    """Tanı yazıldıktan sonra koşuyu durduran hata."""


def _oku(sol) -> dict:
    s = sol.state_numpy()
    return {k: np.array(s[k], copy=True) for k in ALANLAR}


def _sonlu_degil(g: dict) -> np.ndarray:
    kotu = np.zeros(len(g["rho"]), bool)
    for k in ALANLAR:
        a = g[k].reshape(len(kotu), -1)
        kotu |= ~np.all(np.isfinite(a), axis=1)
    return kotu


def _ozet(g: dict, adim: int, t: float, dt: float) -> dict:
    v = np.linalg.norm(g["v"], axis=1)
    return {"adim": int(adim), "t": float(t), "dt": float(dt),
            "rho_min": float(np.nanmin(g["rho"])),
            "v_max": float(np.nanmax(v)),
            "cs2_min": float(np.nanmin(g["cs"] ** 2)),
            "P_min": float(np.nanmin(g["P"])), "P_max": float(np.nanmax(g["P"])),
            "u_min": float(np.nanmin(g["u"])),
            "alpha_min": float(np.nanmin(g["alpha"])),
            "h_min": float(np.nanmin(g["h"])), "h_max": float(np.nanmax(g["h"]))}


class PatlamaGozlemcisi:
    def __init__(self, dizin, *, her: int = 25, halka: int = 8,
                 en_cok_parcacik: int = 40, mermi_maske=None, merkez=None):
        self.dizin = Path(dizin)
        self.her = int(her)
        self.tampon: deque = deque(maxlen=int(halka))
        self.ozetler: deque = deque(maxlen=400)
        self.en_cok = int(en_cok_parcacik)
        self.mermi = None if mermi_maske is None else np.asarray(mermi_maske, bool)
        self.merkez = None if merkez is None else np.asarray(merkez, float)
        self._son_dt = float("nan")

    def __call__(self, adim: int, t: float, dt: float, sol) -> None:
        self._son_dt = float(dt)
        if adim % self.her:
            return
        g = _oku(sol)
        kotu = _sonlu_degil(g)
        if not kotu.any():
            self.tampon.append((adim, t, dt, g))
            self.ozetler.append(_ozet(g, adim, t, dt))
            return
        self._yaz(adim, t, dt, g, kotu)
        raise PatlamaYakalandi(
            f"PATLAMA TANISI: adim {adim}, t = {t:.6e}, {int(kotu.sum())} "
            f"parcacik sonlu degil -> {self.dizin}")

    def _yaz(self, adim, t, dt, g, kotu) -> None:
        self.dizin.mkdir(parents=True, exist_ok=True)
        idx = np.flatnonzero(kotu)
        # Ilk bozulanlari sirala: son iyi anlik goruntude EN UC degerleri
        # tasiyanlar (en kucuk rho, en buyuk |v|) once.
        seri = {}
        if self.tampon:
            _, _, _, son = self.tampon[-1]
            anahtar = np.nan_to_num(son["rho"][idx], nan=np.inf)
            idx = idx[np.argsort(anahtar)]
        sec = idx[: self.en_cok]
        for i in sec:
            satirlar = []
            for (a, ta, dta, s) in self.tampon:
                satirlar.append({
                    "adim": int(a), "t": float(ta), "dt": float(dta),
                    "rho": float(s["rho"][i]), "u": float(s["u"][i]),
                    "P": float(s["P"][i]), "cs": float(s["cs"][i]),
                    "alpha": float(s["alpha"][i]),
                    "S_norm": float(np.linalg.norm(s["S"].reshape(len(s["rho"]), -1)[i])),
                    "v": float(np.linalg.norm(s["v"][i])), "h": float(s["h"][i]),
                    "x": s["x"][i].tolist()})
            seri[int(i)] = satirlar
        hangi = {k: int(np.count_nonzero(~np.all(np.isfinite(
            g[k].reshape(len(kotu), -1)), axis=1))) for k in ALANLAR}
        tani = {
            "adim": int(adim), "t": float(t), "dt": float(dt),
            "n_sonlu_degil": int(kotu.sum()), "alan_basina": hangi,
            "mermi_kesri_bozuk": (float(self.mermi[kotu].mean())
                                  if self.mermi is not None else None),
            "bozuk_konum_ozeti": _konum_ozeti(g, kotu, self.tampon, self.merkez),
            "ilk_bozulanlar": seri,
            "kuresel_seri": list(self.ozetler),
        }
        (self.dizin / "patlama_tani.json").write_text(
            json.dumps(tani, indent=1, default=float), encoding="utf-8")
        if self.tampon:
            a, ta, dta, s = self.tampon[-1]
            np.savez_compressed(self.dizin / "patlama_son_iyi.npz", adim=a, t=ta,
                                dt=dta, **s)
        np.savez_compressed(self.dizin / "patlama_ilk_bozuk.npz", adim=adim, t=t,
                            dt=dt, kotu=kotu, **g)


def _konum_ozeti(g, kotu, tampon, merkez) -> dict:
    if not tampon:
        return {}
    _, _, _, son = tampon[-1]
    x = son["x"][kotu]
    out = {"x_ort": x.mean(axis=0).tolist(), "x_min": x.min(axis=0).tolist(),
           "x_max": x.max(axis=0).tolist()}
    if merkez is not None:
        r = np.linalg.norm(x - merkez[None, :], axis=1)
        out.update(r_min=float(r.min()), r_max=float(r.max()))
    return out
