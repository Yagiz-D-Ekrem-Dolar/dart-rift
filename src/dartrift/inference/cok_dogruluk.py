"""Çok doğruluklu (kaba + orta) Gauss süreci vekili — Kennedy–O'Hagan AR(1).

## Neden

Geç evre şemasıyla bir koşu (600 s) kaba çözünürlükte `~7` GPU-saat, orta
çözünürlükte bunun birkaç katı (ADR-0050, W0). 72 noktalık bir **orta** havuz
bütçeyi aşar; kaba havuz karşılanabilir. Ama kaba ile orta aynı `β`'yı
vermiyor (Protokol M: yakınsama yok; U0 kaba → orta `−%13`).

Çözüm literatürde standart (Kennedy & O'Hagan 2000; özyinelemeli biçim
Le Gratiet & Garnier 2014): **çok sayıda ucuz + az sayıda pahalı** koşu.

    y_orta(x) = ρ · f_kaba(x) + δ(x)

- `f_kaba`: kaba havuzun GP'si (çok nokta),
- `ρ`: ölçek (kaba → orta sistematik farkı),
- `δ`: fark GP'si (az orta nokta; kaba noktalarının alt kümesi olması
  önerilir — iç içe tasarım).

Öngörü (özyinelemeli yaklaşım, iç içe tasarımda kesin):

    μ_orta = ρ μ_kaba + μ_δ,      σ²_orta = ρ² σ²_kaba,gizli + σ²_δ

## `ρ` nasıl seçiliyor (ADR-0004 determinizm)

`ρ` sabit bir ızgarada, `δ`'nın **profil log-marjinal olabilirliği**
en küçüklenerek seçilir; en iyi noktanın çevresi ince ızgarayla yeniden
taranır. İlk `ρ` tam çok-başlangıçlı, sonrakiler bir önceki en iyi
hiperparametreden **sıcak başlangıçla** uydurulur (ölçüldü: Forrester
sınaması `173 s → 15 s`, sonuç aynı). Izgara ve arama tohumsuzdur → aynı
veri bit-aynı sonuç. Seçilen `ρ` ızgaranın kenarındaysa **uyarı alanı**
doldurulur (ızgara dar kalmış olabilir).

> Bu modül karar kuralı DEĞİLDİR. Hangi havuzun (kaba/orta) hangi
> protokolde kullanılacağını protokol kilitler.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .design import ParamSpace
from .gp_vekil import GpVekil, gp_uydur

__all__ = ["CokDogrulukVekil", "cok_dogruluk_uydur", "RHO_IZGARASI"]

#: `ρ` KABA ızgarası — kaba ve orta aynı büyüklüğü ölçtüğü için `0–2` geniş
#: bir kapsam; merkez `1` (fark yok). En iyi noktanın çevresi ayrıca
#: `INCE_ADIM` sayısıyla inceltilir (toplam çözünürlük ~`0,01`).
RHO_IZGARASI = tuple(np.round(np.linspace(0.0, 2.0, 21), 6))
INCE_ADIM = 11


@dataclass(frozen=True)
class CokDogrulukVekil:
    kaba: GpVekil
    fark: GpVekil
    rho: float
    rho_profil: tuple = field(default_factory=tuple)
    uyarilar: tuple = field(default_factory=tuple)

    @property
    def space(self) -> ParamSpace:
        return self.kaba.space

    def predict_u(self, Uy, *, yeni_gerceklem: bool = True):
        """Birim küpte `(ortalama, varyans)` — orta doğrulukta, doğal birim.

        Kaba katmanın **gizli** varyansı `ρ²` ile taşınır; yeni gerçekleme
        gürültüsü fark katmanının `σn²`'sinden gelir (orta koşunun kendi
        gürültüsü).
        """
        mu_k, var_k = self.kaba.predict_u(Uy, yeni_gerceklem=False)
        mu_d, var_d = self.fark.predict_u(Uy, yeni_gerceklem=yeni_gerceklem)
        return self.rho * mu_k + mu_d, self.rho ** 2 * var_k + var_d

    def predict(self, x):
        return self.predict_u(self.space.to_unit(x))[0]


def cok_dogruluk_uydur(space: ParamSpace, x_kaba, y_kaba, x_orta, y_orta, *,
                       rho_izgara=RHO_IZGARASI) -> CokDogrulukVekil:
    """Kaba GP + `ρ` + fark GP'si.

    `x_orta` ideal olarak `x_kaba`'nın alt kümesidir (iç içe tasarım);
    değilse yaklaşım yine çalışır ama özyinelemeli varyans kesin olmaz —
    `uyarilar`'a yazılır.
    """
    x_kaba = np.atleast_2d(np.asarray(x_kaba, float))
    x_orta = np.atleast_2d(np.asarray(x_orta, float))
    y_kaba = np.asarray(y_kaba, float).ravel()
    y_orta = np.asarray(y_orta, float).ravel()
    if len(x_orta) != len(y_orta) or len(x_kaba) != len(y_kaba):
        raise ValueError("x/y uzunluklari farkli")
    if len(y_orta) < 3:
        raise ValueError(f"orta katman en az 3 nokta ister, {len(y_orta)} geldi")
    if len(y_kaba) <= len(y_orta):
        raise ValueError("kaba katman ortadan COK olmali -- aksi halde "
                         "cok dogruluk anlamsiz")
    izgara = np.asarray(rho_izgara, float)
    if izgara.ndim != 1 or len(izgara) < 3 or not np.all(np.isfinite(izgara)):
        raise ValueError("rho_izgara en az 3 sonlu deger olmali")

    uyarilar = []
    ic_ice = all(np.any(np.all(np.isclose(x_kaba, xo[None, :], rtol=0.0,
                                          atol=1e-12), axis=1))
                 for xo in x_orta)
    if not ic_ice:
        uyarilar.append("ic_ice_degil: orta noktalar kaba tasarimin alt "
                        "kumesi degil; ozyinelemeli varyans yaklasik")

    kaba = gp_uydur(space, x_kaba, y_kaba)
    mu_k_orta = kaba.predict(x_orta)

    profil: dict = {}
    en_iyi = [None, np.inf, None]
    sicak = [None]

    def _dene(rho: float) -> None:
        rho = float(np.round(rho, 9))
        if rho in profil:
            return
        r = y_orta - rho * mu_k_orta
        try:
            # SICAK BASLANGIC: ilk rho tam cok-baslangicli arama, sonrakiler
            # bir onceki en iyi hiperparametreden yerel arama (deterministik,
            # ~9 kat ucuz).
            fark = gp_uydur(space, x_orta, r, baslangic=sicak[0])
        except (ValueError, np.linalg.LinAlgError):
            profil[rho] = float("inf")
            return
        if sicak[0] is None:
            sicak[0] = fark.logp
        # gp_uydur standartlastirilmis y'de NLML verir; olcek terimi eklenir
        # ki farkli rho'lar ayni olcekte kiyaslansin.
        nlml = float(fark.nlml + len(r) * np.log(fark.y_olcek))
        profil[rho] = nlml
        if nlml < en_iyi[1]:
            en_iyi[:] = [rho, nlml, fark]
            sicak[0] = fark.logp

    for rho in izgara:
        _dene(rho)
    # INCELTME: kaba en iyinin iki komsusu arasinda esit aralikli ek noktalar
    if en_iyi[0] is not None and len(izgara) > 1:
        adim = float(np.min(np.diff(np.sort(izgara))))
        for rho in np.linspace(en_iyi[0] - adim, en_iyi[0] + adim, INCE_ADIM):
            if izgara.min() <= rho <= izgara.max():
                _dene(rho)
    rho, _, fark = en_iyi
    profil = sorted(profil.items())
    if fark is None:
        raise ValueError("hicbir rho icin fark GP'si uydurulamadi")
    if rho in (float(izgara.min()), float(izgara.max())):
        uyarilar.append(f"rho_kenarda: rho = {rho} izgaranin kenarinda")
    return CokDogrulukVekil(kaba=kaba, fark=fark, rho=rho,
                            rho_profil=tuple(profil), uyarilar=tuple(uyarilar))
