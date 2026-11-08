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
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "dartrift" if (REPO / "dartrift").is_dir() else REPO / "src" / "dartrift"

#: OLCULEN bagli-olmayan moduller. Borc kaydi, onay degil.
#:
#: 2026-11-04 (metin taramasiyla):
#:   dartrift.failure                      -> A120 (sartname DR-RIFT-P0 §6.2)
#:   dartrift.validation.adaptive_h_cost   -> measure_multilevel_waste, measure_neighbour_waste
#:   dartrift.validation.deposit_calibration -> build_piston_ic, run_calibration
#:
#: 2026-11-08 (A121: tarama AST'ye cevrildi, DORT modul ORTAYA CIKTI):
#:   dartrift.validation.coupling_conservation
#:   dartrift.validation.domain_coupling
#:   dartrift.validation.ensemble_cost
#:   dartrift.validation.variable_h
#:
#: Bu dordu YENI BORC DEGIL -- hep bagsizdilar, eski tarama goremiyordu.
#: Ornek: `variable_h`'nin src/ + scripts/ altindaki tek gecisi
#: `validation/kernel_margin.py`'nin 10. satirindaki BELGE CUMLESIDIR
#: ("Bu formul dort ayri modulde yaziliydi (`mass_ratio`, `variable_h`,
#: ...")  -- cagri degil. Dordu de yalniz `tests/` tarafindan
#: kullaniliyor; uretim yolundan cagrilmiyorlar.
BAGLANMAMIS = frozenset({
    "dartrift.failure",
    "dartrift.validation.adaptive_h_cost",
    "dartrift.validation.deposit_calibration",
    "dartrift.validation.coupling_conservation",
    "dartrift.validation.domain_coupling",
    "dartrift.validation.ensemble_cost",
    "dartrift.validation.variable_h",
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


def _uretim_kullanimlari() -> dict[Path, tuple[set[str], set[str]]]:
    """Her üretim dosyasının **gerçekten kullandığı** adlar ve import yolları.

    ## Niçin metin değil AST (A121, 2026-11-08)

    Eski hâli dosyaları **düz metin** olarak tarıyor ve modül adını
    `re.search` ile arıyordu. Sonuç: bir **belge cümlesi** bağlantı
    sayılıyordu. `inference/ic_ice_tasarim.py`'nin 3. satırındaki

        Çok doğruluklu vekil (`cok_dogruluk`, Kennedy–O'Hagan AR(1)) ince

    cümlesi yüzünden `cok_dogruluk` "bağlı" göründü ve A116'nın **baş
    örneği** kendi sınavından kaçtı; modül bir ay boyunca hiçbir üretim
    yolundan çağrılmadan kaldı.

    AST'de yorumlar hiç yoktur, belge dizgileri ise `Constant`'tır —
    `Name`/`Attribute`/`Import` düğümlerine bakmak ikisini de
    kendiliğinden eler. Aranan şey artık ad geçişi değil **kullanım**.
    """
    out: dict[Path, tuple[set[str], set[str]]] = {}
    for kok in (REPO / "src", REPO / "scripts"):
        if not kok.is_dir():
            continue
        for p in sorted(kok.rglob("*.py")):
            try:
                agac = ast.parse(p.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            adlar: set[str] = set()
            yollar: set[str] = set()
            for n in ast.walk(agac):
                if isinstance(n, ast.Import):
                    for a in n.names:
                        yollar.update(a.name.split("."))
                elif isinstance(n, ast.ImportFrom):
                    if n.module:
                        yollar.update(n.module.split("."))
                    for a in n.names:
                        adlar.add(a.name)
                        yollar.add(a.name)
                elif isinstance(n, ast.Name):
                    adlar.add(n.id)
                elif isinstance(n, ast.Attribute):
                    adlar.add(n.attr)
            out[p] = (adlar, yollar)
    return out


def _modul_adi(p: Path) -> str:
    return ".".join(p.relative_to(SRC.parent).with_suffix("").parts)


def _baglanmamislari_bul() -> set[str]:
    """Hiçbir üretim dosyasının **gerçekten kullanmadığı** modüller.

    Ölçüt ad **geçişi** değil **kullanım**: ya modülün genel adlarından
    biri başka bir dosyada `Name`/`Attribute`/`import` olarak geçer, ya
    da modülün kendi adı bir `import` yolunda bulunur. Belge dizgileri
    ve yorumlar AST'de bu düğümler olarak görünmediği için sayılmaz
    (A121'in kapattığı delik).
    """
    moduller = _moduller()
    kullanim = _uretim_kullanimlari()
    bulunan: set[str] = set()
    for p, adlar in moduller.items():
        gecti = False
        for q, (q_adlar, q_yollar) in kullanim.items():
            if q == p:
                continue
            if adlar & (q_adlar | q_yollar):      # (a) genel ad kullanildi
                gecti = True
                break
            if p.stem in q_yollar:                 # (b) modul import edildi
                gecti = True
                break
        if not gecti:
            bulunan.add(_modul_adi(p))
    return bulunan


def test_BOSLUK_moduller_ve_metinler_bulunuyor() -> None:
    """BOŞLUK KONTROLÜ (ADR-0040): dosya yoksa sınav boş doğru sınar."""
    assert SRC.is_dir(), f"kaynak agaci yok: {SRC}"
    assert len(_moduller()) >= 50, f"beklenenden az modul: {len(_moduller())}"
    assert len(_uretim_kullanimlari()) >= 150


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
