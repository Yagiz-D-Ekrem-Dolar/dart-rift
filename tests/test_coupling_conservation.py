"""C-2 ölçüm aracının kendi denetimi (küçük kafes, hızlı).

Ölçülen büyüklük **momentum kaymasıdır**; aracın kendisi momentumu yanlış
hesaplarsa C hakkındaki yargı tamamen çürür.
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.validation.coupling_conservation import RHO, measure_coupling_conservation, net_force

S, HOS = 1.0, 1.3


def _kafes(spacing: float, half: float) -> np.ndarray:
    n = int(np.floor(half / spacing))
    e = np.arange(-n, n + 1) * spacing
    xx, yy, zz = np.meshgrid(e, e, e, indexing="ij")
    return np.column_stack([xx.ravel(), yy.ravel(), zz.ravel()])


def test_tum_parcaciklarda_net_kuvvet_tam_sifir() -> None:
    """Antisimetri: `Σ_tüm m_i a_i = 0` — **tam**.

    Bu ölçümün değil, kuvvet biçiminin sınavıdır; bozuksa hiçbir kayma
    sayısı yorumlanamaz.
    """
    x = _kafes(S, 4.0)
    m = np.full(len(x), RHO * S ** 3)
    P = 1.0e8 * x[:, 0]                       # DOGRUSAL rampa
    net = net_force(x, m, P, HOS * S)
    olcek = float(np.sum(m) * 1.0e8 / RHO)
    assert float(np.linalg.norm(net)) / olcek < 1.0e-14, net


def test_alt_kumede_net_kuvvet_sifirdan_FARKLI() -> None:
    """KALİBRASYON: bir alt küme için toplam sıfır **olmamalı**.

    Olsaydı ölçüm hiçbir şey ayırt edemez ve eşleme kayması da önemsiz
    olarak sıfır çıkardı.
    """
    x = _kafes(S, 4.0)
    m = np.full(len(x), RHO * S ** 3)
    P = 1.0e8 * x[:, 0]
    alt = x[:, 0] > 0.0
    net = net_force(x, m, P, HOS * S, alt)
    olcek = float(np.sum(m[alt]) * 1.0e8 / RHO)
    assert float(np.linalg.norm(net)) / olcek > 1.0e-3, net


def test_duzgun_basincta_IC_bolgede_kuvvet_sifir() -> None:
    """Düzgün alanda kuvvet **yalnızca iç bölgede** sıfırdır.

    İlk yazdığım test `x > 0` alt kümesini kullanıyordu ve düştü. **Ölçtüm:**

    ```
    x>0 (kenar dahil)  n=324  |net|/olcek = 2,8821e-01
    IC bolge (pay 2h)  n= 27  |net|/olcek = 1,2539e-16
    ```

    Kenar parçacıklarının komşuluğu **kesiktir**; oradaki dengesizlik düzgün
    alanla ilgili değil, kafesin bitmesiyle ilgilidir (D1 kuralı). Bu, düzgün
    alanın neden **boş bir sınav** olduğunun da kanıtıdır — C-2'de doğrusal
    rampa tam bu yüzden seçildi.
    """
    x = _kafes(S, 4.0)
    m = np.full(len(x), RHO * S ** 3)
    P = np.full(len(x), 5.0e8)                # DUZGUN
    h = HOS * S
    ic = np.all(np.abs(x) < 4.0 - 2.0 * h, axis=1)
    assert int(ic.sum()) > 20, int(ic.sum())
    net = net_force(x, m, P, h, ic)
    olcek = float(np.sum(m[ic]) * 5.0e8 / (RHO * h))
    assert float(np.linalg.norm(net)) / olcek < 1.0e-12, net

    # BOSLUK KONTROLU: kenar DAHIL edilirse GERCEKTEN bozulmali, yoksa
    # yukaridaki "ic bolge" kosulu bir sey korumuyor demektir.
    kenar = x[:, 0] > 0.0
    net_k = net_force(x, m, P, h, kenar)
    olcek_k = float(np.sum(m[kenar]) * 5.0e8 / (RHO * h))
    assert float(np.linalg.norm(net_k)) / olcek_k > 1.0e-2, net_k


def test_ortusme_sigmazsa_hata() -> None:
    with pytest.raises(ValueError, match="örtüşme sığmıyor"):
        measure_coupling_conservation(lam=2.0, half=6.0, r_split=2.5)


def test_tek_parca_kolu_makine_sifiri() -> None:
    """BOŞLUK KONTROLÜ: araç kalibre mi?"""
    r = measure_coupling_conservation(lam=2.0, half=7.0, r_split=4.0)
    assert r["monolithic_is_exact"] is True, r["monolithic_net_rel"]


def test_bolgeler_dolu() -> None:
    r = measure_coupling_conservation(lam=2.0, half=7.0, r_split=4.0)
    assert r["n_A_real"] > 20 and r["n_B_real"] > 20, r
    # Hayaletler GERCEKTEN var olmali: ortusme bandi bos olsaydi esleme
    # kaymasi tanim geregi sifir cikardi.
    assert r["n_A_total"] > r["n_A_real"], r
    assert r["n_B_total"] > r["n_B_real"], r
