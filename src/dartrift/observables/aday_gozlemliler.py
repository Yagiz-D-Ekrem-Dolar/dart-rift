"""Aday gözlemliler — kaydedilmiş durumlardan **GPU harcamadan** çıkarılan.

## Niçin

`rank(F) ≤ min(gözlemli, parametre)` aritmetiktir: iki gözemliyle (`β`,
`M_ejekta`) üç parametreden en çok iki yön **yerel ve doğrusal** olarak
öğrenilir. Ama bu ifade iki yerde eksik:

1. **Yerel.** Model doğrusal değilse `y(θ) = y_gözlem` çözüm kümesi kutuda
   eğri bir 1-B manifolddur; posterior o eğrinin etrafındaki tüptür ve eğri
   kutu içinde kıvrılıyorsa **üç kenar dağılımı da** önselden dar olabilir.
2. **Gözlemli sayısı bizim seçimimiz.** Her koşu bir **alan** üretiyor;
   onu iki skalere indirmek bir karardı, zorunluluk değil. KAYIT-073 ölçtü:
   `β − 1 = K · M_kaçan · v_ort · kos_ort / p`. Yani `(β, M_ejekta)` bize
   `M`'yi ve `v·kos` **çarpımını** veriyor; üçüncü bilgi için `v` ile
   `kos`'u **ayırmak** gerekiyor.

Bu modül o ayırmayı ve başka aday fonksiyonelleri **kaydedilmiş durumdan**
hesaplar. Havuzun her noktası tam durumu (`x, v, m, rho, mermi_kesri`)
`npz` olarak sakladığı için **yeni gözlemli eklemenin GPU maliyeti sıfır**.

## Dürüstlük kuralı — `gozlenen`

Her adayın yanında **DART karşılığı olup olmadığı** yazılı. `gozlenen =
False` olan aday posteriora **giremez**; yalnız tanı olur. Model-model
karşılaştırmasını gözlem yerine koymak, ölçülmemiş bir kesinlik iddiasıdır
(ADR-0051 §2d'nin kuralı).

## Doğruluk güvencesi

`ejekta_bilesenleri` (KAYIT-073) üç çarpanı **koşunun içinde**, doğru
çarpma ekseniyle hesaplayıp `fizik_tani`'ya yazıyor. Bu modülün çevrimdışı
yeniden hesabı o sayıları **yeniden üretmek zorundadır**; `tutarlilik_denetle`
bunu sayıyla sınar. Yani eksen/kaçış hızı yanlış kurulursa sessiz geçmez.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

__all__ = ["EN_AZ_KACAN", "Aday", "ADAYLAR", "kacan_maske", "aday_hesapla",
           "tum_adaylar", "tutarlilik_denetle", "uretim_ehat",
           "kacis_hizi_kalibre"]

#: Bir aday okunabilmesi için gereken en az kaçan parçacık. `30` altında
#: yüzdelikler ve dağılım eğimi gürültüden okunur (`ejekta_ayrismasi` ile
#: **aynı** eşik; orada ölçülmüştü: DC kolunda `4` parçacık vardı ve
#: üç çarpan reddedildi — koruma çalıştı, KAYIT-076 §5).
EN_AZ_KACAN = 30


@dataclass(frozen=True)
class Aday:
    """Bir aday gözemlinin künyesi.

    `gozlenen`
        DART için **ölçülmüş** bir karşılığı var mı. `False` ise posteriora
        giremez (yalnız tanı). Kararsız durumda `False` yazılır — iddia
        etmemek, iddia etmekten iyidir.
    `kaynak`
        Gözlemsel karşılığın künyesi ya da niçin olmadığı.
    `birim`
        Doğal birim; `log_al` ise vekil `log10` üzerinde kurulur.
    `karsilik_grubu`
        **Hangi DART ölçümünden** geliyor. Aynı gruptan iki aday
        **bağımsız gözlemli sayılmaz**: ikisi de aynı ölçümün özeti olduğu
        için hataları korelasyonludur ve ikisini birlikte kullanmak
        olmayan bilgiyi var saymaktır (ADR-0058 §3'ün `R = I` tuzağının
        aynısı, bu kez gözemli seçiminde).
    """

    ad: str
    aciklama: str
    gozlenen: bool
    kaynak: str
    birim: str
    karsilik_grubu: str
    log_al: bool = False

    def __post_init__(self) -> None:
        if not self.ad or not self.kaynak or not self.karsilik_grubu:
            raise ValueError("aday adi, kaynagi ve karsilik grubu zorunlu")
        if self.gozlenen and self.karsilik_grubu == "gozlenemez":
            raise ValueError(f"{self.ad}: gozlenen ama grubu 'gozlenemez'")


#: Aday kütüğü. **Sıra kilitli** (raporlar bu sırayı kullanır).
#:
#: ## Karşılık grupları — üç parametrenin **yapısal** sınırı
#:
#: | grup | DART ölçümü | durum |
#: |---|---|---|
#: | `periyot_degisimi` | `ΔT = −33,0 ± 1,0 dk` → `β` | **açık** |
#: | `ejekta_kutlesi` | LICIACube fotometrisi → `1,6 ± 0,3e7 kg` | **açık** |
#: | `ejekta_hiz_dagilimi` | ejekta parlaklığının zamanla azalması |
#:   **açık**, ama sayısı bu depoda kilitli değil |
#: | `ejekta_konisi` | LICIACube koni açısı | **A95 ile KAPALI** |
#: | `gozlenemez` | — | yok |
#:
#: Yani koni kapalı olsa bile **üç** açık grup var. Üç parametre için üç
#: bağımsız kısıt gerekir ve sayı **tam tutuyor** — ama yetip yetmeyeceği
#: grupların `θ`'ya **bağımsız** bağlı olmasına bakar ve bunu havuz ölçecek.
#: Bu kütük o ölçümün girdisidir, cevabı değil.
ADAYLAR: tuple[Aday, ...] = (
    Aday("beta", "momentum aktarim carpani (defterden)", True,
         "Cheng ve dig. 2023 + uretim_hedef_beta (ADR-0054 KABUL)", "-",
         "periyot_degisimi"),
    Aday("M_kacan", "kacis hizini gecen hedef kutlesi", True,
         "L17 Lolachi ve dig. 2025: 1,6 +- 0,3e7 kg", "kg",
         "ejekta_kutlesi", log_al=True),
    Aday("v_ort", "kacan kutlenin kutle agirlikli ortalama hizi", False,
         "DOGRUDAN olculmedi; (beta, M) ciftinden v*kos cikar, ayrisma icin "
         "ucuncu bir kisit gerekir", "m/s",
         "ejekta_hiz_dagilimi", log_al=True),
    Aday("kos_ort", "momentum agirlikli yon kosinusu (eksene gore)", False,
         "koni acisinin karsiligi; A95 yuzunden gozlemle KIYASLANAMAZ "
         "(hiz yonunden 600 s'de, LICIACube konumdan ~170 s'de)", "-",
         "ejekta_konisi"),
    Aday("e_hiz", "kutle-hiz dagilimi egimi: M(>v) ~ v^-e", True,
         "ejekta parlakliginin zamanla azalmasi kutle-hiz dagilimini "
         "kisitliyor (DART literaturunde standart); DEGER bu depoda "
         "kilitlenmedi -- karsiligi var, sayisi henuz yok", "-",
         "ejekta_hiz_dagilimi"),
    Aday("v_p50", "kacan kutlenin medyan hizi", False,
         "e_hiz'in saglam alternatifi; ayni gozlemsel karsilik, ayri sayi "
         "degil -- ikisi birlikte kullanilmaz", "m/s",
         "ejekta_hiz_dagilimi", log_al=True),
    Aday("v_p90", "kacan kutlenin 90. yuzdelik hizi", False,
         "hizli kuyruk; yuksek hizli bloklarla iliskili (arXiv:2506.16694) "
         "ama nicel karsilik bu depoda yok", "m/s",
         "ejekta_hiz_dagilimi", log_al=True),
    Aday("aci_p50", "kacan kutlenin medyan eksen acisi", False,
         "A95 ile ayni engel", "derece", "ejekta_konisi"),
    Aday("aci_yayilim", "eksen acisinin kutle agirlikli sd'si", False,
         "A95 ile ayni engel", "derece", "ejekta_konisi"),
    Aday("bagli_kutle", "kacis hizinin ALTINDA kalan hareketli kutle", False,
         "gozlenemez (cisme geri dusen malzeme)", "kg",
         "gozlenemez", log_al=True),
)


def uretim_ehat(carpma_acisi_derece: float = 17.0,
                nisan=(0.0, 0.0, 1.0)) -> np.ndarray:
    """Üretim sahnesinin **çarpma yönü** birim vektörü (merminin gittiği yön).

    Nişan yönü yüzey normalini verir; mermi ondan `carpma_acisi` kadar
    sapar. Üretim havuzunda nişan `(0,0,1)` ve açı `17°`; sapma `+x`
    düzleminde alınır (sahne kurucusunun kuralı).

    **Dikkat:** bu bir **yeniden kurulum**dur. Koşunun kendi kullandığı
    eksen `fizik_tani["ejekta_ayrismasi"]`'ya yansımıştır;
    `tutarlilik_denetle` ikisini karşılaştırır ve uyuşmazsa hata verir.
    """
    n = np.asarray(nisan, dtype=np.float64).ravel()
    if n.size != 3 or not np.isfinite(n).all():
        raise ValueError("nisan sonlu 3-vektor olmali")
    nn = float(np.linalg.norm(n))
    if nn <= 0.0:
        raise ValueError("nisan sifir olamaz")
    n = n / nn
    a = np.radians(float(carpma_acisi_derece))
    # n'e dik bir taban: en kucuk bilesenden kurulan kararli secim
    yardim = np.zeros(3)
    yardim[int(np.argmin(np.abs(n)))] = 1.0
    t1 = np.cross(n, yardim)
    t1 /= np.linalg.norm(t1)
    # mermi ICERI gider: -n yonunden t1'e dogru `a` kadar sapma
    return -np.cos(a) * n + np.sin(a) * t1


def kacis_hizi_kalibre(v, m, M_kacan_kosudan: float, *, mermi_kesri=None,
                       bagil_tolerans: float = 1e-9) -> float:
    """Koşunun kendi `M_kacan`'ından **kaçış hızını geri çöz** — tahmin etme.

    ## Niçin

    Çevrimdışı hesapta `v_esc`'i yeniden kurmak için hedef kütlesi ve
    **etkin yarıçap** gerekir; elipsoit sahnede etkin yarıçap koşunun
    içindeki bir ayrıntıdır ve `npz`'de yok. Tahmin etmek, bütün aday
    gözlemlileri sessizce kaydırır.

    Bunun yerine: koşu `fizik_tani["ejekta_ayrismasi"]["M_kacan"]`'ı
    **doğru** `v_esc` ile yazdı. `M_kacan(v_esc)` azalan bir basamak
    fonksiyonu olduğundan ikiye bölmeyle `v_esc` geri çözülür. Sonra
    `v_ort` ve `kos_ort` **bağımsız denetim** olur: ikisi de tutuyorsa
    eksen ve kaçış hızı doğrudur (`tutarlilik_denetle`).

    Dönen değer, kaydedilen kütleyi tam veren hız **aralığının ortası**.
    Hiçbir hız eşiği o kütleyi vermiyorsa `ValueError`.
    """
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64).ravel()
    if mermi_kesri is not None:
        hedef = ~(np.asarray(mermi_kesri, dtype=np.float64).ravel() > 0.5)
        v, m = v[hedef], m[hedef]
    hiz = np.linalg.norm(v, axis=1)
    if hiz.size == 0:
        raise ValueError("hedef parcacigi yok")
    hedef_M = float(M_kacan_kosudan)
    if not (hedef_M > 0.0):
        raise ValueError(f"M_kacan > 0 olmali, {hedef_M} geldi")
    # Azalan basamak fonksiyonu: esik buyudukce kacan kutle KUCULUR.
    s = np.argsort(hiz)[::-1]
    kum = np.cumsum(m[s])                 # en hizlidan baslayarak kumulatif
    hs = hiz[s]
    k = int(np.searchsorted(kum, hedef_M * (1.0 - bagil_tolerans)))
    if k >= kum.size:
        raise ValueError(
            f"kaydedilen M_kacan ({hedef_M:.6e}) butun hedef kutlesinden "
            f"({float(m.sum()):.6e}) buyuk -- eksen/kutle uyusmuyor")
    if abs(kum[k] - hedef_M) / hedef_M > 1e-6:
        raise ValueError(
            f"hicbir hiz esigi kaydedilen M_kacan'i vermiyor: en yakin "
            f"{kum[k]:.6e} vs {hedef_M:.6e}. Mermi ayiklamasi ya da kutle "
            f"alani yanlis olabilir.")
    # `hs` AZALAN sirali ve `kum[k]` en hizli (k+1) parcacigin kutlesi.
    # `sum(m[hiz > v_esc]) == kum[k]` olmasi icin TAM 0..k parcaciklari
    # esigi gecmeli, yani:  hs[k] > v_esc >= hs[k+1].
    # Yani esik [hs[k+1], hs[k]) araligindadir -- ONUN ortasi alinir.
    # (Ilk surumde [hs[k], hs[k-1]) ortasi aliniyordu; o deger hs[k]'nin
    # USTUNDE kaldigi icin k. parcacik sayilmiyordu ve kutle BIR PARCACIK
    # eksik cikiyordu. Sinav yakaladi.)
    alt = float(hs[k + 1]) if (k + 1) < hs.size else 0.0
    return 0.5 * (alt + float(hs[k]))


def kacan_maske(v, m, *, v_esc: float, mermi_kesri=None):
    """Kaçan hedef parçacıklarının maskesi, hızları ve kütleleri.

    Mermi parçacıkları **dışarıda** (hedef maddesi ölçülüyor). `v_esc`
    altındakiler kaçmıyor sayılır. En az `EN_AZ_KACAN` parçacık yoksa
    `ValueError` — gürültüden sayı okumak yasak.
    """
    v = np.asarray(v, dtype=np.float64)
    m = np.asarray(m, dtype=np.float64).ravel()
    if v.ndim != 2 or v.shape[1] != 3 or v.shape[0] != m.size:
        raise ValueError(f"v (N,3) ve m (N,) olmali: {v.shape}, {m.shape}")
    if not np.isfinite(v).all() or not np.isfinite(m).all():
        raise ValueError("v/m icinde sonlu olmayan deger var")
    if not (float(v_esc) > 0.0):
        raise ValueError(f"v_esc > 0 olmali, {v_esc} geldi")
    if mermi_kesri is not None:
        hedef = ~(np.asarray(mermi_kesri, dtype=np.float64).ravel() > 0.5)
        if hedef.size != m.size:
            raise ValueError("mermi_kesri uzunlugu m ile ayni olmali")
        v, m = v[hedef], m[hedef]
    hiz = np.linalg.norm(v, axis=1)
    kac = hiz > float(v_esc)
    n = int(kac.sum())
    if n < EN_AZ_KACAN:
        raise ValueError(f"kacan parcacik {n} (< {EN_AZ_KACAN}): "
                         f"aday gozlemliler gurultuden okunamaz")
    return kac, v[kac], m[kac], hiz[kac]


def _agirlikli_yuzdelik(x, w, q: float) -> float:
    """Ağırlıklı yüzdelik — ağırlıkların **kümülatif** dağılımından.

    `np.percentile` ağırlık almaz; kütle ağırlıklı hız yüzdeliği için
    kümülatif kütle kesri `q`'yu geçtiği noktada doğrusal ara değer.
    """
    x = np.asarray(x, dtype=np.float64).ravel()
    w = np.asarray(w, dtype=np.float64).ravel()
    if x.size != w.size or x.size == 0:
        raise ValueError("x ve w ayni uzunlukta ve bos olmamali")
    if np.any(w < 0.0) or float(w.sum()) <= 0.0:
        raise ValueError("agirliklar negatif olmamali ve toplami > 0 olmali")
    if not (0.0 < float(q) < 1.0):
        raise ValueError(f"q (0,1) araliginda olmali, {q} geldi")
    s = np.argsort(x)
    xs, ws = x[s], w[s]
    kum = np.cumsum(ws) / float(ws.sum())
    return float(np.interp(float(q), kum, xs))


def _dagilim_egimi(hiz, kutle, *, v_esc: float, n_kenar: int = 14,
                   ust_carpan: float = 50.0) -> float:
    """`M(>v) ∝ v^(−e)` üssü — log-log en küçük kareler.

    Kenarlar `v_esc`'ten `min(v_max, ust_carpan·v_esc)`'e geometrik.
    Boş kutular (kümülatif kütle `0`) dışarıda bırakılır; `2`'den az
    kullanılabilir kenar varsa `ValueError`.
    """
    ust = min(float(hiz.max()), ust_carpan * float(v_esc))
    if not (ust > float(v_esc)):
        raise ValueError("hiz araligi bos: v_max <= v_esc")
    kenar = np.geomspace(float(v_esc), ust, int(n_kenar))
    Mk = np.array([float(kutle[hiz >= c].sum()) for c in kenar])
    iyi = Mk > 0.0
    if int(iyi.sum()) < 2:
        raise ValueError("kutle-hiz dagilimi icin 2'den az kullanilabilir kenar")
    egim = np.polyfit(np.log(kenar[iyi]), np.log(Mk[iyi]), 1)[0]
    return float(-egim)


def aday_hesapla(v, m, *, ehat, v_esc: float, mermi_kesri=None,
                 beta: float | None = None) -> dict[str, float]:
    """Bütün adayları tek durumdan hesaplar — `ADAYLAR` sırasında.

    `beta` verilirse (`fizik_tani["beta_hedef"]`) sözlüğe olduğu gibi
    girer; `None` ise `beta` anahtarı **yazılmaz** (uydurulmaz).

    `ehat` **çarpma yönü**; ejekta ters yöne gittiği için kosinüs
    `−v·ehat/|v|` ile ölçülür (`ejekta_ayrismasi` ile aynı işaret kuralı).
    """
    e = np.asarray(ehat, dtype=np.float64).ravel()
    if e.size != 3:
        raise ValueError("ehat 3-vektor olmali")
    ne = float(np.linalg.norm(e))
    if not (ne > 0.0):
        raise ValueError("ehat sifir olamaz")
    e = e / ne

    kac, vv, mm, hiz = kacan_maske(v, m, v_esc=v_esc, mermi_kesri=mermi_kesri)
    kos = -(vv @ e) / hiz
    aci = np.degrees(np.arccos(np.clip(kos, -1.0, 1.0)))

    M = float(mm.sum())
    out: dict[str, float] = {
        "M_kacan": M,
        "v_ort": float(np.average(hiz, weights=mm)),
        "kos_ort": float(np.average(kos, weights=mm * hiz)),
        "e_hiz": _dagilim_egimi(hiz, mm, v_esc=v_esc),
        "v_p50": _agirlikli_yuzdelik(hiz, mm, 0.50),
        "v_p90": _agirlikli_yuzdelik(hiz, mm, 0.90),
        "aci_p50": _agirlikli_yuzdelik(aci, mm, 0.50),
        "aci_yayilim": float(np.sqrt(np.average(
            (aci - np.average(aci, weights=mm)) ** 2, weights=mm))),
        "n_kacan": float(int(kac.sum())),
    }
    # bagli ama hareketli kutle: kacis esiginin ALTINDA kalan hedef maddesi
    vt = np.asarray(v, dtype=np.float64)
    mt = np.asarray(m, dtype=np.float64).ravel()
    if mermi_kesri is not None:
        hedef = ~(np.asarray(mermi_kesri, dtype=np.float64).ravel() > 0.5)
        vt, mt = vt[hedef], mt[hedef]
    h_tum = np.linalg.norm(vt, axis=1)
    out["bagli_kutle"] = float(mt[h_tum <= float(v_esc)].sum())
    if beta is not None:
        b = float(beta)
        if not np.isfinite(b):
            raise ValueError("beta sonlu olmali")
        out["beta"] = b
    return out


def tum_adaylar(durumlar) -> dict[str, np.ndarray]:
    """Birçok durumdan aday dizileri — `{ad: (N,)}`.

    `durumlar`: her biri `aday_hesapla`'nın döndürdüğü sözlük. Bir durumda
    eksik olan anahtar `nan` olur ve **sessiz geçmez**: `eksik_sayisi`
    anahtarı kaç durumda kaç alanın eksik olduğunu sayar (kural 8).
    """
    kayit = list(durumlar)
    if not kayit:
        raise ValueError("en az bir durum gerekir")
    adlar = sorted({a for d in kayit for a in d})
    out = {ad: np.array([float(d.get(ad, np.nan)) for d in kayit])
           for ad in adlar}
    out["eksik_sayisi"] = np.array(
        [float(sum(1 for ad in adlar if ad not in d)) for d in kayit])
    return out


def tutarlilik_denetle(hesaplanan: dict, kosudan: dict, *,
                       bagil_tolerans: float = 1e-6) -> dict:
    """Çevrimdışı hesap, **koşunun kendi** yazdığı üç çarpanı yeniden üretiyor mu?

    `kosudan`: `fizik_tani["ejekta_ayrismasi"]`. Üç alanın (`M_kacan`,
    `v_ort`, `kos_ort`) bağıl farkı `bagil_tolerans`'ı aşarsa **hata** —
    çünkü aşıyorsa çarpma ekseni ya da kaçış hızı yanlış kurulmuş demektir
    ve bütün aday gözlemliler yanlış olur.
    """
    if "hata" in kosudan:
        return {"denetlendi": False, "neden": str(kosudan["hata"])[:120]}
    farklar = {}
    for ad in ("M_kacan", "v_ort", "kos_ort"):
        if ad not in kosudan or ad not in hesaplanan:
            raise ValueError(f"tutarlilik icin {ad} iki tarafta da gerekli")
        a, b = float(hesaplanan[ad]), float(kosudan[ad])
        if b == 0.0:
            raise ValueError(f"kosudan gelen {ad} sifir")
        farklar[ad] = abs(a - b) / abs(b)
    en_buyuk = max(farklar.values())
    if en_buyuk > float(bagil_tolerans):
        raise ValueError(
            f"cevrimdisi hesap kosunun sayilarini yeniden uretmiyor: "
            f"en buyuk bagil fark {en_buyuk:.3e} > {bagil_tolerans:.1e}; "
            f"farklar {farklar}. Carpma ekseni ya da kacis hizi yanlis.")
    return {"denetlendi": True, "farklar": farklar, "en_buyuk": en_buyuk}
