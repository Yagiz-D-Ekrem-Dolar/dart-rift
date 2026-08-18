"""Kirmizi-takim kontrol listesi kosucusu — DR-RIFT-P0 §12 + DR-RIFT-P3 §10.

Yol Haritasi §7.5: "Her fazin kirmizi-takim kontrol listesi teslimden once
isletilir." Kapi kosucusundan (run_g0_gate.py) ayridir: kapi "gereksinimler
karsilandi mi" diye sorar, kirmizi takim "bu sistemi nasil kandirabilirim"
diye sorar.

RT1-RT6 FAZ 0 maddeleridir (determinizm, config, manifest, sessiz yutma).
RT15 FAZ 4 maddesidir (K21: EOS'ta sessiz NaN).
RT7-RT12 FAZ 3 maddeleridir ve hepsi GERCEKTEN OLCULMUS bir kusurdan
turemistir — varsayimsal senaryo degil:
  RT7  blok doyma bayragi      <- olculen: hedef 0.30, gerceklesen 0.263
  RT8  nokta mermi yasagi      <- P3-FR-06 acik yasak
  RT9  kuresel/yerel ayrimi    <- olculen: cukursuz kurede 41 m hayali krater
  RT10 beta tanim duyarliligi  <- tek sayi, kesin olmayani kesin gostermek
  RT11 settling iddiasi        <- KE zaten sifirdi; settling dusurmedi
  RT12 PDS manifesto eksigi    <- FAZ 0'da verilen soz tutulamadi
  RT13 sahne karmasi referansi <- olculen: karma iki makinede TUTMUYORDU
  RT14 kosede normal kararli mi<- olculen: normal makineye gore 2.5 derece
                                  oynuyordu (ADR-0025)

Kullanim:
    python scripts/run_red_team.py [--run-dir DIZIN]

Cikis kodu 0 = bes madde de temiz.
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tests"))

from golden_scenario import build_canonical_state, state_hash  # noqa: E402

from dartrift.config import ConfigError, config_hash, load_config  # noqa: E402
from dartrift.invariants import InvariantViolation, check_invariants  # noqa: E402
from dartrift.io_hdf5 import Hdf5Writer, LayerDisabledError  # noqa: E402
from dartrift.logging_cfg import (  # noqa: E402
    build_manifest,
    config_from_manifest,
    read_manifest,
    write_manifest,
)
from dartrift.particles import ParticleStore  # noqa: E402
from dartrift.rng import sample_uniform, sample_uniform_sharded  # noqa: E402

GOLDEN = REPO / "tests" / "golden" / "p0_canonical_v1.json"


class Check:
    def __init__(self, cid: str, question: str):
        self.cid, self.question = cid, question
        self.clean: bool | None = None
        self.evidence = ""

    def record(self, clean: bool, evidence: str) -> None:
        self.clean, self.evidence = clean, evidence


def rt1_cross_machine_hash() -> Check:
    """Ayni config + tohum iki farkli makinede ayni hash'i veriyor mu?"""
    c = Check("RT1", "Ayni config + tohum iki farkli makinede ayni hash'i veriyor mu?")
    golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
    current = state_hash(build_canonical_state())
    this_platform = f"{platform.system()}/CPython {platform.python_version()}"
    verified = golden.get("verified_on", [])
    matches = current == golden["sha256"]
    # Altin dosya baska bir platformda uretilmisti; bu kosu ikinci platformdur.
    others = [p for p in verified if p != this_platform]
    c.record(
        matches and bool(others),
        f"bu platform={this_platform}, hash={'ESLESTI' if matches else 'SAPTI'}; "
        f"daha once dogrulanan platformlar={verified or 'kayit yok'}",
    )
    return c


def rt2_shard_invariance() -> Check:
    """Shard sayisini degistirmek sonucu degistiriyor mu? (Degistirmemeli.)"""
    c = Check("RT2", "Shard sayisini degistirmek sonucu degistiriyor mu?")
    ref = sample_uniform(104729, "particles", 257)
    bad = []
    for n_shards in (1, 2, 3, 4, 5, 8, 16, 64, 257):
        got = sample_uniform_sharded(104729, "particles", 257, n_shards)
        if not np.array_equal(ref, got):
            bad.append(n_shards)
    c.record(not bad, f"denenen shard sayilari 1..257 (9 vaka); sapan={bad or 'yok'}")
    return c


def rt3_invalid_configs_rejected() -> Check:
    """Gecersiz her config gercekten reddediliyor mu, sessizce yutulmuyor mu?"""
    c = Check("RT3", "Gecersiz her config gercekten reddediliyor mu?")
    files = sorted((REPO / "configs" / "invalid").glob("*.yaml"))
    slipped = []
    for f in files:
        try:
            load_config(f)
            slipped.append(f.name)  # kabul edildiyse sema delinmis demektir
        except ConfigError:
            pass
    c.record(
        not slipped and len(files) >= 10,
        f"{len(files)} gecersiz vaka denendi; sessizce kabul edilen={slipped or 'yok'}",
    )
    return c


def rt4_manifest_reproduces_run(run_dir: Path) -> Check:
    """Manifest, kosuyu sifirdan yeniden uretmeye yetiyor mu?"""
    c = Check("RT4", "Manifest, kosuyu sifirdan yeniden uretmeye yetiyor mu?")
    cfg = load_config(REPO / "configs" / "p0_smoke.yaml")
    manifest = build_manifest(cfg, status="accepted", wall_time=0.0)
    path = write_manifest(manifest, run_dir / "rt4_manifest.yaml")

    # Orijinal YAML'a hic bakmadan, yalnizca manifestten geri kur:
    recovered = config_from_manifest(read_manifest(path))
    same_hash = config_hash(recovered) == config_hash(cfg)

    # Geri kurulan config gercekten ayni motoru kuruyor mu?
    same_store = (
        ParticleStore.from_config(recovered, 4).precision
        == ParticleStore.from_config(cfg, 4).precision
    )

    # Kurcalama tespiti calisiyor mu?
    tampered = read_manifest(path)
    tampered["config"]["random_seed"] += 1
    try:
        config_from_manifest(tampered)
        detects_tamper = False
    except ValueError:
        detects_tamper = True

    c.record(
        same_hash and same_store and detects_tamper,
        f"config manifestten geri kuruldu (hash {'ayni' if same_hash else 'FARKLI'}), "
        f"ayni depo modu={same_store}, kurcalama tespiti={detects_tamper}",
    )
    return c


def rt5_violation_halts_run() -> Check:
    """Bir invariant ihlali kosuyu durduruyor mu, yoksa devam mi ediyor?"""
    c = Check("RT5", "Bir invariant ihlali kosuyu durduruyor mu?")
    results = []
    injections = [
        ("rho", np.nan), ("rho", -1.0), ("mass", 0.0),
        ("D", 2.0), ("alpha_por", 0.5), ("u", np.inf),
    ]
    for field, value in injections:
        store = ParticleStore(8, "science")
        store.rho[:] = 2600.0
        store.mass[:] = 1.0
        store.as_dict()[field][3] = value
        try:
            check_invariants(store, step=1, level="science")
            results.append(f"{field}={value} KACTI")  # durdurmadiysa kusur
        except InvariantViolation:
            pass
    c.record(
        not results,
        f"{len(injections)} enjeksiyon denendi; yakalanmayan={results or 'yok'}",
    )
    return c


def rt6_disabled_layer_not_silent(run_dir: Path) -> Check:
    """Ek madde: config'de kapatilan bir katmana yazmak sessizce yutuluyor mu?"""
    c = Check("RT6", "Kapatilmis cikti katmanina yazmak sessizce yutuluyor mu?")
    cfg = load_config(REPO / "configs" / "p0_smoke.yaml")
    narrow_io = cfg.io.model_copy(update={"output_layers": ["scalar_budget"]})
    narrowed = cfg.model_copy(update={"io": narrow_io})
    silent = False
    with Hdf5Writer.from_config(narrowed, run_dir / "rt6.h5") as w:
        try:
            w.append_event(0, 0.0, "kapali_katman")
            silent = True  # hata vermediyse sessizce yutmus demektir
        except LayerDisabledError:
            pass
    verdict = "SESSIZCE YUTULDU" if silent else "acik hata verdi"
    c.record(not silent, f"kapali katmana yazma {verdict}")
    return c


# ---------------------------------------------------------------------------
# FAZ 3 maddeleri (DR-RIFT-P3 §10) — sahne kurulumu nasil kandirilabilir?
# ---------------------------------------------------------------------------


def rt7_boulder_saturation_not_silent() -> Check:
    """Istenen blok kesrine ULASILAMAZSA sessizce dusuk kesir mi doner?"""
    c = Check("RT7", "Ulasilamayan blok kesri sessizce dusuk mu donuyor?")
    from dartrift.setup.rubble_generator import build_rubble_pile
    from dartrift.setup.shape_mesh import icosphere

    mesh = icosphere(3, 40.0)
    # fiziksel olarak sigmayacak bir kesir iste: doyma kacinilmaz
    pile = build_rubble_pile(mesh, spacing=6.0, bulk_density=1800.0, root_seed=5,
                              rho0_solid=2700.0,
                             model_class="M1", f_boulder=0.9, q=3.0,
                             r_min=12.0, r_max=30.0)
    # ADR-0034: blok kesri HACIM kesridir. Onceki hali KUTLE kesrini
    # olcuyordu; ADR-0030'dan sonra bloklar %65 daha agir oldugu icin
    # kutle kesri hacim kesrinden BUYUK cikar (olculen 0.3034 -> 0.4335).
    olculen = float(pile.boulder_volume_fraction)
    olculen_kutle = float(np.sum(pile.m[pile.is_boulder]) / np.sum(pile.m))
    bayrak = bool(pile.diagnostics.get("boulder_saturated", False))
    sessiz = (olculen < 0.85) and not bayrak
    c.record(
        not sessiz,
        f"istenen 0.90 (HACIM), olculen hacim {olculen:.3f} "
        f"(kutle kesri {olculen_kutle:.3f}), doyma bayragi "
        f"{'ACIK' if bayrak else 'KAPALI'} -> "
        f"{'SESSIZCE YUTULDU' if sessiz else 'raporlandi'}",
    )
    return c


def rt8_point_impactor_rejected() -> Check:
    """P3-FR-06 nokta parcacigi yasakliyor — kod gercekten reddediyor mu?"""
    c = Check("RT8", "Nokta mermi (N=1) sessizce kabul ediliyor mu?")
    from dartrift.setup.impactor import build_impactor

    kacan = []
    for n in (1, 2, 7):
        try:
            build_impactor(n)
            kacan.append(n)
        except ValueError:
            pass
    c.record(not kacan, f"denenen N=1,2,7; reddedilmeyen={kacan or 'yok'}")
    return c


def rt9_global_deformation_not_crater() -> Check:
    """Cisim TUMUYLE buzusurse krater cikarici bunu krater diye mi sayar?

    Bu, olculmus bir kusurdur: yon kutulari yetersiz orneklendiginde hicbir
    cukuru olmayan bir kurede 41 m'lik hayali krater raporlanmisti.
    """
    c = Check("RT9", "Kuresel buzusme ya da CISMIN SEKLI krater olarak mi sayiliyor?")
    from dartrift.observables.crater_shape import crater_profile
    from dartrift.validation.scene_checks import run_crater_irregular_selftest

    rng = np.random.default_rng(4)
    p = rng.normal(size=(30000, 3))
    p /= np.linalg.norm(p, axis=1)[:, None]
    x = 0.9 * p * (100.0 * rng.uniform(0.0, 1.0, 30000) ** (1.0 / 3.0))[:, None]
    cs = crater_profile(x, center=np.zeros(3),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        reference_radius=100.0, outer_angle_deg=60.0)
    hayali = abs(cs.depth) > 5.0
    # ONCEKI HALI YALNIZCA KUREYI SINIYORDU. Izotropik buzusme referansa
    # zaten girer; asil tehlike cismin KENDI seklidir. Dimorphos 88x87x65 m
    # ve kuresel referans varsayimiyla KRATERSIZ elipsoitte 9,04 m hayali
    # krater olculdu. Duzensiz cisim senaryosu artik sart.
    ir = run_crater_irregular_selftest()
    c.record(
        not hayali and ir["phantom_removed"] and ir["depth_rel_err_true_ref"] < 0.20
        and ir["spherical_flag_reported"] and ir["true_ref_flag_reported"],
        f"cukursuz %10 buzusmus kurede derinlik {cs.depth:.2f} m, kuresel degisim "
        f"{cs.global_radius_change:.2f} m; DUZENSIZ cisim (88x87x65 m): kuresel "
        f"referans kratersiz cisimde {ir['phantom_depth_spherical_ref']:.2f} m "
        f"HAYALI krater ve bilinen {ir['known_depth']:.0f} m cukuru "
        f"{ir['measured_depth_spherical_ref']:.2f} m gosteriyor; carpma oncesi "
        f"referansla hayali {ir['phantom_depth_true_ref']:.2e} m ve gercek olcum "
        f"{ir['measured_depth_true_ref']:.2f} m (hata "
        f"%{100 * ir['depth_rel_err_true_ref']:.1f})",
    )
    return c


def rt10_beta_definition_sensitivity_reported() -> Check:
    """beta tek sayi olarak mi sunuluyor, yoksa tanim duyarliligiyla mi?

    ONCEKI HALI YETERSIZDI: yalnizca TOPLAM yayilimin pozitif olmasina
    bakiyordu. Eksen basina olculunce hiz esigi ekseninin yayilimi TAM SIFIR
    cikti — tarama iki boyutlu gorunuyor, aslinda tek boyutta calisiyordu.
    O senaryoda en yavas ejekta 0,2 m/s, 2x kacis hizi 0,161 m/s; esik
    hicbir seyi eleyemiyordu. Kriter geciyordu ama hiz esigi kod yolu HIC
    kosulmamisti. Simdi HER IKI eksenin de bir yerde gercekten is gordugu
    ayri ayri kanitlanir.
    """
    c = Check("RT10", "beta duyarliligi iki eksende de GERCEKTEN olculuyor mu?")
    from dartrift.validation.scene_checks import (
        run_observable_selftest,
        run_speed_threshold_selftest,
    )

    r = run_observable_selftest()
    s = run_speed_threshold_selftest()
    yayilim = r["beta_relative_spread"]
    c.record(
        bool(r["sensitivity_reported"]) and yayilim > 0.0
        and bool(r["radius_axis_active"])          # yaricap ekseni: 1. senaryo
        and bool(s["speed_axis_active"])           # hiz ekseni: 2. senaryo
        and bool(s["beta_monotone_in_threshold"]),
        f"tarama yayilimi %{100 * yayilim:.2f} "
        f"[{r['beta_min']:.3f}, {r['beta_max']:.3f}]; yaricap ekseni "
        f"{r['beta_spread_radius_axis']:.4f}, hiz ekseni (1. senaryoda) "
        f"{r['beta_spread_speed_axis']:.4f} — hiz esigi orada OLU oldugu icin "
        f"ayri senaryoyla kanitlandi: yayilim {s['beta_spread_speed_axis']:.4f}, "
        f"beta {[round(b, 3) for b in s['beta_by_speed_factor']]} esikle monoton "
        f"azaliyor ({s['beta_monotone_in_threshold']})",
    )
    return c


def rt11_settling_claims_only_what_it_measured() -> Check:
    """Settling 'KE'yi dusurdum' diye mi sunuluyor, yoksa olculen gercek mi?

    Olculen gercek: baslangic durumu ZATEN denge (a_SPH = 0 tam olarak).
    Modulun kendi belgesi bunu soylemek zorunda; soylemiyorsa iddia sisirilmis
    demektir.
    """
    c = Check("RT11", "Settling, olcmedigi bir basariyi iddia ediyor mu?")
    import inspect

    from dartrift.setup import settling as S

    # ONCEKI HALI IKI SEKILDE ZAYIFTI:
    #  1. DIZE ESLESMESIYDI (RT12'nin duzeltilen gunahi),
    #  2. ucuncu anahtar KENDINI DOGRULUYORDU:
    #         "KAPSAM DISI" if "KAPSAM DISI" in doc else "hesaplanabilir"
    #     yani belgede varsa onu ariyordu — ASLA DUSEMEZDI.
    #
    # Yeni sinav DAVRANISSAL: bir iddia, onu DESTEKLEYEN OLCUMU dondurmedikce
    # gecerli sayilmaz. `settle_pile` "baslangic zaten dengede" diyorsa,
    # bunu kanitlayan tani alanlarini URETMEK zorundadir.
    src = inspect.getsource(S.settle_pile)
    gereken = ("a_sph_max_t0", "a_gravity_max_t0", "steps_per_free_fall",
               "ke_threshold", "converged")
    eksik_tani = [k for k in gereken if k not in src]

    # Ve `converged` SABIT True olmamali: yakinsamama yolu gercekten var mi?
    yakinsama_kosullu = ("converged=" in src or "converged =" in src) and (
        "ke_final" in src or "ke_thr" in src)

    # SettleResult varsayilani "basarisiz" olmali — sessizce "oldu" demez.
    varsayilan_kotumser = S.SettleResult(
        x=np.zeros((1, 3)), v=np.zeros((1, 3)), rho=np.ones(1),
        alpha=np.ones(1), n_steps=0, t_end=0.0).converged is False

    c.record(
        not eksik_tani and yakinsama_kosullu and varsayilan_kotumser,
        f"iddiayi destekleyen tanilar uretiliyor (eksik={eksik_tani or 'yok'}); "
        f"yakinsama KOSULLU={yakinsama_kosullu}; "
        f"SettleResult varsayilani converged=False: {varsayilan_kotumser}",
    )
    return c


def rt12_data_manifest_gap_not_hidden() -> Check:
    """Eksik/bozuk bir veri manifestosu 'gecti' diye sayilir mi?

    DAVRANIS sinavi, dize eslesmesi DEGIL. Onceki surum `run_g3_gate.py`
    icinde "unprovable" ve README'de "KANITLANAMADI" gecip gecmedigine
    bakiyordu. C7 gercekten kapandiktan sonra README'de o kelime yalnizca
    TARIHSEL bir notta kaldi ve madde TESADUFEN gecmeye basladi — rastlantiyla
    gecen bir kirmizi takim maddesi hic olmamasindan kotudur.

    Simdi kapinin denetleyicisi UC senaryoda dogrudan calistiriliyor:
      (a) bos dizin           -> gecmemeli
      (b) saglamasiz urun     -> gecmemeli
      (c) bozuk SHA-256       -> gecmemeli
    """
    import importlib.util
    import shutil
    import tempfile

    c = Check("RT12", "Eksik/bozuk PDS manifestosu gecmis sayiliyor mu?")
    spec = importlib.util.spec_from_file_location(
        "_g3", REPO / "scripts" / "run_g3_gate.py")
    g3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g3)

    gercek_man = REPO / "data_manifest"
    yedek = tempfile.mkdtemp(prefix="rt12_")
    kotu = []
    try:
        for f in gercek_man.glob("*.json"):
            shutil.move(str(f), yedek)

        with tempfile.TemporaryDirectory() as rd:
            # (a) manifest yok
            ok, _ = g3._data_manifest_status(Path(rd))
            if ok:
                kotu.append("bos dizin GECTI")

            # (b) saglamasiz urun
            (gercek_man / "_rt12.json").write_text(json.dumps(
                {"bundle": "x", "products": [{"product_id": "p", "filename": "f",
                                              "bytes": 1}]}), encoding="utf-8")
            ok, _ = g3._data_manifest_status(Path(rd))
            if ok:
                kotu.append("saglamasiz urun GECTI")

            # (c) dosya var ama SHA-256 tutmuyor
            veri = Path(rd) / "veri"
            veri.mkdir()
            (veri / "f").write_bytes(b"gercek icerik")
            (gercek_man / "_rt12.json").write_text(json.dumps(
                {"bundle": "x", "data_root": str(veri),
                 "products": [{"product_id": "p", "filename": "f",
                               "sha256": "0" * 64, "md5_verified": True,
                               "bytes": 13}]}), encoding="utf-8")
            ok, ev = g3._data_manifest_status(Path(rd))
            if ok:
                kotu.append("bozuk SHA-256 GECTI")
            elif "UYUSMAYAN" not in ev:
                kotu.append("bozuk SHA-256 raporlanmadi")
    finally:
        (gercek_man / "_rt12.json").unlink(missing_ok=True)
        for f in Path(yedek).glob("*.json"):
            shutil.move(str(f), gercek_man)
        shutil.rmtree(yedek, ignore_errors=True)

    c.record(
        not kotu,
        "uc senaryo da reddedildi (manifest yok / saglamasiz urun / bozuk "
        "SHA-256); denetleyici davranissal olarak dogrulandi"
        if not kotu else f"KUSUR: {kotu}",
    )
    return c


def rt13_scene_determinism_is_cross_machine() -> Check:
    """Sahne karmasi TEK makinede mi dogrulaniyor, yoksa makineler arasi mi?

    Bu madde bir kusurdan dogdu (ADR-0025): `Scene.digest` G3'te "determinizm
    kaniti" diye sunuluyordu ama referansi yoktu; "ayni makinede iki kez ayni"
    sinaniyordu. O bosluk iki gercek kusuru tasidi — isin-yuzey dejenereligi
    (normal 2.5 derece kayiyordu) ve centroid toplama sirasi.
    """
    c = Check("RT13", "Sahne determinizmi yalnizca tek makinede mi dogrulanmis?")
    golden = REPO / "tests" / "golden" / "p3_scene_v1.json"
    if not golden.is_file():
        c.record(False, f"altin sahne dosyasi yok: {golden}")
        return c
    g = json.loads(golden.read_text(encoding="utf-8"))
    plats = g.get("verified_on", [])
    isletim = {p.split("/")[0] for p in plats}
    numpylar = {p.split("numpy ")[-1] for p in plats if "numpy " in p}

    from dartrift.setup.scene import build_scene

    p = g["params"]
    s = build_scene(
        shape=p["shape"], radius=p["radius"], subdiv=p["subdiv"],
        spacing=p["spacing"], bulk_density=p["bulk_density"],
        n_impactor=p["n_impactor"], model_class=p["model_class"],
        f_boulder=p["f_boulder"], q=p["q"], r_min=p["r_min"], r_max=p["r_max"],
        root_seed=g["seed"])
    esles = s.digest == g["sha256"]
    c.record(
        esles and len(isletim) >= 2 and len(numpylar) >= 2,
        f"karma {'ESLESTI' if esles else 'SAPTI'}; kayitli platformlar="
        f"{plats or 'yok'} (isletim sistemi={len(isletim)}, numpy={len(numpylar)})",
    )
    return c


def rt14_ray_degeneracy_normal_is_stable() -> Check:
    """Mesh kosesinden gecen isin, faset secimine bagli bir normal mi veriyor?"""
    c = Check("RT14", "Kosede yuzey normali faset secimine gore oynuyor mu?")
    from dartrift.setup.impactor import impact_geometry
    from dartrift.setup.shape_mesh import icosphere

    kotu = []
    for subdiv in (2, 3, 4, 5):
        g = impact_geometry(icosphere(subdiv, 82.0), np.array([0.0, 0.0, 1.0]))
        sapma = float(np.hypot(g.normal[0], g.normal[1]))
        if sapma > 1.0e-15:
            kotu.append((subdiv, sapma))
    c.record(
        not kotu,
        "kure kutbunda normal tam +z (tum bolunmelerde tegetsel bilesen < 1e-15)"
        if not kotu else f"tegetsel bilesen sifirdan buyuk: {kotu}",
    )
    return c

def rt15_eos_sessiz_nan_uretmiyor() -> Check:
    """K21: Tillotson genlesmis-sicak kolda rho <= 0 -> NaN, GPU'da SESSIZ.

    Bulunus: FAZ 4 E2 olcumunde "overflow encountered in exp". Us
    -beta*(1/eta - 1)'dir; eta kucuk NEGATIF iken us buyuk POZITIF olur,
    exp TASAR ve inf*0 = NaN verir. NaN her komsu toplamina yayilir.
    GPU'da RuntimeWarning YOKTUR — bir uretim kosusu bastan sona NaN uretip
    "bitti" diyebilirdi.

    Kusur ARALIKSIZ DEGILDI: yalnizca rho'nun sifira yakin NEGATIF oldugu
    DAR bir bantta. Rastgele bir sinamayla kolayca kacirilirdi.

    Bu madde iki seyi birden sorar:
      1) EOS TOPLAM mi (sonlu girdi -> sonlu cikti)?
      2) rho <= 0 MASKELENMIYOR mu (defter sayiyor mu)?
    Ikincisi olmadan birincisi bir kusuru GIZLEMEK olurdu.
    """
    import numpy as np

    from dartrift.cpu_reference.materials import MaterialParams, tillotson_pressure
    from dartrift.cpu_reference.solid_ref import SolidState, budgets_solid

    c = Check("RT15", "EOS sessiz NaN uretmiyor; rho<=0 deftere isleniyor")
    tp = MaterialParams(eos="tillotson").tillotson

    # 1) TOPLAM MI — kusurun bulundugu DAR BANT dahil
    rho = np.array([-1.0e-12, -1.0e-9, -0.27, -27.0, -2700.0, 0.0, 1.0e-9])
    sonlu = []
    for carp in (0.0, 0.5, 1.0, 2.0, 10.0):
        P = tillotson_pressure(rho, np.full(rho.shape, tp.u_cv * carp), tp)
        sonlu.append(bool(np.all(np.isfinite(P))))
    hepsi_sonlu = all(sonlu)

    # 2) MASKELENMIYOR MU — defter sayiyor mu
    n = 8
    st = SolidState(x=np.zeros((n, 3)), v=np.zeros((n, 3)), m=np.ones(n),
                    u=np.zeros(n), h=1.0, active=np.ones(n, bool),
                    alpha=np.ones(n), rho=np.full(n, 2700.0))
    temiz = budgets_solid(st)
    st.rho[3] = -1.0
    st.rho[5] = 0.0
    bozuk = budgets_solid(st)
    sayiyor = (temiz["nonpositive_density_count"] == 0
               and bozuk["nonpositive_density_count"] == 2
               and bozuk["rho_min"] == -1.0)

    # 3) BOSLUK KONTROLU — bayrak SABIT True olmasin
    st2 = SolidState(x=np.zeros((n, 3)), v=np.zeros((n, 3)), m=np.ones(n),
                     u=np.zeros(n), h=1.0, active=np.ones(n, bool),
                     alpha=np.ones(n), rho=np.full(n, 2700.0))
    once = budgets_solid(st2)["state_is_finite"]
    st2.rho[2] = np.nan
    sonra = budgets_solid(st2)["state_is_finite"]
    dusebiliyor = (once is True and sonra is False)

    c.record(
        hepsi_sonlu and sayiyor and dusebiliyor,
        f"EOS toplam mi: {hepsi_sonlu} (5 enerji x 7 yogunluk, dar bant dahil); "
        f"defter rho<=0 sayiyor: {sayiyor} "
        f"(temiz {temiz['nonpositive_density_count']}, bozuk "
        f"{bozuk['nonpositive_density_count']}, rho_min {bozuk['rho_min']}); "
        f"state_is_finite DUSEBILIYOR: {dusebiliyor}",
    )
    return c




def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-dir", default=None)
    args = ap.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.run_dir) if args.run_dir else REPO / "gate_runs" / f"redteam_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    checks = [
        rt1_cross_machine_hash(),
        rt2_shard_invariance(),
        rt3_invalid_configs_rejected(),
        rt4_manifest_reproduces_run(run_dir),
        rt5_violation_halts_run(),
        rt6_disabled_layer_not_silent(run_dir),
        rt7_boulder_saturation_not_silent(),
        rt8_point_impactor_rejected(),
        rt9_global_deformation_not_crater(),
        rt10_beta_definition_sensitivity_reported(),
        rt11_settling_claims_only_what_it_measured(),
        rt12_data_manifest_gap_not_hidden(),
        rt13_scene_determinism_is_cross_machine(),
        rt14_ray_degeneracy_normal_is_stable(),
        rt15_eos_sessiz_nan_uretmiyor(),
    ]
    all_clean = all(c.clean for c in checks)

    lines = [
        "# Kirmizi-Takim Kontrol Listesi — FAZ 0 §12 + FAZ 3 §10",
        "",
        f"- Tarih (UTC): {datetime.now(timezone.utc).isoformat()}",
        f"- Makine: {platform.node()} / {platform.platform()}",
        f"- Python: {platform.python_version()}",
        "",
        "| # | Soru | Sonuc | Kanit |",
        "|---|------|-------|-------|",
    ]
    for c in checks:
        verdict = "TEMIZ" if c.clean else "KUSUR"
        lines.append(f"| {c.cid} | {c.question} | **{verdict}** | {c.evidence} |")
    summary = "Tum maddeler temiz" if all_clean else "EN AZ BIR KUSUR VAR — teslim edilemez"
    lines += [
        "",
        f"## SONUC: {summary}",
        "",
        "> Kirmizi takim, gereksinimleri degil sistemin kandirilabilirligini sinar.",
    ]
    (run_dir / "red_team_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if all_clean else 1


if __name__ == "__main__":
    raise SystemExit(main())
