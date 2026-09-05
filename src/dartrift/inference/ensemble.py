"""Ensemble sürücüsü — **kaldığı yerden devam eden** koşu döngüsü.

## Neden gerekli

FAZ 5 `~300` koşu istiyor ve ölçüldü ki bu `~10` GPU-günü
([KAYIT-040](../../../docs/defter/KAYIT-040_2026-08-08_ensemble-fizibilitesi-A-prime-ile.md)).
Bir SLURM işi `12` saatte kesiliyor; yani ensemble **birden çok işe**
yayılmak zorunda.

> Devam edemeyen bir ensemble sürücüsü, her kesintide **her şeyi**
> kaybeder. TRUBA kotası şu an dolu — yani kesinti bir olasılık değil,
> **yaşanmış** bir gerçek (iş 1460700 zaman aşımından kesildi).

## Tasarım: **satır satır** JSONL

Her nokta tamamlanır tamamlanmaz **kendi satırı** olarak eklenir.
Yeniden başlatıldığında dosya okunur ve **zaten var olan** noktalar
atlanır.

| seçenek | neden seçilmedi |
|---|---|
| tek büyük JSON, sonda yaz | kesinti = **her şey** gider |
| her nokta için ayrı dosya | binlerce dosya; `/arf` kotası inode de sayar |
| **JSONL, satır satır** | **seçilen** — atomik ekleme, kısmi dosya okunabilir |

## Bozuk son satır

Kesinti tam yazma anında olursa son satır **yarım** kalabilir. Okuyucu
bunu **atlar** ve o nokta yeniden koşulur — sessizce bozuk veri
kullanmaktan iyidir.

## Determinizm (ADR-0004)

Tasarım `root_seed`'e bağlı; sürücü **aynı** tasarımı yeniden üretir.
Bir noktanın kimliği **indeksi**dir, o yüzden kısmi bir dosya sonraki
koşuda doğru noktalarla eşleşir. Tohum değişirse eski satırlar
**geçersizdir** ve sürücü bunu **fark eder** (tohum dosyaya yazılır).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

__all__ = ["EnsembleDurum", "oku_tamamlananlar", "ensemble_kos"]


@dataclass(frozen=True)
class EnsembleDurum:
    """Bir ensemble koşusunun özeti."""

    toplam: int
    tamamlanan: int
    dusen: int
    atlanan: int          # bu kosuda ATLANAN (onceden tamamlanmis)
    bozuk_satir: int
    yol: str

    @property
    def bitti(self) -> bool:
        return self.tamamlanan + self.dusen >= self.toplam


def oku_tamamlananlar(yol, root_seed: int | None = None,
                      surum: str | None = None) -> tuple[dict, int]:
    """JSONL'den `{indeks: y}` ve **bozuk satır sayısı**.

    Bozuk (yarım yazılmış) satırlar **atlanır**; o noktalar yeniden
    koşulur. `root_seed` verilirse tohumu uyuşmayan satırlar da atlanır —
    tasarım değiştiyse eski sonuçlar **geçersizdir**.

    ## `surum` — aynı gerekçe, **kod** tarafında (rapor A40)

    `L1` bir kez `47` saniyede `COMPLETED` döndü ve **hiçbir şey
    koşmadı**: devam mantığı önceki koşunun satırlarını görüp bütün
    noktaları atladı. Ama o satırlar **iki gün eski kodla** ve
    provenance kaydı (`npz`) olmadan üretilmişti.

    > *"Dosya var"* ile *"geçerli bilimsel veri var"* aynı şey değil.
    > Geçerlilik: `var ∧ doğru tohum ∧ doğru şema ∧ doğru sürüm`.

    `surum` verilirse sürümü uyuşmayan satırlar da **atlanır** ve o
    noktalar yeniden koşulur.
    """
    yol = Path(yol)
    if not yol.is_file():
        return {}, 0
    tamam: dict = {}
    bozuk = 0
    for satir in yol.read_text(encoding="utf-8").splitlines():
        satir = satir.strip()
        if not satir:
            continue
        try:
            d = json.loads(satir)
            i = int(d["i"])
            y = d["y"]
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            bozuk += 1
            continue
        if surum is not None and d.get("surum") != surum:
            # KOD DEGISTIYSE eski sonuc gecersiz -- tohumla ayni gerekce.
            continue
        if root_seed is not None and d.get("root_seed") != root_seed:
            bozuk += 1          # tasarim degismis -> gecersiz
            continue
        if y is None:
            tamam[i] = None     # DUSEN nokta -- tekrar denenmez
            continue
        arr = np.asarray(y, dtype=np.float64)
        if not np.all(np.isfinite(arr)):
            bozuk += 1
            continue
        tamam[i] = arr
    return tamam, bozuk


def ensemble_kos(tasarim, ileri, yol, root_seed: int,
                 ilerleme=None, yeniden_dene_dusenleri: bool = False,
                 surum: str | None = None) -> EnsembleDurum:
    """Tasarımı koştur; **zaten tamamlanmış** noktaları atla.

    Parameters
    ----------
    tasarim
        `(n, d)` parametre noktaları.
    ileri
        `ileri(theta) -> (k,)` dizi; patlarsa `Exception` atmalı.
    yol
        JSONL dosyası. Her satır:
        `{"i": …, "y": […] | null, "root_seed": …, "surum": …}`.
    surum
        Kod sürümü (commit SHA). Verilirse **başka sürümle** üretilmiş
        satırlar geçersiz sayılır ve o noktalar yeniden koşulur
        (rapor A40).
    yeniden_dene_dusenleri
        `False` (varsayılan): düşen nokta **tekrar denenmez** — aynı
        parametre aynı şekilde düşer ve GPU boşa gider. `True` yalnızca
        düşme nedeni **düzeltildikten sonra** anlamlıdır.
    """
    tasarim = np.atleast_2d(np.asarray(tasarim, dtype=np.float64))
    yol = Path(yol)
    yol.parent.mkdir(parents=True, exist_ok=True)
    tamam, bozuk = oku_tamamlananlar(yol, root_seed, surum)

    atlanan = 0
    dusen = sum(1 for v in tamam.values() if v is None)
    for i, th in enumerate(tasarim):
        if i in tamam and (tamam[i] is not None or not yeniden_dene_dusenleri):
            atlanan += 1
            continue
        try:
            y = np.asarray(ileri(th), dtype=np.float64).ravel()
            if not np.all(np.isfinite(y)):
                raise RuntimeError(f"sonlu olmayan cikti: {y}")
            kayit = {"i": i, "y": [float(v) for v in y],
                     "root_seed": root_seed, "surum": surum}
            durum = "tamam"
        except Exception as e:                             # noqa: BLE001
            kayit = {"i": i, "y": None, "root_seed": root_seed,
                     "surum": surum,
                     "hata": str(e)[:400]}
            durum = f"DUSTU: {str(e)[:120]}"
            dusen += 1
        # HER NOKTA HEMEN YAZILIR ve dosya kapatilir: kesinti en fazla
        # SON noktayi kaybeder.
        with yol.open("a", encoding="utf-8") as f:
            f.write(json.dumps(kayit, ensure_ascii=False) + "\n")
            f.flush()
        tamam[i] = None if kayit["y"] is None else np.asarray(kayit["y"])
        if ilerleme:
            ilerleme(i, len(tasarim), durum)

    tamamlanan = sum(1 for v in tamam.values() if v is not None)
    return EnsembleDurum(toplam=len(tasarim), tamamlanan=tamamlanan,
                         dusen=dusen, atlanan=atlanan, bozuk_satir=bozuk,
                         yol=str(yol))
