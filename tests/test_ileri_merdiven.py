"""Merdivenli ileri model + şok kapısı (ADR-0049).

`ileri_kosu` ve `ileri_kosu_ikiasama` şokun hiç oluşmadığı ya da
aktarımda silindiği rejimlerde koşuyordu (A22 – A25). Ensemble'ın
anlamlı olabilmesi için ileri modelin **merdivenli** sürümü gerekli.

Ve ADR-0049: şok kurulmayan nokta `nan` döner, vekil onu **görmez**.
Sessizce zayıf bir noktayı veri saymaktansa eksik saymak doğru.
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from dartrift.observables.sok import (
    GECME_KESRI,
    hugoniot_bandi,
    sikisma_max,
    sok_gecti,
)

# ------------------------------------------------------- SOK KAPISI

def test_band_DART_hizinda_literatur_mertebesinde() -> None:
    alt, ust = hugoniot_bandi(6144.9)
    assert alt == pytest.approx(45.6, abs=0.2)
    assert ust == pytest.approx(74.3, abs=0.2)


def test_sikisma_alpha0_ile_KESIN() -> None:
    a0 = np.array([1.7564, 1.05])
    rho = np.array([2700.0 / 1.7564 * 1.5, 2700.0 / 1.05 * 1.2])
    assert sikisma_max(rho, a0) == pytest.approx(50.0, abs=1e-3)


def test_kapi_OLCULEN_degerleri_dogru_ayiriyor() -> None:
    """Eşik, A23'ün iki ölçümünün **arasında** ve ikisine de uzak.

    | `λ₂` | sıkışma | beklenen |
    |---|---|---|
    | `8` | `%1,68` | **düşer** |
    | `20` | `%22,0` | **geçer** |
    | merdiven | `%45,18` | geçer |
    """
    a0 = np.array([1.7564])
    taban = 2700.0 / 1.7564
    for sik, bek in ((0.0168, False), (0.2200, True), (0.4518, True)):
        assert sok_gecti(np.array([taban * (1 + sik)]), a0) is bek, sik


def test_kapi_esigi_iki_olcumun_ARASINDA() -> None:
    alt, _ = hugoniot_bandi()
    esik = GECME_KESRI * alt
    assert 1.68 < esik < 22.0, esik


def test_kapi_bozuk_girdiyi_REDDEDIYOR() -> None:
    with pytest.raises(ValueError, match="ayni olmali"):
        sikisma_max(np.ones(3), np.ones(2))
    with pytest.raises(ValueError, match="alpha0 pozitif"):
        sikisma_max(np.ones(2), np.zeros(2))


# ------------------------------------------------- ILERI MODEL YAPISI

def test_ileri_merdiven_VAR_ve_kademeleri_aliyor() -> None:
    from dartrift.inference.forward import ileri_kosu_merdiven
    s = inspect.signature(ileri_kosu_merdiven)
    for ad in ("kademeler", "spacing", "t_end", "sok_yargisi"):
        assert ad in s.parameters, ad
    assert s.parameters["sok_yargisi"].default is True


def test_ileri_merdiven_SESSIZ_KISALMAYI_reddediyor() -> None:
    """A20: adım sınırına takılan koşu tam koşmuş gibi kaydedilirse
    vekil **yanlış veriyle** eğitilir ve bunu anlayamaz."""
    from dartrift.inference.forward import ileri_kosu_merdiven
    k = inspect.getsource(ileri_kosu_merdiven)
    assert "ADIM SINIRINA TAKILDI" in k
    assert "raise RuntimeError" in k


def test_ileri_merdiven_SOK_KAPISINI_uyguluyor() -> None:
    from dartrift.inference.forward import ileri_kosu_merdiven
    k = inspect.getsource(ileri_kosu_merdiven)
    assert "sok_gecti" in k
    assert "ADR-0049" in k


def test_ileri_merdiven_AKTARIM_kullanmiyor() -> None:
    """Tek aşamalı: `ρ` hiçbir yerde sıfırlanmıyor (A24)."""
    from dartrift.inference.forward import ileri_kosu_merdiven
    k = inspect.getsource(ileri_kosu_merdiven)
    assert "asama2" not in k and "two_stage" not in k
    assert "refine_scene_kademeli" in k


# ------------------------------------------------- ENSEMBLE SURUCUSU

def test_ensemble_surucusu_MERDIVENI_kullaniyor() -> None:
    """Sürücü eski (şoksuz) ileri modele düşerse ensemble yine boş çıkar."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m
    k = inspect.getsource(m.main)
    assert "ileri_kosu_merdiven(" in k
    assert "kademeler=MERDIVEN" in k
    assert m.MERDIVEN == ("48:2.8", "24:1.4", "12:0.7", "6:0.35", "3:0.175")


def test_ensemble_surucusu_SOK_KAPISI_varsayilan_ACIK() -> None:
    """Kapıyı kapatmak tanı içindir; varsayılan olmamalı (ADR-0049)."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m
    k = inspect.getsource(m.main)
    assert '"--sok-kapisi-kapali", action="store_true"' in k
    assert "sok_yargisi=not a.sok_kapisi_kapali" in k


def test_ensemble_surucusu_EnsembleDurum_alanlarini_dogru_okuyor() -> None:
    """Yanlış alan adı `AttributeError` ile koşunun **sonunda** patlar —
    yani bütün GPU işi bittikten sonra. Burada erken yakalanıyor."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m

    from dartrift.inference.ensemble import EnsembleDurum
    alanlar = set(EnsembleDurum.__dataclass_fields__)
    k = inspect.getsource(m.main)
    for ad in ("tamamlanan", "toplam", "dusen", "atlanan", "bozuk_satir"):
        assert ad in alanlar, ad
        assert f"durum.{ad}" in k, ad
    # VARLIK YETMIYOR -- YOKLUK da sinanmali (rapor A33).
    # Onceki surum yalnizca `durum.tamamlanan` VAR mi diye bakiyordu;
    # `durum.n_tamam` de kaynakta DURUYORDU ve test GECIYORDU. TRUBA'da
    # kosu 15 saat surup ozet satirinda AttributeError ile dustu.
    import re
    kullanilan = set(re.findall(r"durum\.(\w+)", k))
    yabanci = kullanilan - alanlar
    assert not yabanci, (
        f"EnsembleDurum'da olmayan alan(lar) kullaniliyor: {yabanci}; "
        f"gecerli alanlar: {sorted(alanlar)}")


# ------------------------------------------- DILIM (A31: 6 kat israf)

def test_dilim_ORTUSMESIZ_ve_TAM_kapsiyor() -> None:
    """`K5` altı görevle koştu, `30` satır yazdı, **`5`** benzersiz nokta.

    `ensemble_kos` tamamlananları başlangıçta **bir kez** okuyor;
    altı görev aynı anda başlayıp boş dosya gördü. `108` GPU-saat
    harcanıp `18` saatlik iş elde edildi — **`%83` israf**.
    """
    tam, n_s = 24, 6
    kaplama: set[int] = set()
    for i in range(n_s):
        s = set(np.where(np.arange(tam) % n_s == i)[0].tolist())
        assert not (s & kaplama), f"gorev {i} ORTUSUYOR"
        assert len(s) == tam // n_s
        kaplama |= s
    assert kaplama == set(range(tam)), "kapsama EKSIK"


def test_surucu_DILIM_bayragini_tasiyor() -> None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m
    k = inspect.getsource(m.main)
    assert '"--dilim"' in k
    assert "np.arange(tam_n) % n_s == i_s" in k


def test_surucu_dilimde_AYRI_dosyaya_yaziyor() -> None:
    """Aynı dosyaya eşzamanlı ekleme satır bozabilir — A31'in ikinci yüzü."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m
    k = inspect.getsource(m.main)
    assert 'yol.with_suffix(f".dilim' in k
    assert "ensemble_kos(tasarim, _ileri, yol" in k


def test_surucu_bozuk_dilimi_REDDEDIYOR() -> None:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m
    k = inspect.getsource(m.main)
    assert "0 <= i < n olmali" in k
    assert "dilim {a.dilim} bos" in k


# ----------------------------------- PROTOKOL v2: iki tarafli kapi

def test_v2_ASIRI_sikismayi_ISARETLIYOR_ama_IPTAL_ETMIYOR() -> None:
    """v1 yalnızca alt sınıra bakıyordu (A35); v2 üst sınırı **işaretliyor**.

    İlk v2 taslağı bunu **sert kapı** yapmıştı ve o yanlıştı:
    `%74,3` bandın üst kenarı `up = v/2`'den geliyor ve bu **aynı
    malzeme/empedanstaki simetrik düzlemsel** çarpma için doğru.
    DART'ta mermi alüminyum, hedef gözenekli bazalt — arayüz hızı
    **empedans eşleşmesiyle** belirlenir.

    Gerçek bir üst tavan ancak EOS/Hugoniot ve çarpma empedans
    probleminden **türetilirse** sert kapıya dönüşür. O türetim
    yapılana kadar bu yalnızca **şüphe işareti**.
    """
    from dartrift.observables.sok import sok_gecti, sok_yargisi_ayrintili
    a0 = np.array([1.7564])
    taban = 2700.0 / 1.7564
    r = sok_yargisi_ayrintili(np.array([taban * (1 + 1.20)]), a0)
    assert r["yargi"] == "SOK_ASIRI_ADAY"
    assert r["asiri_suphe"] is True
    assert r["gecti"] is True, "tani bayragi sonucu IPTAL ETMEMELI"
    assert sok_gecti(np.array([taban * (1 + 1.20)]), a0)


def test_v2_ust_payi_bandi_KESIN_saymiyor() -> None:
    """`%74,3` bir **sezgisel** üst kenar; `up = v/2` yalnızca aynı
    malzeme/empedanstaki simetrik düzlemsel çarpma için doğru.

    DART'ta mermi alüminyum, hedef gözenekli bazalt — arayüz hızı
    empedans eşleşmesiyle belirlenir. Pay o belirsizliği kapıya
    yazıyor, bu yüzden `%75,65` **elenmiyor**.
    """
    from dartrift.observables.sok import UST_PAY, sok_yargisi_ayrintili
    a0 = np.array([1.7564])
    taban = 2700.0 / 1.7564
    r = sok_yargisi_ayrintili(np.array([taban * (1 + 0.7565)]), a0)
    assert r["yargi"] == "SOK_VAR" and r["gecti"]
    assert not r["asiri_suphe"], "dusuk AV kolu supheli bile isaretlenmemeli"
    assert UST_PAY > 1.0, "pay 1,0 olsaydi sezgisel band KESIN sayilirdi"


def test_v2_alt_sinir_DEGISMEDI() -> None:
    """v1 -> v2 yalnızca **üst** sınır ekledi; alt eşik aynı kalmalı."""
    from dartrift.observables.sok import GECME_KESRI, sok_yargisi_ayrintili
    a0 = np.array([1.7564])
    taban = 2700.0 / 1.7564
    assert sok_yargisi_ayrintili(
        np.array([taban * 1.0168]), a0)["yargi"] == "SOK_YOK"   # lam2=8
    assert sok_yargisi_ayrintili(
        np.array([taban * 1.2200]), a0)["gecti"]                # lam2=20
    assert GECME_KESRI == 0.1


def test_ileri_model_NPZ_kaydediyor() -> None:
    """`L1`'in `β`'ları kullanılamadı çünkü durum kaydı yoktu (A37).

    Defter post-hoc uygulanamadı, parçacık kimliği karşılaştırılamadı.
    """
    from dartrift.inference.forward import ileri_kosu_merdiven
    s = inspect.signature(ileri_kosu_merdiven)
    assert "durum_dizini" in s.parameters
    k = inspect.getsource(ileri_kosu_merdiven)
    assert "savez_compressed" in k
    assert "mermi_kesri" in k          # provenance kaydediliyor


# ----------------------------- A40: 'dosya var' != 'gecerli veri var'

def test_devam_SURUMU_uysmayan_satiri_ATLIYOR() -> None:
    """`L1` `47` saniyede `COMPLETED` dönüp **hiçbir şey koşmadı**.

    Devam mantığı önceki satırları gördü ve hepsini atladı — ama o
    satırlar **iki gün eski kodla** ve provenance kaydı olmadan
    üretilmişti. Geçerlilik: `var ∧ doğru tohum ∧ doğru şema ∧
    **doğru sürüm**`.
    """
    import json
    import tempfile
    from pathlib import Path as _P

    from dartrift.inference.ensemble import oku_tamamlananlar
    yol = _P(tempfile.mkdtemp()) / "e.jsonl"
    yol.write_text("\n".join(json.dumps(r) for r in [
        {"i": 0, "y": [1.0], "root_seed": 7, "surum": "eski"},
        {"i": 1, "y": [2.0], "root_seed": 7, "surum": "yeni"},
    ]) + "\n", encoding="utf-8")
    assert sorted(oku_tamamlananlar(yol, 7, "yeni")[0]) == [1]
    assert sorted(oku_tamamlananlar(yol, 7, "eski")[0]) == [0]
    # surum verilmezse eski davranis (geriye uyum)
    assert sorted(oku_tamamlananlar(yol, 7)[0]) == [0, 1]


def test_ensemble_kos_SURUMU_satira_yaziyor() -> None:
    """Sürüm yazılmazsa sonraki koşu doğrulayamaz."""
    import inspect

    from dartrift.inference import ensemble
    k = inspect.getsource(ensemble.ensemble_kos)
    assert '"surum": surum' in k
    assert "oku_tamamlananlar(yol, root_seed, surum)" in k


def test_surucu_KOD_SURUMUNU_gecirıyor() -> None:
    import inspect
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
    import faz5_ensemble_merdiven as m
    k = inspect.getsource(m.main)
    assert "rev-parse" in k and "surum=surum" in k
