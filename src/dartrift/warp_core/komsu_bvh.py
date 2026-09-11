"""A52 — destek kutulu BVH + kimliğe göre sıralı CSR komşu listesi.

## Neden (rapor A52, uzman yanıtı 2026-09-11 Soru 6/20)

Hash ızgarası TEK küresel yarıçapla (`2 h_max`) sorgulanıyor. Merdivende
`h_max / h_min = 40` olduğundan en ince parçacık bile kaba parçacığın
yarıçapıyla arıyor. Ölçüldü (orta kayıt, `N = 69 379`):

| | hash ızgarası | destek kutulu BVH |
|---|---:|---:|
| aday / parçacık (seviye ağırlıklı) | 50 892,99 | 626,81 |
| gerçek komşu / parçacık | 351,79 | 351,79 |

Uzmanın gözlemi: gerçekleşen çiftlerde `h_j / h_i ≤ 2,5` — büyük küresel
`h` oranı gerçek çiftlerin oranı DEĞİL.

## Yöntem

Destek koşulu `r_ij < h_i + h_j` (`h_ij = (h_i + h_j)/2`, destek `2 h_ij`).
Her `j` için eksenlere paralel kutu `B_j = [x_j − h_j, x_j + h_j]`. Gerçek
bir çiftte her koordinat farkı `h_i + h_j`'den küçük olduğundan
`B_i ∩ B_j ≠ ∅` ZORUNLU. Kutu adayları FP64 küresel koşulla süzülür.
Böylece `h` sürekli değişse de tek BVH ile eksiksiz aday üretilir;
düğüm başına `h_max` ya da seviye ağaçları gerekmez.

- **Gather kalır**: her parçacık yalnız kendi sonucuna yazar, atomik yok,
  `h_ij` formülü değişmez.
- **Deterministik sıra**: BVH dolaşım sırası ağaca bağlıdır (CPU ve GPU
  ağaçları farklı). Her satır kalıcı parçacık kimliğine göre SIRALANIR;
  toplama sırası ağaçtan bağımsızlaşır.
- **FP32 kutular muhafazakâr**: yarıçap `h (1 + 1e-4) + 1e-6` ile
  genişletilir; `|x| ≲ 500 m`'de FP32 yuvarlaması (`~ulp/2`) bu payın
  çok altında. Süzgeç FP64'te ve ÜST KÜME verir (`1 + 1e-12`); fizik
  çekirdekleri kendi kesin koşullarını uygular, destek dışı komşunun
  katkısı TAM sıfırdır (`grad_w3d`, `w3d`).
- **Önbellek**: konum sürümü değişmediyse (adımdaki ikinci
  değerlendirme) liste yeniden kurulmaz.
"""

from __future__ import annotations

import warp as wp

F = wp.float64
V3 = wp.vec3d

KUTU_PAY_REL = wp.constant(F(1.0e-4))
KUTU_PAY_ABS = wp.constant(F(1.0e-6))
SUZGEC_PAY = wp.constant(F(1.0e-12))


@wp.kernel
def _destek_kutulari(x: wp.array(dtype=V3), h: wp.array(dtype=F),
                     alt: wp.array(dtype=wp.vec3), ust: wp.array(dtype=wp.vec3)):
    i = wp.tid()
    p = x[i]
    r = h[i] * (F(1.0) + KUTU_PAY_REL) + KUTU_PAY_ABS
    alt[i] = wp.vec3(wp.float32(p[0] - r), wp.float32(p[1] - r), wp.float32(p[2] - r))
    ust[i] = wp.vec3(wp.float32(p[0] + r), wp.float32(p[1] + r), wp.float32(p[2] + r))


@wp.func
def _komsu_mu(xi: V3, hi: F, xj: V3, hj: F) -> bool:
    return wp.length(xi - xj) < (hi + hj) * (F(1.0) + SUZGEC_PAY)


@wp.kernel
def _say(bvh: wp.uint64, x: wp.array(dtype=V3), h: wp.array(dtype=F),
         alt: wp.array(dtype=wp.vec3), ust: wp.array(dtype=wp.vec3),
         say: wp.array(dtype=wp.int32)):
    i = wp.tid()
    xi = x[i]
    hi = h[i]
    q = wp.bvh_query_aabb(bvh, alt[i], ust[i])
    j = int(0)
    n = int(0)
    while wp.bvh_query_next(q, j):
        if _komsu_mu(xi, hi, x[j], h[j]):
            n += 1
    say[i] = n


@wp.kernel
def _doldur(bvh: wp.uint64, x: wp.array(dtype=V3), h: wp.array(dtype=F),
            alt: wp.array(dtype=wp.vec3), ust: wp.array(dtype=wp.vec3),
            bas: wp.array(dtype=wp.int32), icerde_sirala: int,
            nbr: wp.array(dtype=wp.int32)):
    i = wp.tid()
    xi = x[i]
    hi = h[i]
    s = int(bas[i])
    k = int(s)
    q = wp.bvh_query_aabb(bvh, alt[i], ust[i])
    j = int(0)
    while wp.bvh_query_next(q, j):
        if _komsu_mu(xi, hi, x[j], h[j]):
            nbr[k] = j
            k += 1
    if icerde_sirala == 0:
        return
    # YEDEK: EKLEME SIRALAMASI (bolutlu siralama yoksa). Olculdu (RTX
    # 3050, kaba merdiven): bu dongu 256 ms/adim -- sayim gecisinin 15
    # kati; bolutlu radix siralama varsayilan. Kosul bilesik yazilmadi:
    # Warp `and`'i kisa devre etmez; `b >= s` yanlisken `nbr[b]` bir
    # onceki satiri (ya da -1'i) okurdu.
    for a in range(s + 1, k):
        anahtar = nbr[a]
        b = a - 1
        while b >= s:
            if nbr[b] > anahtar:
                nbr[b + 1] = nbr[b]
                b -= 1
            else:
                break
        nbr[b + 1] = anahtar


class BvhKomsu:
    """Destek kutulu BVH'den sıralı CSR: `bas` (N+1), `nbr` (toplam).

    Satır `i`'nin komşuları `nbr[bas[i]:bas[i+1]]`, artan kimlik sırasında,
    kendisi DAHİL (fizik çekirdekleri kendi koşullarıyla dışlar).
    """

    def __init__(self, n: int, device: str, yeniden_kurma: int = 16,
                 siralama: str = "bolutlu"):
        self.n = int(n)
        self.device = device
        self.alt = wp.zeros(self.n, dtype=wp.vec3, device=device)
        self.ust = wp.zeros(self.n, dtype=wp.vec3, device=device)
        self.say = wp.zeros(self.n, dtype=wp.int32, device=device)
        self.bas = wp.zeros(self.n + 1, dtype=wp.int32, device=device)
        # SIRALAMA: "bolutlu" -- wp.utils.segmented_sort_pairs (CUB bolutlu
        # radix; deterministik). "ekleme" -- cekirdek icinde (yedek).
        # Bolutlu siralama anahtar VE deger dizilerinin 2*toplam
        # kapasitede olmasini ister; deger dizisi yalniz tampon.
        if siralama not in ("bolutlu", "ekleme"):
            raise ValueError(f"siralama 'bolutlu' ya da 'ekleme', {siralama!r}")
        if siralama == "bolutlu" and not hasattr(wp.utils, "segmented_sort_pairs"):
            siralama = "ekleme"
        self.siralama = siralama
        kap = max(2, 2 * 64 * self.n)
        self.nbr = wp.zeros(kap, dtype=wp.int32, device=device)
        self._deger = (wp.zeros(kap, dtype=wp.int32, device=device)
                       if siralama == "bolutlu" else None)
        self.bvh = None
        self._surum = None
        self._refit = 0
        self.yeniden_kurma = int(yeniden_kurma)
        self.n_kurulum = 0
        self.toplam = 0

    def kur(self, x: wp.array, h: wp.array, surum=None) -> bool:
        """Listeyi kur; `surum` öncekiyle aynıysa ATLA ve `False` döndür."""
        if surum is not None and surum == self._surum:
            return False
        n = self.n
        wp.launch(_destek_kutulari, dim=n, inputs=[x, h],
                  outputs=[self.alt, self.ust], device=self.device)
        if self.bvh is None:
            self.bvh = wp.Bvh(self.alt, self.ust)
        elif self._refit >= self.yeniden_kurma:
            # refit topolojiyi korur (DOGRU ama hareketle verim duser);
            # arada bir tam yeniden kurma verimi geri getirir.
            self.bvh.rebuild()
            self._refit = 0
        else:
            self.bvh.refit()
            self._refit += 1
        wp.launch(_say, dim=n,
                  inputs=[self.bvh.id, x, h, self.alt, self.ust],
                  outputs=[self.say], device=self.device)
        wp.utils.array_scan(self.say, self.bas[1:], inclusive=True)
        toplam = int(self.bas[n:n + 1].numpy()[0])
        gerek = 2 * toplam
        if gerek > len(self.nbr):
            kap = int(gerek * 1.25) + 2
            self.nbr = wp.zeros(kap, dtype=wp.int32, device=self.device)
            if self._deger is not None:
                self._deger = wp.zeros(kap, dtype=wp.int32, device=self.device)
        bolutlu = self.siralama == "bolutlu"
        wp.launch(_doldur, dim=n,
                  inputs=[self.bvh.id, x, h, self.alt, self.ust, self.bas,
                          0 if bolutlu else 1],
                  outputs=[self.nbr], device=self.device)
        if bolutlu and toplam > 0:
            # Her satir [bas[i], bas[i+1]) bir bolut; anahtar = komsu kimligi.
            wp.utils.segmented_sort_pairs(self.nbr, self._deger, toplam, self.bas)
        self._surum = surum
        self.toplam = toplam
        self.n_kurulum += 1
        return True

    def tani(self) -> dict:
        return {"komsu_arama": "bvh", "siralama": self.siralama,
                "n_kurulum": int(self.n_kurulum),
                "toplam_cift": int(self.toplam),
                "ortalama_komsu": float(self.toplam / max(self.n, 1))}
