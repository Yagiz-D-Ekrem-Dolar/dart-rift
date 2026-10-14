"""`β`'nın izdüşüm geleneği — model ile gözlemi **aynı** büyüklüğe getirir.

## Niçin (ADR-0060)

Benzetim `β`'yı **çarpıcı momentumu** doğrultusuna izdüşürüyor. Gözlenen
değer öyle tanımlanmamış: Cheng ve ark. (2023, arXiv:2303.03464)
Denklem (1), `β`'yı **net fırlatı momentumu** doğrultusu `Ê`'ye
referanslı tanımlıyor ve gerekçesini de yazıyor — sonuç yüzey
topografyasından bağımsız olsun diye.

Along-track yön `β`'nın tanımı DEĞİL; `Δv⃗`'nin tamamı ölçülemediği için
Denklem (1) `ê_T` ile skaler çarpılır (Denklem 2). Referans yön hâlâ `Ê`.

Zincir: Cheng `β = 3,61 (+0,19/−0,25)`; ADR-0054'ün
`β_göz = 3,5418 (+0,188/−0,247)` bunun sahne kütlesine göre
düzeltilmişidir. Yani karşılaştırdığımız sayı `Ê` geleneğinde.

## Dönüşüm

`P⃗ = Σ m v⃗` kaçan hedef maddesinin net momentumu, `Ê = P⃗/|P⃗|`,
`θ = ∠(Ê, ê_U)` olmak üzere:

    b_çarpıcı = |P⃗| |cos θ| / p
    b_fırlatı = |P⃗| / (p |cos θ|)
    ⟹ b_fırlatı = b_çarpıcı / cos²θ

Ölçüldü (88 koşu, KAYIT-078 §6): `θ = 14,1°..27,7°`, oran ortanca
`1,166`. Bu, `σ_model`'in (`0,065`) iki katından büyük.

**Ayarlanabilir serbestlik yoktur:** `cos θ` seçilmez, her koşunun kendi
fırlatı alanından hesaplanır. `|cos θ| < 1` olduğundan düzeltme `b`'yi
**daima büyütür**; yönü seçilemez.
"""

from __future__ import annotations

import numpy as np

__all__ = ["firlati_dogrultusu", "gelenek_carpani", "b_firlati_geleneginde"]

#: `|cos θ|` bunun altındaysa dönüşüm patlar: `Ê` ile `ê_U` dikleşirken
#: `1/cos²` ıraksar ve sayı anlamını yitirir. Ölçülen aralık
#: `0,886–0,970`; bu taban ondan çok uzakta, yani normal koşuda hiç
#: devreye girmez — bozuk bir fırlatı alanını yakalamak için var.
ASGARI_KOSINUS = 0.30


def firlati_dogrultusu(v, m, kacan) -> tuple[np.ndarray, float]:
    """Kaçan hedef maddesinin net momentum doğrultusu `Ê` ve `|P⃗|`.

    `kacan`: kaçan **hedef** parçacıklarının maskesi (mermi ayıklanmış,
    hız eşiğini geçen). Maskeyi bu fonksiyon kurmaz — kaçış ölçütü
    koşunun kendi `M_kacan`'ından geri çözülür (PROTOKOL-SI §2).
    """
    v = np.atleast_2d(np.asarray(v, dtype=np.float64))
    m = np.asarray(m, dtype=np.float64).ravel()
    kacan = np.asarray(kacan, dtype=bool).ravel()
    if v.shape[0] != m.size or kacan.size != m.size:
        raise ValueError(f"v {v.shape}, m {m.shape}, kacan {kacan.shape} "
                         "uyusmuyor")
    if not kacan.any():
        raise ValueError("kacan parcacik yok -- Ê tanimsiz")
    P = (m[kacan, None] * v[kacan]).sum(0)
    nP = float(np.linalg.norm(P))
    if not (nP > 0.0):
        raise ValueError("net firlati momentumu sifir -- Ê tanimsiz")
    return P / nP, nP


def gelenek_carpani(E_sapka, e_carpici) -> float:
    """`1/cos²θ` — çarpıcı geleneğinden fırlatı geleneğine çarpan.

    `θ`, net fırlatı doğrultusu ile çarpıcı momentumu doğrultusu
    arasındaki açıdır. Fırlatı geri tepmeyle çıktığı için `cos θ < 0`
    beklenir; işaret önemsizdir, kare alınır.
    """
    E_sapka = np.asarray(E_sapka, dtype=np.float64).ravel()
    e_carpici = np.asarray(e_carpici, dtype=np.float64).ravel()
    for ad, u in (("Ê", E_sapka), ("ê_U", e_carpici)):
        n = float(np.linalg.norm(u))
        if not np.isclose(n, 1.0, atol=1e-8):
            raise ValueError(f"{ad} birim vektor olmali, |{ad}| = {n:.6g}")
    kos = float(E_sapka @ e_carpici)
    if abs(kos) < ASGARI_KOSINUS:
        raise ValueError(
            f"|cos theta| = {abs(kos):.4f} < {ASGARI_KOSINUS}: firlati "
            "dogrultusu carpiciya neredeyse dik, 1/cos^2 iraksiyor")
    return 1.0 / (kos * kos)


def b_firlati_geleneginde(b_carpici: float, E_sapka, e_carpici) -> float:
    """`b` değerini gözlemin geleneğine çevir (ADR-0060).

    `b_carpici = β_koşu − 1`, yani koşunun kendi raporladığı değer.
    """
    if not np.isfinite(b_carpici):
        raise ValueError(f"b sonlu olmali, {b_carpici} geldi")
    return float(b_carpici) * gelenek_carpani(E_sapka, e_carpici)
