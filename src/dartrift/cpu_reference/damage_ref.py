"""Grady-Kipp hasar modeli — CPU referansi (Benz & Asphaug 1995).

P2 §1.3'te STRETCH olarak birakilmis, D = 0 sabitlenmisti. Bu modul o bosluğu
kapatir.

UC PARCA:

1. **Kusur tohumlama** (`seed_flaws`). Weibull dagilimindan her parcaciga
   aktivasyon gerinimleri atanir. Tohumlama DETERMINISTIKTIR
   (`dartrift.rng` adlandirilmis akisi) ve parcacik SIRASINDAN bagimsizdir.

2. **Hasar evrimi** (`damage_rate`). Aktive olmus kusur sayisiyla orantili
   catlak buyumesi:  d(D^(1/3))/dt = n_aktif * c_g / R_s

3. **Hasar uygulamasi** (`apply_damage`). YALNIZCA CEKME zayiflatilir.

GERI DONUSUM YOK: hasar monoton artar (D_yeni >= D_eski). Kirilan kaya
kendini onarmaz; bunu zorlamak fiziksel bir sarttir, sayisal bir kolaylik
degil.
"""

from __future__ import annotations

import numpy as np

from ..rng import stream_generator
from .materials import DamageParams

__all__ = [
    "seed_flaws",
    "activated_flaw_count",
    "damage_rate",
    "apply_damage",
    "weibull_strain_scale",
    "max_principal_stress",
    "youngs_modulus",
    "local_scalar_strain",
]


def youngs_modulus(bulk_K: float, shear_G: float) -> float:
    """E = 9KG / (3K + G) — izotropik elastik baglanti."""
    if bulk_K <= 0.0 or shear_G <= 0.0:
        raise ValueError("K ve G pozitif olmali")
    return float(9.0 * bulk_K * shear_G / (3.0 * bulk_K + shear_G))


def max_principal_stress(P: np.ndarray, S: np.ndarray) -> np.ndarray:
    """sigma = -P I + S tensorunun EN BUYUK ozdegeri (cekme POZITIF).

    Isaret sozlesmesi: bu depoda P > 0 BASMADIR. Gerilme tensoru bu yuzden
    -P I + S'dir ve pozitif ozdeger CEKME demektir. Hasari tetikleyen sey
    en cok cekme goren asal yondur — hacimsel cekmeye (-P) bakmak, kesme
    kaynakli kirilmayi tamamen kacirirdi.
    """
    P = np.asarray(P, dtype=np.float64)
    S = np.asarray(S, dtype=np.float64)
    sig = S - P[:, None, None] * np.eye(3)[None, :, :]
    # simetrikligi zorla: sayisal asimetri ozdegerleri karmasik yapabilir
    sig = 0.5 * (sig + np.transpose(sig, (0, 2, 1)))
    return np.linalg.eigvalsh(sig)[:, -1]


def local_scalar_strain(
    P: np.ndarray, S: np.ndarray, bulk_K: float, shear_G: float
) -> np.ndarray:
    """eps = sigma_max / E — Benz & Asphaug'un yerel skaler gerinimi.

    Yalnizca CEKME sayilir; basmada eps = 0 (kusurlar acilmaz).
    """
    e_mod = youngs_modulus(bulk_K, shear_G)
    return np.maximum(max_principal_stress(P, S), 0.0) / e_mod


def weibull_strain_scale(k: float, m: float, volume: float) -> float:
    """Bir parcacigin hacminde ILK kusurun beklenen aktivasyon gerinimi.

    n(eps) V = 1 -> eps = (1 / (k V))^(1/m). Olcek kontrolu icin kullanisli:
    bu deger malzemenin etkin cekme gerinimi mertebesindedir.
    """
    if k <= 0.0 or m <= 0.0 or volume <= 0.0:
        raise ValueError("k, m ve hacim pozitif olmali")
    return float((1.0 / (k * volume)) ** (1.0 / m))


def seed_flaws(
    n_particles: int,
    particle_volume: float,
    dp: DamageParams,
    root_seed: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Her parcaciga Weibull kusurlari ata -> (eps_min, n_flaws).

    YONTEM (Benz & Asphaug 1995 §2.2). Toplam N_f = n_flaws_per_particle * N
    kusur, TUM hacme dagitilir. j'inci kusurun aktivasyon gerinimi ters
    donusumle:

        eps_j = (j / (k * V_toplam))^(1/m),   j = 1..N_f

    ve kusurlar parcaciklara rastgele DAGITILIR. Bir parcacigin cekme
    davranisini belirleyen sey, ustundeki EN ZAYIF kusurdur (`eps_min`);
    hasar hizi ise aktive olmus kusur SAYISINA baglidir.

    Donen:
      eps_min  (N,) parcacik basina en dusuk aktivasyon gerinimi
      n_flaws  (N,) parcacik basina kusur sayisi (>=1 garanti degil; kusursuz
               parcacik eps_min = +inf alir ve asla hasar gormez)

    DETERMINIZM: dagitim `dartrift.rng`in adlandirilmis akisindan gelir;
    ayni tohum + ayni N ayni sonucu verir.
    """
    if n_particles <= 0:
        raise ValueError(f"n_particles pozitif olmali, {n_particles} geldi")
    if particle_volume <= 0.0:
        raise ValueError(f"parcacik hacmi pozitif olmali, {particle_volume} geldi")
    if dp.k_weibull <= 0.0 or dp.m_weibull <= 0.0:
        raise ValueError("k_weibull ve m_weibull pozitif olmali")
    if dp.n_flaws_per_particle <= 0.0:
        raise ValueError("n_flaws_per_particle pozitif olmali")

    v_total = particle_volume * n_particles
    n_f = int(round(dp.n_flaws_per_particle * n_particles))
    rng = stream_generator(root_seed, "damage_flaws")

    j = np.arange(1, n_f + 1, dtype=np.float64)
    eps_j = (j / (dp.k_weibull * v_total)) ** (1.0 / dp.m_weibull)
    owner = rng.integers(0, n_particles, size=n_f)

    eps_min = np.full(n_particles, np.inf, dtype=np.float64)
    np.minimum.at(eps_min, owner, eps_j)
    n_flaws = np.bincount(owner, minlength=n_particles).astype(np.float64)
    return eps_min, n_flaws


def activated_flaw_count(
    strain: np.ndarray, eps_min: np.ndarray, n_flaws: np.ndarray, dp: DamageParams
) -> np.ndarray:
    """Verili gerinimde aktive olan kusur sayisi (parcacik basina).

    Weibull geregi aktive olan kesir (eps/eps_min)^m ile buyur, kusur
    sayisiyla sinirlanir. Gerinim eps_min'in altindaysa hicbir kusur acilmaz.
    """
    e = np.maximum(np.asarray(strain, dtype=np.float64), 0.0)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        oran = np.where(np.isfinite(eps_min) & (eps_min > 0.0), e / eps_min, 0.0)
        n_act = np.where(oran > 1.0, oran ** dp.m_weibull, 0.0)
    return np.minimum(np.nan_to_num(n_act, nan=0.0, posinf=0.0), n_flaws)


def damage_rate(
    strain: np.ndarray,
    eps_min: np.ndarray,
    n_flaws: np.ndarray,
    cs: np.ndarray,
    r_s: float,
    dp: DamageParams,
) -> np.ndarray:
    """d(D^(1/3))/dt = n_aktif * c_g / R_s.

    `r_s` parcacigin etkin yaricapi (catlagin kat etmesi gereken uzunluk).
    Kubuk kok uzerinden ilerlemek Grady-Kipp'in tanimi: D hacimsel bir
    kesirdir, catlak YARICAPI ise dogrusal buyur.
    """
    if r_s <= 0.0:
        raise ValueError(f"r_s pozitif olmali, {r_s} geldi")
    n_act = activated_flaw_count(strain, eps_min, n_flaws, dp)
    c_g = dp.crack_speed_frac * np.asarray(cs, dtype=np.float64)
    return n_act * c_g / r_s


def apply_damage(
    P: np.ndarray, S: np.ndarray, D: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Hasari basinc ve deviatorik gerilmeye uygula.

    YALNIZCA CEKME zayiflar:
        P < 0 -> (1-D) P
        P >= 0 -> degismez        (kirik kaya hala basmaya dayanir)
        S     -> (1-D) S

    Basmayi da zayiflatmak, kraterlesmeyi tamamen yanlis yapardi: sok
    onunde malzeme basma altindadir ve orada dayanim kaybi fiziksel degildir.
    """
    d = np.clip(np.asarray(D, dtype=np.float64), 0.0, 1.0)
    p = np.asarray(P, dtype=np.float64)
    p_new = np.where(p < 0.0, (1.0 - d) * p, p)
    s_new = np.asarray(S, dtype=np.float64) * (1.0 - d)[:, None, None]
    return p_new, s_new
