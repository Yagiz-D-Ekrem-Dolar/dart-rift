# G0 + G1 + G2 — porozite düzeltmesi sonrası kanıt (commit `b29c03a`)

Bu koşu, [ADR-0023](../adr/ADR-0023-porozite-ortuk-cozum.md) ile kapatılan
gözeneklilik kusurundan **sonra** üretilmiştir. Önceki kapanış kanıtı
([GATES_HEAD_9ffe342](GATES_HEAD_9ffe342.md)) o kusur açıkken alınmıştı.

## Künye

| | |
|---|---|
| Depo commit | **`b29c03a`**, temiz git ağacı |
| SLURM işleri | G0: **1434417** · G1+G2: **1434418** · dayanıklılık: **1434419** |
| Düğüm | `kolyoz-cuda` / H100 |
| Ortam | Python 3.10.15, NumPy 1.26.4, warp 1.15.0, CUDA Toolkit 12.9 |
| pytest | **396 geçti / 0 kaldı** (13:24), `xfail` yok |
| Kapsam | %97,6 (eşik %85) |
| Kırmızı takım (§12) | 6/6 temiz |
| Çıkış kodları | G0: 0 · G1: 0 · G2: 0 |

## Sonuçlar

| Kapı | Sonuç | Karar |
|---|---|---|
| **G0** — Zemin sağlam | **GEÇTİ** 8/8 | FAZ 1 başlayabilir |
| **G1** — Şok motoru çalışıyor | **GEÇTİ** 8/8 | FAZ 2 başlayabilir |
| **G2** — Gerçek malzeme fiziği | **GEÇTİ** 7/7 | **FAZ 3 başlayabilir** |

## G2 — bu koşuda ilk kez görünen kanıt

**C4 (yerçekimi):**

```
iki-cisim 20 yorunge: E hatasi 2.4e-07, yaricap drifti 1.3e-08;
kure: BH-direct medyan 0.43%, kabuk hata maks 1.90%;
GPU<->CPU dogrudan 3.0e-16, Barnes-Hut 3.1e-16
```

Son satır yenidir. Bu koşuya kadar `mode="barnes_hut"` **hiçbir testte ya da
kapıda çözücüye verilmemişti**; GPU halat-ağacı gezinmesi hiç
çalıştırılmamıştı. Ölçüt artık GPU çekirdeğini CPU referansına karşı şart
koşuyor.

**C3 (crush curve):** `alpha_min = 1.212`. Önceki koşuda 1.207 idi; fark,
α'nın artık örtük çözülmesindendir.

## G1 — önceki koşudan devralınan iki ölçü

**C3:** `dt yarilaninca hata/2.45 (~2 = birinci mertebe KESME hatasi,
sizinti DEGIL)` — [ADR-0020](../adr/ADR-0020-enerji-hatasi-kesme-hatasidir.md).

**C5:** `KE/E=0.182 (sonlu enjeksiyonda ~0.19 beklenir; nokta patlamasi
0.28)` — [ADR-0011](../adr/ADR-0011-sedov-yakinsama-kurulumu.md) §4'ün iki faz
boyunca uygulanmayan raporlama sözü.

## Dayanıklılık testi (iş 1434419) — porozite düzeltmesinin üretim doğrulaması

Tam fizikli gerçek çarpma (Tillotson + dayanım + gözeneklilik + öz-yerçekimi),
N = 33 596:

| adım | enerji hatası | momentum | kütle |
|---|---|---|---|
| 2 000 | **%0,48549** | 9,2e-11 | 0,00e+00 |
| 4 000 | %0,48549 | 2,3e-10 | 0,00e+00 |
| 6 000 | %0,48549 | 4,0e-10 | 0,00e+00 |
| 20 000 | %0,48550 | 1,6e-09 | 0,00e+00 |
| 24 000 | %0,48550 | 1,9e-09 | 0,00e+00 |

Aynı senaryo düzeltmeden önce (iş 1429628): **%44,80285**.
**92 kat iyileşme**, ve drift 24 000 adımda tamamen düz.

## Kapsam sınırı

Kapılar motorun **doğrulama senaryolarını** geçtiğini gösterir. Dimorphos
hakkında hiçbir bilimsel sonuç iddia edilmemektedir; çarpma koşuları
FAZ 3'tedir.

> Görsel olarak makul bir krater kanıt DEĞİLDİR; kanıt test ve sayıdır.
