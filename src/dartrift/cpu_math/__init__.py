"""NumPy tabanli CPU vektor matematigi — referans katmaninin temeli.

FAZ 1'deki Warp kernel'leri bu referans uygulamalara karsi dogrulanacaktir.
Deterministik indirgemeler (sabit-sirali Kahan toplami) burada tanimlanir.
"""

from .reductions import fixed_order_sum, kahan_sum
from .vector import cross3, dot3, norm3, normalize3

__all__ = [
    "dot3",
    "cross3",
    "norm3",
    "normalize3",
    "kahan_sum",
    "fixed_order_sum",
]
