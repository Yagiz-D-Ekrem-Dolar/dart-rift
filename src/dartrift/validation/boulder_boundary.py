"""ADR-0043 #4 — blok sınırlarının kaba kalmasının **geometrik** hatası.

`refine_scene_local` ince bölgenin `α₀`/`Y₀`/`is_boulder` değerlerini
**en yakın kaba parçacıktan** örnekliyor. Blok sınırları böylece ince
kafeste değil, **kaba** kafesin çözünürlüğünde temsil ediliyor.

`f_boulder` çıkarımın üç parametresinden biri ve ince bölge tam olarak
`β`'nın üretildiği yer — yani bu hata doğrudan ürüne gidiyor.

## Neden ayrı bir `judge`

Ölçümün **dejenere** olabildiği bir durum var ve sessizce *"hata yok"*
diye okunuyordu: ince bölgede **hiç blok yoksa** `f_kesin = f_kullanılan
= 0` ve göreli sapma `0/0`. İlk sürümüm bunu `%0,000` diye yazdı ve bir
an geçmiş gibi göründü.

> Ölçülemeyen bir şeye `0` demek, `nan` demekten **daha kötüdür**:
> `nan` görünür, `0` başarı gibi okunur.
"""
from __future__ import annotations

import numpy as np

__all__ = ["blok_sapmasi", "judge"]

#: `f_boulder` sapması bu oranı aşarsa yaklaşım çıkarımı bozacak
#: sayılır. `DART_UZAYI`'nın `f_boulder` aralığına göre **ölçümden önce**
#: yazıldı; bkz. `docs/G4-OLCUTLERI.md` disiplini.
F_BLOK_SAPMA_ESIGI = 0.10


def blok_sapmasi(m, kesin_blok, kullanilan_blok) -> dict:
    """Kütle-ağırlıklı blok kesri: **kesin** vs **kullanılan**.

    `kesin_blok` `assign_material`ın ince kafes noktalarında doğrudan
    hesapladığı üyelik; `kullanilan_blok` en yakın kaba parçacıktan
    örneklenen. Fark, yaklaşımın hatasıdır.
    """
    m = np.asarray(m, dtype=np.float64)
    kb = np.asarray(kesin_blok, dtype=bool)
    ub = np.asarray(kullanilan_blok, dtype=bool)
    if not (len(m) == len(kb) == len(ub)):
        raise ValueError(f"uzunluklar uyuşmuyor: m={len(m)} "
                         f"kesin={len(kb)} kullanilan={len(ub)}")
    if len(m) == 0:
        raise ValueError("ince bölgede parçacık yok")
    if np.any(m <= 0.0):
        raise ValueError("kütleler pozitif olmalı")

    mt = float(m.sum())
    f_kes = float(m[kb].sum() / mt)
    f_kul = float(m[ub].sum() / mt)
    yanlis = kb != ub
    # DEJENERE: bolgede hic blok yoksa olculecek SINIR yoktur.
    blok_var = bool(kb.any() or ub.any())
    return {
        "blok_var": blok_var,
        "durum": "olculdu" if blok_var else "belirsiz",
        "neden": "" if blok_var else "ince bölgede hiç blok yok — "
                                     "ölçülecek sınır yok",
        "f_blok_kesin": f_kes,
        "f_blok_kullanilan": f_kul,
        # Bolunme YOK: f_kes = 0 iken oran tanimsiz, `nan` dogru cevap.
        "f_blok_sapma": (abs(f_kul - f_kes) / f_kes if f_kes > 0.0
                         else float("nan")),
        "yanlis_oran": float(yanlis.mean()),
        "yanlis_kutle_oran": float(m[yanlis].sum() / mt),
        "n": int(len(m)),
    }


def judge(kayitlar, esik: float = F_BLOK_SAPMA_ESIGI) -> dict:
    """Kollardan **en kötüsüne** göre karar.

    Dejenere kollar **atılır**, sayılmaz. Hiç ölçülebilir kol yoksa
    sonuç `belirsiz` — `gecti = False` **değil**, çünkü bu bir başarısızlık
    değil, ölçüm yokluğudur (RULES.txt).
    """
    kayitlar = list(kayitlar)
    olculen = [k for k in kayitlar if k.get("durum") == "olculdu"]
    if not olculen:
        return {"durum": "belirsiz", "gecti": None,
                "neden": f"{len(kayitlar)} kolun hiçbirinde blok yok — "
                         f"kayıt bulunamadı",
                "n_kol": len(kayitlar), "n_olculen": 0}
    en_kotu = max(olculen, key=lambda k: k["f_blok_sapma"])
    return {
        "durum": "olculdu",
        "gecti": bool(en_kotu["f_blok_sapma"] < esik),
        "esik": float(esik),
        "en_kotu_sapma": float(en_kotu["f_blok_sapma"]),
        "en_kotu_yanlis_oran": float(en_kotu["yanlis_oran"]),
        "n_kol": len(kayitlar), "n_olculen": len(olculen),
        "n_dejenere": len(kayitlar) - len(olculen),
    }
