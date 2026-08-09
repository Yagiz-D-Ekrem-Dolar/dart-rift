"""G4 kapı yargısı — **kod**, elle yazılmış bir rapor değil (FAZ 4.7).

## Neden kod

G0–G3 kapılarında rapor elle yazıldı ve her seferinde aynı risk vardı:
bir ölçüt koşulmamışken *"geçti"* yazmak. KAYIT-017'nin (3. tur) bulduğu
kusurların bir kısmı tam buydu — **kriterin kendisi** denetlenmemişti.

Bu modül ölçüm çıktılarını okur ve kapıyı **kendisi** yargılar. Elle
yazılan tek şey ölçüt tanımıdır ve o da
[`docs/G4-OLCUTLERI.md`](../../../docs/G4-OLCUTLERI.md)'de **ölçümden
önce** sabitlendi.

## Üç kural, kodla zorlanıyor

1. **Kısmi geçiş yok.** A, B, C üçü de geçmeden kapı geçilmez.
2. **Koşulmayan ölçüt geçmiş sayılmaz.** Eksik veri `geçti` değil,
   `koşulmadı`dır ve kapıyı **geçirmez**.
3. **Koşullu kabuller listelenir.** ADR-0041 ve ADR-0042 küp
   geometrisinde ölçüldü; kapı geçse bile bu rapora yazılır.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = ["Olcut", "G4Rapor", "degerlendir", "KOSULLU_KABULLER", "TANILAR",
           "TANI_KAYNAGI",
           "A1_MERMI_PARCACIK", "A2_R_INCE_CARPANI", "A3_KUTLE_SAPMASI",
           "B1_BETA_FARKI", "B4_ENERJI_EGIM"]

# --- G4-OLCUTLERI.md ile AYNI sayilar. Ayrisirlarsa test kirilir.
A1_MERMI_PARCACIK = 2.0
A2_R_INCE_CARPANI = 3.0
A3_KUTLE_SAPMASI = 0.005
B1_BETA_FARKI = 0.10
B4_ENERJI_EGIM = 1.0

#: Kapı geçse **bile** raporda kalan koşullar.
KOSULLU_KABULLER = (
    "ADR-0041 ve ADR-0042 küp geometrisinde ölçüldü, DART geometrisinde "
    "değil (KAYIT-035, KAYIT-037).",
    "Boşluk 3 `λ = 2` (8:1) oranında kapandı; ADR-0026 DART için çok daha "
    "yüksek oran istiyor.",
    "B1 eşiği (`%10`) bilinçli olarak gevşek; ana ürün henüz `±0,1` "
    "doğrulukta değil (G4-OLCUTLERI §3).",
)


@dataclass(frozen=True)
class Olcut:
    """Tek bir ölçüt: değeri, eşiği ve **koşulup koşulmadığı**."""

    kimlik: str
    aciklama: str
    deger: float | None
    esik: float
    yon: str                    # "<" ya da ">="

    @property
    def kosuldu(self) -> bool:
        return self.deger is not None and np.isfinite(self.deger)

    @property
    def gecti(self) -> bool:
        """Koşulmadıysa **geçmemiştir** — sessiz geçiş yok."""
        if not self.kosuldu:
            return False
        return (self.deger < self.esik if self.yon == "<"
                else self.deger >= self.esik)

    @property
    def durum(self) -> str:
        if not self.kosuldu:
            return "KOSULMADI"
        return "GECTI" if self.gecti else "DUSTU"

    def satir(self) -> str:
        d = "—" if not self.kosuldu else f"{self.deger:.6g}"
        return (f"| {self.kimlik} | {self.aciklama} | `{self.yon} "
                f"{self.esik:g}` | `{d}` | **{self.durum}** |")


#: Raporlanan ama **ölçüt olmayan** büyüklükler.
#:
#: G4-OLCUTLERI.md ölçümden **önce** yazıldı ve eşikleri kilitli. Sonradan
#: ölçülen bir büyüklüğü ölçüt yapmak o ön-kaydı bozar (ADR-0040). Ama
#: bilgiyi gizlemek de doğru değil: kapı raporunu okuyan bunları
#: **görmeli** ve ölçüt olmadıklarını bilmeli.
TANILAR = {
    "dikis_en_yakin_oran": (
        "A′ dikişinde en yakın komşu / ince aralık",
        "0,5'in altı gözden geçirme gerektirir (KAYIT-039 §2'de ölçülen: 0,6521)"),
    "tasarruf": (
        "A′'nın parçacık tasarrufu (her yeri inceltmeye göre)",
        "yüksek olması iyi; ölçülen 6,87× (s = 7,0/3,5, r_iç = 25)"),
    # --- NEDEN kosulmadi: bir olcut `kosulmadi` diyorsa SEBEBI gorunsun.
    # Bunlar OLCUT DEGIL; kapiyi gecirmez ya da dusurmez.
    "esit_t_sim": (
        "FAZ 4.4 kolları aynı `t_sim`'e ulaştı mı",
        "`0` ise B1 ve B3 **yazılmaz** — farklı `t`'deki `β`'lar "
        "yakınsama ölçmez (sıkıntı A6)"),
    "B2_sabit_seri": (
        "`β_bound` baştan sona sabit mi kaldı",
        "`1` ise B2 **yazılmaz** — sabit seride `durulmuş` boş bir "
        "kanıttır (sıkıntı 33)"),
}

#: `TANILAR`ın hangi kaynaktan okunacağı. Hepsini `faz44`'ten okumak
#: `B2_sabit_seri`'yi sessizce **düşürürdü** (o `faz45`'ten gelir).
TANI_KAYNAGI = {"esit_t_sim": "faz44", "B2_sabit_seri": "faz45"}


@dataclass(frozen=True)
class G4Rapor:
    a: list = field(default_factory=list)
    b: list = field(default_factory=list)
    c: list = field(default_factory=list)
    #: {anahtar: değer} — ölçüt DEĞİL, yalnızca raporlanır.
    tanilar: dict = field(default_factory=dict)

    def _parca(self, ol: list) -> bool:
        return bool(ol) and all(o.gecti for o in ol)

    @property
    def a_gecti(self) -> bool:
        return self._parca(self.a)

    @property
    def b_gecti(self) -> bool:
        return self._parca(self.b)

    @property
    def c_gecti(self) -> bool:
        return self._parca(self.c)

    @property
    def gecti(self) -> bool:
        """**Kısmi geçiş yok.**"""
        return bool(self.a_gecti and self.b_gecti and self.c_gecti)

    @property
    def tum_olcutler(self) -> list:
        return [*self.a, *self.b, *self.c]

    @property
    def kosulmayanlar(self) -> list:
        return [o.kimlik for o in self.tum_olcutler if not o.kosuldu]

    @property
    def dusenler(self) -> list:
        return [o.kimlik for o in self.tum_olcutler if o.kosuldu and not o.gecti]

    def markdown(self) -> str:
        """Kapı raporu — **üretilir**, elle yazılmaz."""
        p = ["# G4 kapı raporu", ""]
        durum = "**GEÇİLDİ**" if self.gecti else "**GEÇİLEMEDİ**"
        p += [f"**Sonuç:** {durum}", ""]
        if not self.gecti:
            if self.kosulmayanlar:
                p.append(f"- **koşulmayan ölçütler:** "
                         f"{', '.join(self.kosulmayanlar)}")
            if self.dusenler:
                p.append(f"- **düşen ölçütler:** {', '.join(self.dusenler)}")
            p.append("")
            p.append("> Kısmi geçiş yoktur. Bir ölçüt koşulmadıysa "
                     "**geçmemiş** sayılır.")
            p.append("")
        for ad, ol, gec in (("A — mermi çözülüyor", self.a, self.a_gecti),
                            ("B — gözlenebilirler yakınsıyor", self.b, self.b_gecti),
                            ("C — parametreler geri bulunuyor", self.c, self.c_gecti)):
            p += [f"## G4-{ad} — {'GEÇTİ' if gec else 'GEÇMEDİ'}", "",
                  "| # | ölçüt | eşik | ölçülen | durum |",
                  "|---|---|---|---|---|"]
            p += [o.satir() for o in ol]
            p.append("")
        if self.tanilar:
            p += ["## Tanılar — **ölçüt değil**", "",
                  "> Bunlar ölçüldü ama G4'ün geçme koşulu **değil**. "
                  "Ölçütler ölçümden önce yazıldı ve sonradan eklenmiyor "
                  "(ADR-0040); bilgi ise gizlenmiyor.", "",
                  "| büyüklük | ölçülen | yorum |", "|---|---|---|"]
            for k, v in sorted(self.tanilar.items()):
                ad, yorum = TANILAR.get(k, (k, ""))
                d = "—" if v is None else f"{v:.6g}"
                p.append(f"| {ad} | `{d}` | {yorum} |")
            p.append("")
        p += ["## Koşullu kabuller", "",
              "> Kapı geçse **bile** bunlar açık kalır.", ""]
        p += [f"{i}. {k}" for i, k in enumerate(KOSULLU_KABULLER, 1)]
        p.append("")
        return "\n".join(p)


def _sayi(v):
    """Sayıya çevir; çevrilemiyorsa `None`.

    ## Neden `isinstance(v, (int, float))` yetmiyor

    Numpy tiplerinin **yalnızca bir kısmı** Python sayılarının alt
    sınıfıdır. Ölçüldü:

    | tip | `isinstance(v, (int, float))` |
    |---|---|
    | `np.float64` | **True** |
    | `np.int64` | **False** |
    | `np.bool_` | **False** |
    | `np.float32` | **False** |

    Eski `_al` `isinstance` ile süzüyordu; numpy değerler geldiğinde
    ölçülmüş bir ölçütü **`koşulmadı`** sanıyordu. Ölçüldü — `np.float32`
    ve `np.bool_` girdilerle kapı:

    ```
    kosulmayan: ['A2', 'B2']      <- ikisi de OLCULMUSTU
    dusen     : ['C3']            <- gecmisti
    ```

    > Kapının var olma sebebi tam bu hatayı önlemekti: *"koşulmayan
    > ölçüt geçmiş sayılmaz."* Tersi de geçerli olmalı — **ölçülen ölçüt
    > koşulmamış sayılmaz.**

    `float()` çağrısı hepsini kapsıyor: `np.bool_` → `1.0/0.0`,
    `np.int64` → float, Python `bool` → `1.0/0.0`. Diziler ve `None`
    `TypeError`/`ValueError` verir ve `None` dönülür.
    """
    if v is None or isinstance(v, (str, bytes, dict, list, tuple)):
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _al(d: dict | None, *yol, varsayilan=None):
    """İç içe sözlükten güvenli okuma — eksik anahtar `None` döner."""
    if d is None:
        return varsayilan
    v = d
    for k in yol:
        if not isinstance(v, dict) or k not in v:
            return varsayilan
        v = v[k]
    s = _sayi(v)
    return s if s is not None else varsayilan


def degerlendir(faz44: dict | None = None, faz45: dict | None = None,
                faz46: dict | None = None) -> G4Rapor:
    """Ölçüm çıktılarından kapıyı yargıla.

    Herhangi biri `None` ise ilgili ölçütler **koşulmadı** sayılır ve
    kapı geçemez.
    """
    a = [
        Olcut("A1", "mermi çapı / yerel aralık",
              _al(faz44, "A1_mermi_parcacik_cap"), A1_MERMI_PARCACIK, ">="),
        Olcut("A2", "`r_ince / R_mermi`",
              _al(faz44, "A2_r_ince_carpani"), A2_R_INCE_CARPANI, ">="),
        Olcut("A3", "kaba/ince ek yerinde kütle sapması",
              _al(faz44, "A3_kutle_sapmasi"), A3_KUTLE_SAPMASI, "<"),
    ]
    b = [
        Olcut("B1", "ardışık çözünürlükte `β` farkı",
              _al(faz44, "B1_beta_farki"), B1_BETA_FARKI, "<"),
        Olcut("B2", "`β` durulmuş (1 = evet)",
              _al(faz45, "B2_durulmus"), 1.0, ">="),
        Olcut("B3", "A′, ince kola tek `h`'den yakın (1 = evet)",
              _al(faz44, "B3_Aprime_daha_yakin"), 1.0, ">="),
        Olcut("B4", "enerji sapması log-log eğim",
              _al(faz45, "B4_enerji_egim"), B4_ENERJI_EGIM, "<"),
    ]
    c = [
        Olcut("C1", "parametre kapsaması (3/3)",
              _al(faz46, "c1_kapsama"), 1.0, ">="),
        Olcut("C2", "en dar bant / önsel",
              _al(faz46, "c2_en_dar"), 0.50, "<"),
        # `_sayi` np.bool_ dahil her sayisal tipi float'a cevirdigi icin
        # burada ayri bir True/False esleme tablosuna GEREK KALMADI.
        Olcut("C3", "gürültüyle genişleme (1 = evet)",
              _al(faz46, "c3_gecti"), 1.0, ">="),
    ]
    _kaynak = {"faz44": faz44, "faz45": faz45, "faz46": faz46}
    tanilar = {k: _al(_kaynak[TANI_KAYNAGI.get(k, "faz44")], k)
               for k in TANILAR}
    tanilar = {k: v for k, v in tanilar.items() if v is not None}
    # KURU KIP bir kanit DEGILDIR: G4-C olcutleri kosulmamis sayilir.
    if faz46 is not None and bool(faz46.get("kuru", False)):
        c = [Olcut(o.kimlik, o.aciklama + " *(kuru kip — sayılmaz)*",
                   None, o.esik, o.yon) for o in c]
    return G4Rapor(a=a, b=b, c=c, tanilar=tanilar)
