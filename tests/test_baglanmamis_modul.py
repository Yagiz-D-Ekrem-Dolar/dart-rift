"""A116'nın çaresi: **üretime bağlanmamış modül** defteri.

A116 (2026-10-09) bir kusur **sınıfı** adlandırdı: *"yazılmış ama
bağlanmamış modül"* — altyapı yazılır, belgelenir, sınavlanır ve
**çağrı yerine bağlanmadan** bırakılır. Sınavlar geçtiği için hiçbir
uyarı çıkmaz; modül "var" görünür ama üretimde **yok**. Üç örneği vardı
ve A116'nın kendi çaresi şöyleydi:

> *"`src/` altındaki her genel API'nin en az bir üretim çağrısı
> olduğunu denetleyen bir sınav. Bu yazılana kadar dördüncü örnek
> gelebilir."*

Dördüncü örnek **geldi** (A120: `failure.py` hiç çağrılmıyor ve
şartnamenin DR-RIFT-P0 §6.2 maddesini karşılamıyor), çünkü bu sınav
yazılmamıştı.

## Niçin A116'nın önerdiği GENİŞ biçim yazılmadı

Ölçüldü (2026-11-01): `__all__` ile dışa açılan `395` adın **187**'si
`src/` ve `scripts/` altında kendi modülü dışında hiç geçmiyor. Yani
geniş sınav **187 düşen** üretirdi ve çoğu **yanlış pozitif**:
`units.py`'nin birim sabitleri (`LENGTH`, `MASS`, `PRESSURE`…),
veri sınıfları (`Quantity`, `SBCSonuc`), istisnalar (`UnitError`) ve
`validation/` koşucuları (`run_arm`, `measure_*`) — hepsi meşru
kütüphane yüzeyi, sınavlar tarafından kullanılıyor. `187` düşen sınav
okunmaz, o yüzden yazılmaz.

## Yazılan DAR biçim: modül düzeyi

A116'nın üç örneğini ayıran şey **ad** değil **modül**: `cok_dogruluk`
ve `anlik_plan` modüllerinin *hiçbir* genel adı üretimden çağrılmıyordu.
Bu sınav onu ölçer — bir modülün hiçbir genel adı ve modül adının
kendisi `src/` + `scripts/` altında (kendi dosyası hariç) geçmiyorsa,
o modül **bağlanmamıştır**.

## Defter, onay değil

`BAGLANMAMIS` listesi `2026-11-04`'te **ölçülen** durumdur; bir borç
kaydıdır, "bunlar böyle kalsın" demek değildir. Sınavın işi listenin
**büyümesini** engellemek: yeni bir bağlanmamış modül eklenirse düşer.
Bir modül bağlanırsa listeden çıkarılır (sınav bunu da söyler).
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "dartrift" if (REPO / "dartrift").is_dir() else REPO / "src" / "dartrift"

#: 2026-11-04'te OLCULEN bagli-olmayan moduller. Borc kaydi, onay degil.
#:
#:   dartrift.failure                      -> A120 (sartname DR-RIFT-P0 §6.2)
#:   dartrift.validation.adaptive_h_cost   -> measure_multilevel_waste, measure_neighbour_waste
#:   dartrift.validation.deposit_calibration -> build_piston_ic, run_calibration
BAGLANMAMIS = frozenset({
    "dartrift.failure",
    "dartrift.validation.adaptive_h_cost",
    "dartrift.validation.deposit_calibration",
})


def _genel_adlar(p: Path) -> set[str]:
    """Modülün `__all__` ile dışa açtığı adlar."""
    adlar: set[str] = set()
    for n in ast.parse(p.read_text(encoding="utf-8")).body:
        if not isinstance(n, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == "__all__"
                   for t in n.targets):
            continue
        if isinstance(n.value, (ast.List, ast.Tuple)):
            for e in n.value.elts:
                if isinstance(e, ast.Constant) and isinstance(e.value, str):
                    adlar.add(e.value)
    return adlar


def _moduller() -> dict[Path, set[str]]:
    out: dict[Path, set[str]] = {}
    for p in sorted(SRC.rglob("*.py")):
        if p.name == "__init__.py":
            continue
        adlar = _genel_adlar(p)
        if adlar:
            out[p] = adlar
    return out


def _uretim_metinleri() -> dict[Path, str]:
    m: dict[Path, str] = {}
    for kok in (REPO / "src", REPO / "scripts"):
        if not kok.is_dir():
            continue
        for p in sorted(kok.rglob("*.py")):
            m[p] = p.read_text(encoding="utf-8")
    return m


def _modul_adi(p: Path) -> str:
    return ".".join(p.relative_to(SRC.parent).with_suffix("").parts)


def _baglanmamislari_bul() -> set[str]:
    moduller = _moduller()
    metinler = _uretim_metinleri()
    bulunan: set[str] = set()
    for p, adlar in moduller.items():
        gecti = False
        # (a) genel adlardan biri baska bir uretim dosyasinda geciyor mu
        for ad in adlar:
            d = re.compile(rf"\b{re.escape(ad)}\b")
            if any(d.search(m) for q, m in metinler.items() if q != p):
                gecti = True
                break
        # (b) modulun KENDI adi (import yolu) geciyor mu
        if not gecti:
            d = re.compile(rf"\b{re.escape(p.stem)}\b")
            if any(d.search(m) for q, m in metinler.items() if q != p):
                gecti = True
        if not gecti:
            bulunan.add(_modul_adi(p))
    return bulunan


def test_BOSLUK_moduller_ve_metinler_bulunuyor() -> None:
    """BOŞLUK KONTROLÜ (ADR-0040): dosya yoksa sınav boş doğru sınar."""
    assert SRC.is_dir(), f"kaynak agaci yok: {SRC}"
    assert len(_moduller()) >= 50, f"beklenenden az modul: {len(_moduller())}"
    assert len(_uretim_metinleri()) >= 150


def test_BOSLUK_defterdeki_moduller_GERCEKTEN_var() -> None:
    """Defterde var olmayan bir modül dururken sınav yeşil kalmasın."""
    adlar = {_modul_adi(p) for p in _moduller()}
    hayalet = sorted(BAGLANMAMIS - adlar)
    assert not hayalet, (
        f"defterde var OLMAYAN modul: {hayalet} -- yeniden adlandirildiysa "
        f"defteri guncelle")


def test_YENI_baglanmamis_modul_EKLENMEDI() -> None:
    """A116'nın çaresi: liste **büyümesin**."""
    yeni = sorted(_baglanmamislari_bul() - BAGLANMAMIS)
    assert not yeni, (
        f"{len(yeni)} YENI baglanmamis modul: {yeni}\n"
        f"A116'nin deseni: yazilmis, sinavlanmis, URETIME BAGLANMAMIS. "
        f"Ya cagri yerine bagla, ya da BAGLANMAMIS defterine gerekcesiyle "
        f"ekle.")


def test_baglanan_modul_defterden_CIKARILSIN() -> None:
    """Borç kapandıysa defter de kapanmalı — eskimiş kayıt bırakmaz."""
    hala = _baglanmamislari_bul()
    kapanan = sorted(BAGLANMAMIS - hala)
    assert not kapanan, (
        f"su moduller artik BAGLI: {kapanan} -- BAGLANMAMIS defterinden "
        f"cikar (A116 kapanisa dogru gidiyor, kayit onu gostermeli)")
