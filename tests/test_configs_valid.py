"""Depoda gonderilen her ornek config GECERLI olmali ve motora BAGLANMALI.

Neden: `configs/p2_basalt.yaml` uzun sure gecersizdi ve kimse fark etmedi,
cunku CI yalnizca `p0_smoke.yaml`'i dogruluyordu. Kok neden PyYAML'in YAML 1.1
kurali: isaretsiz us (`2.67e10`) sayi degil STRING olarak ayristirilir; sema
`strict=True` oldugu icin reddedilir. `6.6743e-11` isaretli oldugu icin
gecmisti — bu yuzden hata kismi ve sessizdi.

Bu dosya iki ayri seyi sinar:
  1. Her config semadan geciyor mu (sozdizimi/tip).
  2. Config'teki degerler motora GERCEKTEN ulasiyor mu (ADR-0006). Yalnizca
     "gecerli" olmak yetmez; okunmayan bir alan sessiz sapma demektir.
"""

from pathlib import Path

import pytest
import yaml

from dartrift.config import load_config

CONFIG_DIR = Path(__file__).resolve().parents[1] / "configs"
SHIPPED = sorted(CONFIG_DIR.glob("*.yaml"))


def test_shipped_configs_found():
    """Glob bosalirsa asagidaki testler sessizce hicbir sey sinamaz."""
    assert len(SHIPPED) >= 3, [p.name for p in SHIPPED]


@pytest.mark.parametrize("path", SHIPPED, ids=lambda p: p.name)
def test_shipped_config_validates(path):
    cfg = load_config(path)
    assert cfg.run_id
    assert cfg.schema_version == 1


@pytest.mark.parametrize("path", SHIPPED, ids=lambda p: p.name)
def test_no_unsigned_exponent_in_shipped_config(path):
    """Kok nedeni dogrudan sabitle: isaretsiz us YAML 1.1'de string olur.

    Sema testi bunu zaten yakalar, ama hata mesaji ("Input should be a valid
    number") nedeni soylemez. Bu test dogrudan sucluyu gosterir.
    """
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    def walk(node, trail=""):
        if isinstance(node, dict):
            for k, v in node.items():
                yield from walk(v, f"{trail}.{k}" if trail else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{trail}[{i}]")
        elif isinstance(node, str):
            yield trail, node

    suspect = [
        (t, v) for t, v in walk(raw)
        if v and v[0].isdigit() and ("e" in v.lower()) and _looks_numeric(v)
    ]
    assert not suspect, (
        f"{path.name}: bilimsel gosterim STRING olarak ayrisiyor "
        f"(us isareti eksik): {suspect}"
    )


def _looks_numeric(s: str) -> bool:
    try:
        float(s)
    except ValueError:
        return False
    return True


@pytest.mark.parametrize(
    "name,check",
    [
        ("p1_sod.yaml", lambda c: c.physics.eos in ("ideal_gas", "linear", "tillotson")),
        ("p2_basalt.yaml", lambda c: c.physics.eos == "tillotson"),
    ],
)
def test_phase_config_reaches_engine(name, check):
    """ADR-0006: dogrulanan alan TUKETILIR — motor nesnesi config'i yansitmali."""
    from dartrift.cpu_reference.materials import MaterialParams

    cfg = load_config(CONFIG_DIR / name)
    assert check(cfg)
    mat = MaterialParams.from_config(cfg)
    assert mat.eos == cfg.physics.eos
    assert mat.density_method == cfg.physics.density_method


def test_p2_basalt_modules_actually_enabled():
    """p2_basalt FAZ 2'nin TAM kosusudur; modulleri kapali olsa test bos olurdu."""
    cfg = load_config(CONFIG_DIR / "p2_basalt.yaml")
    assert cfg.physics.strength.enabled
    assert cfg.physics.porosity.enabled
    assert cfg.physics.gravity.enabled
    assert cfg.physics.porosity.Ps > cfg.physics.porosity.Pe

    from dartrift.cpu_reference.materials import MaterialParams

    mat = MaterialParams.from_config(cfg)
    assert mat.strength.enabled and mat.porosity.enabled and mat.gravity.enabled
    assert mat.tillotson.A == pytest.approx(2.67e10)
    assert mat.porosity.Ps == pytest.approx(1.0e8)
