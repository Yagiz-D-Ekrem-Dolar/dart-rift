"""**Dinamik regresyon**: şok, inceltme arayüzünden geçiyor mu?

## Neden statik test yetmiyor

`test_arayuz_orani.py` ve `test_kademeli_inceltme.py` **aritmetiği**
kilitliyor: basamak oranı `8 000` mü `8` mi. Ama asıl soru dinamik —
*şok gerçekten geçiyor mu?*

Kütle parmak izi (A25, `2026-08-29`) şunu gösterdi: tek basamaklı
şemada `>%1` sıkışan `1 306` parçacığın **`1 306`'sı ince**, kaba
olan **`0`**. Şoklanan kütle `1 306 × 46,6043 = 60 865,2 kg` — ince
parçacık kütlesinin **tam katı**. Kaba bölgeye şok **hiç girmedi**.

Bu test o ölçüyü **koşarak** yapıyor: ince olmayan parçacıkların
şoklanıp şoklanmadığına bakıyor.

## Neden `gpu` işaretli

Gerçek bir çarpma koşusu gerekiyor (`~2 – 5` dakika). Aritmetik
testleri her koşuda çalışır; bu, çare değiştiğinde çalıştırılır:

    pytest tests/test_arayuz_sok_gecisi.py -m gpu
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

#: Sok kabul esigi (kesir) -- A25 ile ayni.
ESIK = 0.01
#: Kaba parcacik ayrimi: ince `s = 0,175 - 0,35 m` -> `6 - 47 kg`;
#: bir sonraki seviye `373 kg`. Esik ikisinin ARASINDA ve genis.
INCE_UST_KG = 150.0


def _kos(kademeler, *, t_end: float = 1.5e-3, device: str = "cuda:0"):
    """Sahneyi kurup `t_end`'e koş; hedefin son durumunu döndür."""
    from faz48_iki_asama import SAHNE, _cozucu, _kos, _mat, _sahne_kolu
    from sok_sinavi import sikisma

    from dartrift.setup.refine import (
        refine_scene_kademeli,
        refine_scene_local,
    )
    from dartrift.setup.scene import _build_mesh, build_scene

    kaba = build_scene(spacing=3.5, device="cpu", **_sahne_kolu(False))
    mesh = _build_mesh("icosphere", radius=SAHNE["radius"], subdiv=4)
    if len(kademeler) == 1:
        r, lam = kademeler[0]
        s = refine_scene_local(kaba, mesh, r_ince=r, lam=lam)
    else:
        s = refine_scene_kademeli(kaba, mesh, kademeler)
    sol = _cozucu(s.x, s.v, s.m, np.zeros(s.n), s.h, np.asarray(s.alpha0),
                  np.asarray(s.Y0), device, mat=_mat())
    _kos(sol, 0.0, t_end, 200000, "arayuz")
    st = sol.state_numpy()
    hedef = ~np.asarray(s.is_impactor, dtype=bool)
    m = st["m"][hedef]
    sik = sikisma(st["rho"][hedef], np.asarray(s.alpha0)[hedef])
    return {"m": m, "sikisma": sik, "soklu": sik > ESIK,
            "ince": m < INCE_UST_KG}


@pytest.mark.gpu
def test_TEK_BASAMAK_soku_arayuzden_GECIRMIYOR() -> None:
    """A25'in ölçtüğü durum — regresyon değil, **taban çizgisi**.

    Bu test *"kusur hâlâ orada"* diyor. Geçmesi beklenen davranış
    **kötü** olan; çare uygulandığında öteki test canlanır.
    """
    r = _kos([(3.0, 20.0)])
    soklu_kaba = int((r["soklu"] & ~r["ince"]).sum())
    assert soklu_kaba == 0, (
        f"tek basamakli semada {soklu_kaba} kaba parcacik soklanmis; "
        f"A25 sifir olcmustu -- ya sema ya olcut degismis")
    # ve soklanan kutle ince parcacik kutlesinin TAM KATI olmali
    n = int(r["soklu"].sum())
    assert n > 100, f"sok hic olusmamis (n={n}); duzenek bozuk"
    tek = float(np.median(r["m"][r["ince"]]))
    assert float(r["m"][r["soklu"]].sum()) == pytest.approx(n * tek, rel=1e-9)


@pytest.mark.gpu
def test_MERDIVEN_soku_arayuzden_GECIRIYOR() -> None:
    """Çarenin **dinamik** kanıtı: kaba parçacıklar da şoklanmalı.

    Statik testler basamağın `8 000 -> 8` olduğunu gösteriyor; bu,
    o değişikliğin **işe yaradığını** gösteriyor. İkisi ayrı sorular
    ve bu depoda *"ölçüt geçti ama fizik kurulmadı"* bir kez oldu
    (`λ₂` `β`'yı `%5` oynatıp geçti dedi, iç enerjiyi `450×`
    değiştirmişti).
    """
    r = _kos([(12.0, 1.25), (8.0, 2.5), (6.0, 5.0), (4.5, 10.0), (3.0, 20.0)])
    soklu_kaba = int((r["soklu"] & ~r["ince"]).sum())
    assert soklu_kaba > 0, (
        "merdiven kurulu ama sok yine yalnizca ince parcaciklarda; "
        "arayuz duzeltmesi ISLEMIYOR")
