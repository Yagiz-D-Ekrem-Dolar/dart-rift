"""Sentetik kurtarma ve parametre çıkarımı (FAZ 4.6 — G4-C).

İleri model **pahalıdır** (her koşu bir GPU benzetimi), dolayısıyla
doğrudan MCMC yapılamaz. Mimari standarttır ve üç katmanlıdır:

```
deney tasarımı  →  vekil (emülatör)  →  posterior
   design.py         surrogate.py        posterior.py
```

`recovery.py` bu üçünü G4-C ölçütlerine bağlar.

## Neden GPU olmadan da yazılabilir

Çıkarım katmanının **kendisi** ileri modelden bağımsızdır. Bilinen
analitik bir haritayla sınanabilir: *"gerçek parametreler geri
buluniyor mu?"* Bu bir **boşluk kontrolüdür** ve GPU koşuları
harcanmadan **önce** yapılmalıdır — makine bozuksa pahalı koşular boşa
gider.

> TRUBA kotası doldu (`7.200.096 / 7.200.000 cpu-dk`), yani gerçek ileri
> koşular şu an yapılamıyor. Bu katman o yüzden **analitik haritaya
> karşı** doğrulanıyor; gerçek koşular geldiğinde yalnızca `design`'ın
> çıktısı beslenecek.
"""
from .design import ParamSpace, factorial_design, lhs_design
from .posterior import GridPosterior, grid_posterior
from .recovery import G4C, recovery_verdict
from .surrogate import Surrogate, fit_surrogate

__all__ = ["ParamSpace", "factorial_design", "lhs_design",
           "Surrogate", "fit_surrogate",
           "GridPosterior", "grid_posterior",
           "G4C", "recovery_verdict"]
