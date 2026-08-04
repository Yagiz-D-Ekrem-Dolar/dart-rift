"""Kenar payının **tek kaynağı**.

## Neden ayrı bir modül

Ölçüm bölgeleri serbest yüzeyden bir **pay** kadar içeride seçilir; yoksa
komşuluğu kesik parçacıklar ölçüme girer ve sonuç fizikten değil kafesin
bitmesinden gelir. KAYIT-019 §3b'de tam olarak bu oldu: pay `2,5·s` iken
taban `0,0878` görünüyordu, `4,0·s` iken `5,9e-12`.

Bu formül **dört ayrı modülde** yazılıydı (`mass_ratio`, `variable_h`,
`domain_coupling`, `coupling_conservation`). Aynı büyüklüğün birden fazla
yerde yazılması K7'nin kalıbıdır: hepsi bugün aynı, ama hiçbir şey onları
aynı tutmuyor. Çekirdek değişirse (Wendland C2 → başka bir çekirdek) destek
yarıçapı değişir ve dördü ayrı ayrı güncellenmek zorunda kalır.

## Formül

Wendland C2'nin desteği `2h`'dir. Buna yarım aralık güvenlik payı eklenir:

```
pay = SUPPORT_OVER_H · h + 0.5 · aralık
```

`SUPPORT_OVER_H` çekirdeğe özgüdür ve **tek yerde** tanımlıdır.

## `depth` parametresi — bilgi kaç komşuluk üzerinden taşınıyor?

Çoğu ölçümde bir parçacığın sonucu **kendi** komşuluğuna bağlıdır; pay bir
destek yeter (`depth = 1`).

Ama grad-h kuvveti **komşunun** `Ω_j`'sini kullanır ve `Ω_j` o komşunun
**kendi** komşuluğundan gelir; yüzeyin kestiği bilgi **bir çekirdek daha**
içeri sızar (`depth = 2`). Ölçüldü (KAYIT-024 §2): `λ = 1`'de grad-h
`7,69e-06` verirken diğer üç şema `1,86e-15` veriyordu — fark tamamen bu
sızıntıdandı.

> **Kural:** payı yazmadan önce sor — *bu parçacığın sonucu kaç adım
> komşuluk üzerinden bilgi taşıyor?* Cevap `k` ise `depth = k`.
"""
from __future__ import annotations

__all__ = ["SUPPORT_OVER_H", "support_margin", "margin_factor"]

# Wendland C2: W(q) sifirdir q >= 2 icin, yani destek yaricapi 2h.
# BU DEGER CEKIRDEGE OZGUDUR ve bu satir onun TEK kaynagidir.
SUPPORT_OVER_H = 2.0

# Yarim aralik: hedef nokta ile en yakin kafes duzlemi arasindaki en kotu
# mesafe. Destege eklenerek "hicbir komsu kesik degil" garantisi verilir.
_SAFETY_OVER_SPACING = 0.5


def support_margin(h: float, spacing: float, depth: int = 1) -> float:
    """Serbest yüzeyden bırakılacak pay.

    `depth`: sonucun kaç komşuluk üzerinden bilgi taşıdığı (bkz. modül
    başlığı). `1` çoğu ölçüm için; grad-h gibi komşunun türetilmiş bir
    büyüklüğünü kullanan biçimler için `2`.
    """
    if h <= 0.0 or spacing <= 0.0:
        raise ValueError(f"h ve aralık pozitif olmalı: h={h}, spacing={spacing}")
    if depth < 1 or int(depth) != depth:
        raise ValueError(f"depth pozitif tam sayı olmalı, {depth} geldi")
    return float(depth) * SUPPORT_OVER_H * float(h) + _SAFETY_OVER_SPACING * float(spacing)


def margin_factor(h_over_spacing: float, depth: int = 1) -> float:
    """Payın **aralık cinsinden** katsayısı: `pay / aralık`.

    Geometri boyutlandırırken kullanışlı: `r_dış ≥ r_iç + h + pay`.
    """
    if h_over_spacing <= 0.0:
        raise ValueError(f"h/aralık pozitif olmalı, {h_over_spacing} geldi")
    return support_margin(h_over_spacing, 1.0, depth)
