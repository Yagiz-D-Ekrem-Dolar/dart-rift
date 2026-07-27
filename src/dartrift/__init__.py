"""DART-RIFT: Dimorphos icin GPU hizlandirmali SPH sok-fizigi motoru — FAZ 0 altyapisi.

Bu paket, DR-RIFT-P0 sartnamesindeki "temel altyapi ve test iskeleti"ni uygular:
SI birim sistemi, surumlu config semasi, SoA parcacik deposu (CPU<->GPU koprusu),
deterministik RNG, invariant denetimi, yapilandirilmis loglama + kosu manifesti
ve 3 katmanli HDF5 G/C.

G0 kapisi gecilmeden hicbir DART/fizik kosusu calistirilamaz.
"""

__version__ = "0.1.0"

SCHEMA_VERSION = 1
"""Config semasinin desteklenen surumu (P0-DR-01)."""
