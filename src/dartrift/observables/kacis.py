"""Kaçış sınıflaması — bağlı kalan kütleden, yinelemeli (uzman Soru 10).

## Neden

`momentum_defteri` kaçışı `r > R` **ve** `v_r > v_esc` ile tanımlıyor:
sabit yarıçap, sabit kaçış hızı, merkez orijinde. İki sorun:

1. `t = 24 ms`'de kazılan maddenin çoğu henüz `R`'nin **içinde**
   (E2'de cismin içinde `v_r > 10 m/s` olan `23 t` ölçüldü); ölçüt onu
   hiç saymıyor.
2. Uzman: *"Erken hidrodinamik evrede yerçekimini ihmal etmek kontrollü
   bir yaklaşım olabilir; buna karşın sonradan pozitif enerji etiketi
   vermek gerçek kaçış takibinin yerine geçmez. Bağlı kalan kütleden
   V_rem ve Phi_rem hesaplayın... 'Üç tur' gibi sabit sayı yerine
   yakınsama ölçütü, azami tur ve sınırdaki parçacık bayrağı olsun."*

## Tanım

Bağlı küme `B` ile başlanır (hepsi). Her turda:

- `M_B`, `X_rem`, `V_rem` = `B`'nin kütlesi, kütle merkezi, hızı;
- `Φ(r)`: `M_B` kütleli, `R` yarıçaplı düzgün kürenin potansiyeli
  (içeride `−G M (3R² − r²) / 2R³`, dışarıda `−G M / r`);
- `ε_i = ½ |v_i − V_rem|² + Φ(|x_i − X_rem|)`;
- yeni `B = {ε < 0}`. Üyelik değişmeyince ya da bağlı kütle değişimi
  `tolerans`'ın altına inince durulur; `azami_tur` aşılırsa
  `yakinsadi = False`.

**Üç ayrı çıktı** (uzman): *yüzeyden ayrılmış* (başlangıç yarıçapının
dışına çıkmış ve dışa gidiyor — `x0` gerekir), *balistik kaçış adayı*
(`ε > 0`, bu anda), *dışarıda ve bağsız* (`ε > 0` ve `r > R`). Geç
zamanda sistemden ayrılma (Didymos dahil) bu anlık görüntüden
çıkarılamaz; öyle yazılır.

> Çözücüde yerçekimi kapalı (üretim malzemesi). Potansiyel burada
> **analitik** eklenir: sınıflama anlık bir tanıdır, dinamik değildir.
"""
from __future__ import annotations

import numpy as np

G_SI = 6.67430e-11

__all__ = ["kacis_siniflari"]


def _kure_potansiyeli(r: np.ndarray, M: float, R: float, G: float) -> np.ndarray:
    ic = -G * M * (3.0 * R * R - r * r) / (2.0 * R ** 3)
    dis = -G * M / np.maximum(r, 1e-300)
    return np.where(r >= R, dis, ic)


def kacis_siniflari(x, v, m, *, R: float, G: float = G_SI, x0=None,
                    mermi_kesri=None, ehat=None, p_imp: float | None = None,
                    h=None, ayrilma_mesafesi: float = 2.0,
                    azami_tur: int = 50, tolerans: float = 1.0e-12,
                    sinir_payi: float = 1.0e-3) -> dict:
    """Yinelemeli bağlı-kütle kaçış sınıflaması (bkz. modül açıklaması).

    ## `β` hangi sınıftan (ölçülen yapıt, 2026-09-11)

    İlk sürüm `β`'yı bütün `ε > 0` maddeden hesaplıyordu ve gerçek DART
    durumunda `β_enerji = 0,84` (< 1) verdi: şoklanıp İÇERİ hızla giden
    madde de `ε > 0`. Uzman: *"Enerji >0 ile dışa hız işaretini birbirine
    karıştırmayın."* Ayrıca yüzeydeki stres dalgası (`~0,2 m/s`, mm yer
    değiştirme) kaçış hızını (`8,2 cm/s`) aşıyor. Artık sınıflar AYRI:

    - `bagsiz`        : `ε > 0`
    - `bagsiz_disa`   : `ε > 0` ve dışa (`v_r > 0`)
    - `ejekta`        : `bagsiz_disa` ve ayrılmış — `x0` verildiyse
      `r − r0 > ayrilma_mesafesi · h` (`h` yoksa `r > r0`)

    `beta_enerji` `ejekta`dan (yoksa `bagsiz_disa`dan); `beta_enerji_tum`
    bütün `ε > 0`'dan — şeffaflık için.
    """
    x = np.asarray(x, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64)
    n = len(m)
    if x.shape != (n, 3) or v.shape != (n, 3):
        raise ValueError("x ve v (N,3), m (N,) olmali")
    if R <= 0.0 or azami_tur < 1:
        raise ValueError("R > 0 ve azami_tur >= 1 olmali")
    f = (np.zeros(n) if mermi_kesri is None
         else np.asarray(mermi_kesri, dtype=np.float64))

    bagli = np.ones(n, dtype=bool)
    yakinsadi = False
    gecmis = []
    for tur in range(1, azami_tur + 1):
        M = float(m[bagli].sum())
        if M <= 0.0:
            raise ValueError("bagli kume bosaldi -- sinif tanimsiz")
        X = (m[bagli] @ x[bagli]) / M
        V = (m[bagli] @ v[bagli]) / M
        d = x - X
        r = np.linalg.norm(d, axis=1)
        phi = _kure_potansiyeli(r, M, R, G)
        dv = v - V
        eps = 0.5 * np.einsum("ij,ij->i", dv, dv) + phi
        yeni = eps < 0.0
        M_yeni = float(m[yeni].sum())
        gecmis.append(M_yeni)
        degisim = abs(M_yeni - M) / M
        esit = bool(np.array_equal(yeni, bagli))
        bagli = yeni
        if esit or degisim < tolerans:
            yakinsadi = True
            break
    bagsiz = ~bagli
    sinirda = np.abs(eps) < sinir_payi * np.abs(phi)
    disarida = r > R
    agirlik_h = m * (1.0 - f)
    out = {
        "yakinsadi": yakinsadi, "n_tur": tur, "M_bagli": float(m[bagli].sum()),
        "M_gecmisi": gecmis, "X_rem": X.tolist(), "V_rem": V.tolist(),
        "n_sinirda": int(np.count_nonzero(sinirda)),
        "M_sinirda": float(m[sinirda].sum()),
        "M_bagsiz_hedef": float(agirlik_h[bagsiz].sum()),
        "M_bagsiz_mermi": float((m * f)[bagsiz].sum()),
        "M_bagsiz_disarida_hedef": float(agirlik_h[bagsiz & disarida].sum()),
        "M_bagsiz_iceride_hedef": float(agirlik_h[bagsiz & ~disarida].sum()),
        "P_bagsiz_hedef": (agirlik_h[bagsiz] @ v[bagsiz]).tolist(),
        "bagsiz_maske": bagsiz,
    }
    vr = np.einsum("ij,ij->i", dv, d) / np.maximum(r, 1e-300)
    disa = vr > 0.0
    bagsiz_disa = bagsiz & disa
    out["M_bagsiz_disa_hedef"] = float(agirlik_h[bagsiz_disa].sum())
    ejekta = None
    if x0 is not None:
        x0 = np.asarray(x0, dtype=np.float64)
        r0 = np.linalg.norm(x0 - X, axis=1)
        if h is not None:
            hh = np.broadcast_to(np.asarray(h, dtype=np.float64), (n,))
            uzak = (r - r0) > float(ayrilma_mesafesi) * hh
        else:
            uzak = r > r0
        ayrilmis = uzak & disa
        ejekta = bagsiz_disa & uzak
        out["M_ayrilmis_hedef"] = float(agirlik_h[ayrilmis].sum())
        out["M_ayrilmis_bagsiz_hedef"] = float(agirlik_h[ayrilmis & bagsiz].sum())
        out["M_ejekta_hedef"] = float(agirlik_h[ejekta].sum())
    if ehat is not None and p_imp is not None:
        e = np.asarray(ehat, dtype=np.float64)
        e = e / np.linalg.norm(e)
        pe = agirlik_h * (v @ e)
        # Defterle AYNI isaret kurali: kacan madde -e yonunde -> negatif
        # izdusum -> beta > 1.
        out["P_bagsiz_hedef_eksenel"] = float(pe[bagsiz].sum())
        out["beta_enerji_tum"] = 1.0 - float(pe[bagsiz].sum()) / float(p_imp)
        out["beta_enerji_disa"] = (1.0 - float(pe[bagsiz_disa].sum())
                                   / float(p_imp))
        sinif = ejekta if ejekta is not None else bagsiz_disa
        out["beta_sinifi"] = "ejekta" if ejekta is not None else "bagsiz_disa"
        out["P_ejekta_eksenel"] = float(pe[sinif].sum())
        out["beta_enerji"] = 1.0 - float(pe[sinif].sum()) / float(p_imp)
    return out
