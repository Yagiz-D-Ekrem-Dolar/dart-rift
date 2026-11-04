"""`docs/onkayit/` altındaki **gerçek** mühürler sağlam mı?

2026-11-04'te ölçüldü: `tests/test_hera_tahmin.py` mühür özetini
sınıyordu — ama **kendi ürettiği geçici** bir kaydın özetini. Depoda
duran iki gerçek mührü (`uretim66`, `uretim96`) **hiçbir şey
doğrulamıyordu**.

Mühürün değeri "başkası doğrulayabilir" olmasına bağlıdır. Doğrulamayı
hiç koşmuyorsak, mühür bir iddiadan fazlası değil. Bu dosya onu her
sınav koşusunda doğrular.

İki ağırlık karıştırılmaz (`scripts/muhur_dogrula.py` ile aynı ayrım):

- **MÜHÜR BOZUK** — özet tutmuyor. Burada **sıfır tolerans**.
- **İZ EKSİK** — özet sağlam, gönderme yapılan dosya/commit depodan
  bulunamıyor. Kusurdur, mühürü geçersiz kılmaz; bilinen hâli
  aşağıda **sayılı** olarak çivilenmiştir ki artması fark edilsin.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from muhur_dogrula import govde_ozeti, kaydi_denetle  # noqa: E402

ONKAYIT = REPO / "docs" / "onkayit"
#: 2026-11-04'te OLCULEN iz eksikligi. Borc kaydi, onay degil:
#: spin kaydinin `havuz` alani `analiz/...` diyor (TRUBA calisma
#: alaninin yolu), deponun karsiligi `docs/sonuclar/...`. Muhur SAGLAM.
IZ_EKSIK_BEKLENEN = {
    # yol bayat (TRUBA alani) + `girdi_ozetleri` yok
    "ONKAYIT_HERA_SPIN_uretim96.json": 2,
    # yalniz `girdi_ozetleri` yok
    "ONKAYIT_HERA_KRATER_uretim66.json": 1,
}


def _kayitlar() -> list[Path]:
    return sorted(ONKAYIT.glob("*.json"))


def test_BOSLUK_muhurler_bulunuyor() -> None:
    """BOŞLUK KONTROLÜ (ADR-0040): kayıt yoksa sınav boş doğru sınar."""
    k = _kayitlar()
    assert len(k) >= 2, f"en az 2 muhurlu kayit bekleniyordu, {len(k)} var"
    for p in k:
        d = json.loads(p.read_text(encoding="utf-8"))
        assert isinstance(d.get("sha256"), str) and d["sha256"], p.name


@pytest.mark.parametrize("p", _kayitlar(), ids=lambda p: p.name)
def test_MUHUR_bozulmamis(p: Path) -> None:
    """Sıfır tolerans: özet tutmalı."""
    ihlal, _ = kaydi_denetle(p)
    assert not ihlal, f"{p.name} MUHUR BOZUK:\n  " + "\n  ".join(ihlal)


@pytest.mark.parametrize("p", _kayitlar(), ids=lambda p: p.name)
def test_IZ_eksikligi_BEKLENENDEN_fazla_degil(p: Path) -> None:
    """İz eksikliği **artmasın**; borç defteri gibi çivili."""
    _, iz = kaydi_denetle(p)
    beklenen = IZ_EKSIK_BEKLENEN.get(p.name, 0)
    assert len(iz) <= beklenen, (
        f"{p.name}: {len(iz)} iz bulgusu, beklenen en fazla {beklenen}\n  "
        + "\n  ".join(iz))
    if len(iz) < beklenen:
        pytest.fail(
            f"{p.name}: iz eksikligi KAPANMIS ({len(iz)} < {beklenen}) -- "
            f"IZ_EKSIK_BEKLENEN defterini guncelle")


def test_ozet_tarifi_UYDURULMADI() -> None:
    """Özet, üretici betiklerin tarifiyle **aynı** olmalı.

    Tarif: `json.dumps(kayit_sha_haric, ensure_ascii=False, indent=1,
    sort_keys=True)` -> `sha256`. İkinci bir tanım yanlış negatif
    üretirdi; bu sınav tarifin kaymadığını çiviler.
    """
    import hashlib
    for p in _kayitlar():
        kayit = json.loads(p.read_text(encoding="utf-8"))
        govde = json.dumps({k: v for k, v in kayit.items() if k != "sha256"},
                           ensure_ascii=False, indent=1, sort_keys=True)
        elle = hashlib.sha256(govde.encode("utf-8")).hexdigest()
        assert govde_ozeti(kayit) == elle == kayit["sha256"], p.name


def test_TEK_BAYT_degisirse_YAKALANIR(tmp_path: Path) -> None:
    """Boş iddia sınamadığının kanıtı: kurcalanan kayıt **düşmeli**."""
    kaynak = _kayitlar()[0]
    kayit = json.loads(kaynak.read_text(encoding="utf-8"))
    # Govdede TEK bir alan degistirilir, `sha256` AYNI birakilir.
    kayit["etiket"] = str(kayit.get("etiket", "")) + "x"
    hedef = tmp_path / kaynak.name
    hedef.write_text(json.dumps(kayit, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    ihlal, _ = kaydi_denetle(hedef)
    assert any("SHA-256 TUTMUYOR" in m for m in ihlal), ihlal


def test_sha256_alani_YOKSA_muhur_sayilmaz(tmp_path: Path) -> None:
    kayit = json.loads(_kayitlar()[0].read_text(encoding="utf-8"))
    kayit.pop("sha256")
    hedef = tmp_path / "sahte.json"
    hedef.write_text(json.dumps(kayit, ensure_ascii=False, indent=1),
                     encoding="utf-8")
    ihlal, _ = kaydi_denetle(hedef)
    assert any("muhur degil" in m for m in ihlal), ihlal


# ===================================================================
# `girdi_ozetleri`: bundan sonraki kayitlar girdi dosyalarinin ICERIK
# ozetini tasiyacak. Gecmisteki iki kayda eklenmez; bu sinavlar yeni
# uretici yolunun DOGRU hesapladigini civiler.
# ===================================================================

from hera_krater_onkayit import girdi_ozetleri  # noqa: E402


def test_girdi_ozeti_GERCEK_sha256_veriyor(tmp_path: Path) -> None:
    import hashlib
    f = tmp_path / "veri.csv"
    icerik = b"idx,beta\n0,3.14\n"
    f.write_bytes(icerik)
    o = girdi_ozetleri(f)
    assert o[str(f)] == hashlib.sha256(icerik).hexdigest()


def test_girdi_ozeti_TEK_BAYT_degisirse_degisiyor(tmp_path: Path) -> None:
    f = tmp_path / "veri.csv"
    f.write_bytes(b"idx,beta\n0,3.14\n")
    a = girdi_ozetleri(f)[str(f)]
    f.write_bytes(b"idx,beta\n0,3.15\n")
    b = girdi_ozetleri(f)[str(f)]
    assert a != b


def test_girdi_ozeti_okunamazsa_SESSIZ_gecmiyor(tmp_path: Path) -> None:
    """Sessiz varsayilan yok: okunamayan dosya `OKUNAMADI:` yazar."""
    yok = tmp_path / "olmayan.csv"
    o = girdi_ozetleri(yok)
    assert o[str(yok)].startswith("OKUNAMADI:"), o


def test_girdi_ozeti_None_atlanir(tmp_path: Path) -> None:
    f = tmp_path / "v.csv"
    f.write_bytes(b"x")
    o = girdi_ozetleri(f, None)
    assert list(o) == [str(f)]
