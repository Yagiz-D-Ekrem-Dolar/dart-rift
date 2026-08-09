"""Bir ensemble koşusu **yeterince uzun** mu — koşmadan **önce**.

## Korunan hata sınıfı

Erken kesilmiş bir koşu `β`'yı **sistematik olarak** küçük verir ve
**bütün** tasarım noktalarını **aynı yönde** kaydırır. Bunun sinsi
yanı, hiçbir olağan tanının onu görmemesi:

| tanı | kısa koşuda ne der |
|---|---|
| vekil `q2` | **yüksek** — yüzey hâlâ düzgün, sadece kaymış |
| `sabit` | **hayır** — `β` değişiyor, sadece yanlış değerde |
| korunum | **tam** — hiçbir şey kaybolmuyor |
| G4-C `C1` | gerçeği **kaçırabilir** ama nedenini söylemez |

Sonuç: **dar ama yanlış** bir posterior. ADR-0011 §3'ün dersi tam
buydu.

## Neden koşudan **önce**

`~3` saatlik GPU'yu harcayıp sonucun geçersiz olduğunu görmek pahalı.
Kontrol ucuz: FAZ 4.5 zaten durulma zamanını **ölçtü**.

## Adım→zaman oranı **tahmin edilmiyor**

`dt`, `h`'ye ve dolayısıyla sahneye bağlı. FAZ 4.5 **aynı** sahneyi
koştuğu için oran onun kendi çıktısından okunuyor
(`t_sim_end / steps_done`).

> Kontrol yapılamadığında sonuç `denetlenmedi`'dir — `yeterli` **değil**.
> Bilinmeyeni geçmiş saymak, kapının `koşulmadı`yı geçmiş saymamasıyla
> aynı ilke.
"""
from __future__ import annotations

import math

__all__ = ["sure_denetimi", "DURUM"]

#: Olası sonuçlar. `yeterli` dışındaki her şey koşuyu **durdurmalı**
#: ya da açıkça işaretlenmelidir.
DURUM = ("yeterli", "kisa", "denetlenemedi")


def sure_denetimi(faz45: dict | None, steps: int) -> dict:
    """`steps` adım, FAZ 4.5'in ölçtüğü durulmaya yetiyor mu?

    Parameters
    ----------
    faz45
        FAZ 4.5 çıktı sözlüğü. `None` ise denetim **yapılamaz**.
    steps
        Planlanan adım sayısı.

    Returns
    -------
    `durum` ∈ :data:`DURUM`, `kisa_kosu` (bool | None) ve gerekçe.
    `kisa` durumunda `onerilen_steps` de döner.
    """
    if steps <= 0:
        raise ValueError(f"steps pozitif olmalı, {steps} geldi")

    out: dict = {"durum": "denetlenemedi", "kisa_kosu": None,
                 "steps": int(steps), "neden": ""}
    if not faz45:
        out["neden"] = "FAZ 4.5 çıktısı verilmedi"
        return out

    tani = faz45.get("beta_bound_settling_diag") or {}
    if tani.get("sabit"):
        out["sabit_seri"] = True
        out["neden"] = ("FAZ 4.5'te `β_bound` baştan sona SABİT — durulma "
                        "zamanı anlamlı değil")
        return out
    out["sabit_seri"] = False

    t_dur = faz45.get("beta_bound_settling_time_s")
    if t_dur is None or not math.isfinite(float(t_dur)):
        out["neden"] = "FAZ 4.5 durulmadı — karşılaştırılacak zaman yok"
        return out
    t_dur = float(t_dur)
    out["t_durulma_s"] = t_dur

    t_son, adim_son = faz45.get("t_sim_end"), faz45.get("steps_done")
    if not t_son or not adim_son:
        out["neden"] = "FAZ 4.5 çıktısında `t_sim_end`/`steps_done` yok"
        return out
    # `dt` tahmin EDILMIYOR: ayni sahnenin olculmus ortalamasi.
    dt_ort = float(t_son) / float(adim_son)
    if not math.isfinite(dt_ort) or dt_ort <= 0.0:
        out["neden"] = f"geçersiz adım→zaman oranı: {dt_ort}"
        return out

    t_kestirim = dt_ort * steps
    out["dt_ort_s"] = dt_ort
    out["t_kestirim_s"] = t_kestirim
    out["kisa_kosu"] = bool(t_kestirim < t_dur)
    if out["kisa_kosu"]:
        out["durum"] = "kisa"
        out["onerilen_steps"] = int(math.ceil(t_dur / dt_ort))
        out["neden"] = (f"koşu durulmadan bitiyor "
                        f"({t_kestirim:.4g} s < {t_dur:.4g} s); "
                        f"`--steps {out['onerilen_steps']}` gerekir")
    else:
        out["durum"] = "yeterli"
        out["neden"] = (f"{t_kestirim:.4g} s ≥ durulma {t_dur:.4g} s")
    return out
