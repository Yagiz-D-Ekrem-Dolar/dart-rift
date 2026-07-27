"""Warp GPU SPH cekirdegi (DR-RIFT-P1).

Fizik kernel'lerinin ICI ogrenci-yazimidir; Warp yalnizca GPU derlemesi ve
hash-grid ilkelini saglar (Ana Plan Karar 2 ve Karar 5). Tum fizik FP64'tur
(bilim modu). Kernel cagri sirasi DR-RIFT-P1 §4.1'deki sozlesmeyi izler:

    build_hash_grid -> density -> eos -> (divcurl/balsara) -> forces
    -> integrate_KDK -> timestep -> invariants -> output
"""
