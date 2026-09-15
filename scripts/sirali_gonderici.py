"""Sıralı gönderici — ortak TRUBA hesabında aynı anda en fazla 8 GPU, kuyrukta yığın yok.

TRUBA hesabı ortak kullanılıyor. Kurallar (kullanıcı, 2026-09-15):

1. Kullanıcının kuyruğundaki **çalışan + bekleyen** işlerin GPU toplamı
   `AZAMI_GPU` (8) sınırını hiç aşmaz. Bekleyenler de sayılır, böylece
   kuyrukta asla sınırın ötesinde iş beklemez (`%N` kısıtlı dizi bile
   bekleyen görev bıraktığı için kullanılmaz; her dizi görevi tek tek
   `--array=<i>` ile gönderilir).
2. Adımlar sırayla ilerler: `sonra` alanı yoksa adım, plandaki bir önceki
   adım **tamamen BİTTİ** olmadan gönderilmez. `"sonra": []` bağımsız
   adımdır (boş yuvayı doldurabilir), `"sonra": ["Mt"]` açık bağımlılıktır.
3. Bir adımda HATA'lı görev varsa ona bağlı adımlar gönderilmez (DURDU);
   görev kendiliğinden yeniden gönderilmez, insan bakar.
4. A84: `export` değerinde virgül varsa gönderim reddedilir.

Betik uzun süre açık kalmaz (giriş düğümünde artalan süreci yok): her
çağrı bir adım atar — kuyruğu okur, durumu günceller, boş yuva kadar
görev gönderir ve çıkar. Gönderimleri `--kuru` ile önce görmek mümkün.

Plan (JSON):
    {"adimlar": [
      {"ad": "Mt", "betik": "truba/is_Mt_plato.slurm", "gorevler": [8, 9, 10],
       "gpu": 1, "export": {"LAD": "kaba"}},
      {"ad": "U", "betik": "truba/is_U_model.slurm", "gorevler": [0, 1]},
      {"ad": "D", "betik": "truba/is_D_dart.slurm", "gorevler": null, "sonra": ["Mt", "U"]}
    ]}

Kullanim (TRUBA, depo kökünde):
    python scripts/sirali_gonderici.py adim --plan truba/sira.json --durum kampanya/SIRA.json --kuru
    python scripts/sirali_gonderici.py adim --plan truba/sira.json --durum kampanya/SIRA.json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path

AZAMI_GPU = 8
BITTI_DURUMLARI = {"COMPLETED"}
HATA_DURUMLARI = {"FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL",
                  "PREEMPTED", "BOOT_FAIL", "DEADLINE"}
_GPU = re.compile(r"gpu(?::[A-Za-z0-9_.-]+)?[:=](\d+)")


def gpu_sayisi(gres: str) -> int:
    """`squeue %b` alanından GPU sayısı: 'gres:gpu:1', 'gres/gpu:a100:2', 'N/A'."""
    m = _GPU.search(gres or "")
    return int(m.group(1)) if m else 0


def kuyruk_gpu(squeue_satirlari: list[str]) -> int:
    """`squeue -r -h -o "%i %T %b"` satırlarından çalışan+bekleyen GPU toplamı.

    `-r` her dizi görevini ayrı satır yapar; yine de sıkıştırılmış
    `123_[4-9]` gelirse görev sayısıyla çarpılır (sayım eksik kalmasın).
    """
    top = 0
    for s in squeue_satirlari:
        p = s.split()
        if len(p) < 2:
            continue
        # COMPLETING da sayilir: GPU'yu hala tutuyor (ortak hesapta guvenli taraf)
        if p[1] not in ("RUNNING", "PENDING", "CONFIGURING", "COMPLETING", "REQUEUED",
                        "SUSPENDED", "R", "PD", "CF", "CG", "RQ", "S"):
            continue
        top += gpu_sayisi(p[2] if len(p) > 2 else "") * _dizi_gorev_sayisi(p[0])
    return top


def _dizi_gorev_sayisi(is_kimligi: str) -> int:
    m = re.search(r"_\[([^\]]+)\]", is_kimligi)
    if not m:
        return 1
    n = 0
    for parca in m.group(1).split("%")[0].split(","):
        if "-" in parca:
            a, b = parca.split("-")
            n += int(b) - int(a) + 1
        elif parca:
            n += 1
    return n


def _gorevler(adim: dict) -> list:
    g = adim.get("gorevler")
    return [None] if g is None else list(g)


def _anahtar(adim: dict, gorev) -> str:
    return adim["ad"] if gorev is None else f"{adim['ad']}:{gorev}"


def plani_denetle(plan: dict) -> None:
    adlar = [a["ad"] for a in plan["adimlar"]]
    if len(set(adlar)) != len(adlar):
        raise ValueError("adim adlari benzersiz olmali")
    for i, a in enumerate(plan["adimlar"]):
        for b in a.get("sonra", []):
            if b not in adlar[:i]:
                raise ValueError(f"{a['ad']}: 'sonra' {b} plandaki ONCEKI bir adim degil")
        for k, v in a.get("export", {}).items():
            if "," in str(v) or "," in str(k):
                raise ValueError(f"{a['ad']}: export {k} virgul iceriyor (A84); '+' kullan")
        if int(a.get("gpu", 1)) > AZAMI_GPU:
            raise ValueError(f"{a['ad']}: gorev basina gpu > {AZAMI_GPU}")


def adim_durumu(plan: dict, durum: dict, ad: str) -> str:
    """BITTI | HATA | SURUYOR | BASLAMADI."""
    adim = next(a for a in plan["adimlar"] if a["ad"] == ad)
    ds = [durum.get(_anahtar(adim, g), {}).get("durum") for g in _gorevler(adim)]
    if all(d == "BITTI" for d in ds):
        return "BITTI"
    if any(d == "HATA" for d in ds):
        return "HATA"
    if any(d is not None for d in ds):
        return "SURUYOR"
    return "BASLAMADI"


def _bagimliliklar(plan: dict, i: int) -> list[str]:
    a = plan["adimlar"][i]
    if "sonra" in a:
        return list(a["sonra"])
    return [plan["adimlar"][i - 1]["ad"]] if i > 0 else []


def secim(plan: dict, durum: dict, kullanilan_gpu: int, azami: int = AZAMI_GPU) -> dict:
    """Bu çağrıda gönderilecek görevler (saf fonksiyon, yan etkisiz)."""
    plani_denetle(plan)
    bos = azami - kullanilan_gpu
    secilen, bekleyen, duran = [], [], []
    for i, a in enumerate(plan["adimlar"]):
        bag = _bagimliliklar(plan, i)
        bag_durum = {b: adim_durumu(plan, durum, b) for b in bag}
        if any(d == "HATA" for d in bag_durum.values()):
            duran.append(a["ad"])
            continue
        if any(d != "BITTI" for d in bag_durum.values()):
            bekleyen.append(a["ad"])
            continue
        gpu = int(a.get("gpu", 1))
        for g in _gorevler(a):
            if _anahtar(a, g) in durum:
                continue
            if gpu > bos:
                break
            secilen.append((a, g))
            bos -= gpu
    return {"secilen": secilen, "bekleyen_adim": bekleyen, "duran_adim": duran,
            "bos_gpu_sonra": bos}


def sbatch_komutu(adim: dict, gorev) -> list[str]:
    k = ["sbatch", "--parsable"]
    if gorev is not None:
        k.append(f"--array={int(gorev)}")
    ex = adim.get("export")
    if ex:
        k.append("--export=ALL," + ",".join(f"{a}={v}" for a, v in ex.items()))
    k.append(adim["betik"])
    return k


def durumu_guncelle(durum: dict, sacct: dict[str, str]) -> dict:
    """`sacct` durumlarını (`is_kimligi -> STATE`) göreve işler. Yeni sözlük döner."""
    yeni = {k: dict(v) for k, v in durum.items()}
    for v in yeni.values():
        if v.get("durum") in ("BITTI", "HATA"):
            continue
        st = sacct.get(v["is"], "").split()[0] if sacct.get(v["is"]) else ""
        if st in BITTI_DURUMLARI:
            v["durum"] = "BITTI"
        elif st in HATA_DURUMLARI:
            v["durum"] = "HATA"
            v["slurm"] = st
    return yeni


def _is_kimligi(parsable: str, gorev) -> str:
    j = parsable.strip().split(";")[0]
    return j if gorev is None or "_" in j else f"{j}_{int(gorev)}"


def _calistir(k: list[str]) -> str:
    return subprocess.run(k, check=True, capture_output=True, text=True).stdout


def adim_at(plan: dict, durum_yolu: Path, *, kuru: bool, calistir=_calistir,
            kullanici: str | None = None) -> dict:
    durum = json.loads(durum_yolu.read_text(encoding="utf-8")) if durum_yolu.exists() else {}
    kullanici = kullanici or os.environ.get("USER", "")
    acik = [v["is"] for v in durum.values() if v.get("durum") == "GONDERILDI"]
    sacct = {}
    if acik:
        out = calistir(["sacct", "-n", "-X", "-P", "-o", "JobID,State", "-j", ",".join(acik)])
        for s in out.splitlines():
            if "|" in s:
                j, st = s.split("|", 1)
                sacct[j.strip()] = st.strip()
    durum = durumu_guncelle(durum, sacct)
    kul = kuyruk_gpu(calistir(["squeue", "-r", "-h", "-u", kullanici,
                               "-o", "%i %T %b"]).splitlines())
    s = secim(plan, durum, kul)
    gonderilen = []
    for a, g in s["secilen"]:
        k = sbatch_komutu(a, g)
        if kuru:
            gonderilen.append(" ".join(k))
            continue
        j = _is_kimligi(calistir(k), g)
        durum[_anahtar(a, g)] = {"is": j, "durum": "GONDERILDI"}
        gonderilen.append(f"{_anahtar(a, g)} -> {j}")
        tmp = durum_yolu.with_suffix(".tmp")
        tmp.write_text(json.dumps(durum, indent=1), encoding="utf-8")
        os.replace(tmp, durum_yolu)          # her gönderimden sonra: yarıda kesilirse kayıp yok
    if not kuru:
        tmp = durum_yolu.with_suffix(".tmp")
        tmp.write_text(json.dumps(durum, indent=1), encoding="utf-8")
        os.replace(tmp, durum_yolu)
    return {"kuyruk_gpu": kul, "gonderilen": gonderilen,
            "adimlar": {a["ad"]: adim_durumu(plan, durum, a["ad"]) for a in plan["adimlar"]},
            "bekleyen_adim": s["bekleyen_adim"], "duran_adim": s["duran_adim"]}


_SURE = re.compile(r"^#SBATCH\s+(?:--time=|-t\s+)(\S+)", re.M)


def sure_saat(betik_metni: str) -> float:
    """`#SBATCH --time` → saat. SLURM biçimleri: `dk`, `dk:sn`, `sa:dk:sn`,
    `gün-sa`, `gün-sa:dk`, `gün-sa:dk:sn`."""
    m = _SURE.search(betik_metni)
    if not m:
        raise ValueError("#SBATCH --time yok")
    s, gun = m.group(1), 0
    if "-" in s:
        g, s = s.split("-", 1)
        gun = int(g)
        p = [int(x) for x in s.split(":")] + [0, 0]
        sa, dk, sn = p[0], p[1], p[2]
    else:
        p = [int(x) for x in s.split(":")]
        sa, dk, sn = {1: (0, p[0], 0), 2: (0, p[0], p[-1]), 3: tuple(p)}[len(p)]
    return gun * 24 + sa + dk / 60 + sn / 3600


def butce(plan: dict, durum: dict, saatler: dict[str, float], azami: int = AZAMI_GPU) -> dict:
    """Kalan işin ÜST sınır bütçesi (süre sınırları, adımlar sıralı varsayımı).

    `gpu_saat_ust` = kalan görev × GPU × süre sınırı; `duvar_saat_ust` = her
    adımda `ceil(kalan / (azami // gpu))` tur × süre sınırı, adımlar art arda.
    Gerçek süre genellikle sınırın altındadır; bu bir ÜST tahmindir.
    """
    satir, gs_top, duvar = {}, 0.0, 0.0
    for a in plan["adimlar"]:
        kalan = [g for g in _gorevler(a)
                 if durum.get(_anahtar(a, g), {}).get("durum") != "BITTI"]
        gpu = int(a.get("gpu", 1))
        h = float(saatler[a["ad"]])
        tur = -(-len(kalan) // max(1, azami // max(gpu, 1))) if kalan else 0
        gs = len(kalan) * gpu * h
        satir[a["ad"]] = {"kalan": len(kalan), "gpu_saat_ust": gs, "duvar_saat_ust": tur * h}
        gs_top += gs
        duvar += tur * h
    return {"adimlar": satir, "gpu_saat_ust": gs_top, "duvar_saat_ust": duvar}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    alt = ap.add_subparsers(dest="komut", required=True)
    a = alt.add_parser("adim")
    a.add_argument("--plan", type=Path, required=True)
    a.add_argument("--durum", type=Path, required=True)
    a.add_argument("--kuru", action="store_true", help="gonderme, komutlari yaz")
    b = alt.add_parser("butce", help="kalan isin ust sinir GPU-saat / duvar saati")
    b.add_argument("--plan", type=Path, required=True)
    b.add_argument("--durum", type=Path, default=None)
    ns = ap.parse_args(argv)
    if ns.komut == "butce":
        plan = json.loads(ns.plan.read_text(encoding="utf-8"))
        durum = (json.loads(ns.durum.read_text(encoding="utf-8"))
                 if ns.durum and ns.durum.exists() else {})
        saat = {x["ad"]: sure_saat(Path(x["betik"]).read_text(encoding="utf-8"))
                for x in plan["adimlar"]}
        r = butce(plan, durum, saat)
        for ad, s in r["adimlar"].items():
            print(f"  {ad}: kalan {s['kalan']}, <= {s['gpu_saat_ust']:.0f} GPU-sa, "
                  f"<= {s['duvar_saat_ust']:.0f} sa duvar")
        print(f"TOPLAM (ust sinir, {AZAMI_GPU} GPU, sirali): {r['gpu_saat_ust']:.0f} GPU-sa, "
              f"{r['duvar_saat_ust']:.0f} sa = {r['duvar_saat_ust'] / 24:.1f} gun")
        return 0
    r = adim_at(json.loads(ns.plan.read_text(encoding="utf-8")), ns.durum, kuru=ns.kuru)
    print(f"kuyrukta GPU: {r['kuyruk_gpu']} / {AZAMI_GPU}")
    for g in r["gonderilen"]:
        print(("  KURU: " if ns.kuru else "  GONDERILDI: ") + g)
    for ad, d in r["adimlar"].items():
        print(f"  {ad}: {d}")
    if r["duran_adim"]:
        print("DURDU (bagimli adimda HATA):", ", ".join(r["duran_adim"]))
        return 7
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
