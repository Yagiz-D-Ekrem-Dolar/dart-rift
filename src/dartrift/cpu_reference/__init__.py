"""Warp'tan BAGIMSIZ, kucuk-N FP64 CPU referans katmani (DR-RIFT-P1 §4.2).

GPU kernel'lerinin dogrulanacagi bagimsiz gercek kaynagi. NumPy disinda
hicbir seye bagimli degildir; determinizmi trivialdir (tek is parcacigi,
sabit sirali toplama).
"""

from .sph_ref import RefParams, RefState, evaluate, run_sph, step_kdk

__all__ = ["RefParams", "RefState", "evaluate", "step_kdk", "run_sph"]
