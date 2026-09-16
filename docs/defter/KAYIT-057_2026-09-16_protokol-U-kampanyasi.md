# KAYIT-057 — Protokol U kampanyası: model DART'ın β'sına ulaşabiliyor mu (2026-09-16)

**Kapsam:** Bitiş 3 / Protokol U (model yeterliliği) · **Durum:** kaba görevler
koşuyor · **Öncül:** [KAYIT-056](KAYIT-056_2026-09-16_yagiztruba-kurulum-ve-duman.md),
[`PROTOKOL-U-MODEL.md`](../truba/PROTOKOL-U-MODEL.md) (kural koşudan önce kilitli),
[`BITIS3-DURUM.md`](../BITIS3-DURUM.md)

---

## 0. Soru

Gerçek DART `β = 3,12 ± 0,34`; model önsel boyunca en fazla `β ≈ 1,85`
(24 ms keşif, kaba-72, +5,2σ). **Hangi model bileşeni `β`'yı gözlem bandına
taşır?** Tek faktörlü tarama, merkez θ `(1,15 ; 1e5 ; 0,275)`, plato anı
`t = 0,1 s`, üretim fiziği (kesme + taban), matris sahası, iki tohum
(`20260906`, `99991111`).

| varyant | değişiklik |
|---|---|
| U0 | taban (üretim) |
| U1 | `Y₀ = 10 Pa` (önsel dışı) |
| U2 | `Y₀ = 1 Pa` (önsel dışı) |
| U3 | `μ_f = 0,2` (üretim 0,6) |
| U4 | `μ_f = 0,05` |
| U5 | `Pe = 1e5, Ps = 1e7` (üretim 1e6 / 1e8) |
| U6 | yığın yoğunluğu `1500 kg/m³` (sahne 1800) |
| U8 | birleşik: `Y₀ = 1`, `μ_f = 0,2`, Pe/Ps düşük, `ρ = 1500` |

**Yargı (kilitli, `u_model_raporu.py`):** varyantın **kendi hedef kütlesiyle**
gözlenen β; `z = (β−1_gözlem − β̄−1_sim) / σ_β`; `|z| ≤ 2` BANDA ULAŞIYOR,
`z > 2` ALTINDA. En az bir varyant ulaşırsa MODEL GÖZLEME ULAŞABİLİYOR; hiçbiri
→ HİÇBİR VARYANT ULAŞMIYOR (→ koşullu Protokol V). Rapor artık kapsamı da yazar
(beklenen 20 görev; eksikse "EKSİK", V kararı verilmez — A88).

Önceden denetlendi (2026-09-15): bayraklar çözücüye gerçekten ulaşıyor (malzeme
θ başına değiştirilmeden `WarpSolid3D`'ye gidiyor, `ρ` sahne tabanında korunuyor).

## 1. Gönderim

| | |
|---|---|
| hesap / alan | `egitimg16u3`, `/arf/scratch/egitimg16u3/driftclaude` |
| kod | **`24e513e343cdbccf240a73258cb3909b0fb41340`** (`SABIT_COMMIT`; uymazsa iş 92 ile durur) |
| plan / durum | `truba/sira_bitis3_U.json` / `kampanya/SIRA_U.json`; günlük `gonderimler.txt` |
| gönderim öncesi denetim | 16 betik: tek `--array=i`, u1 yolu yok, atomik tasarım yazımı var, `--exclude=kolyoz19,kolyoz9` |
| sıra | `U_orta` (16–19) **üretilmedi** — kaba tamamen bitmeden gönderilmez |
| GPU | 16 (sınır 20) |
| zaman | 2026-09-16 22:31:59–22:32:01 (+03) |

| görev | varyant | tohum | iş |
|---|---|---|---|
| 0 | U0 | 20260906 | `1565205_0` |
| 1 | U0 | 99991111 | `1565206_1` |
| 2 | U1 | 20260906 | `1565207_2` |
| 3 | U1 | 99991111 | `1565208_3` |
| 4 | U2 | 20260906 | `1565209_4` |
| 5 | U2 | 99991111 | `1565210_5` |
| 6 | U3 | 20260906 | `1565211_6` |
| 7 | U3 | 99991111 | `1565212_7` |
| 8 | U4 | 20260906 | `1565213_8` |
| 9 | U4 | 99991111 | `1565214_9` |
| 10 | U5 | 20260906 | `1565215_10` |
| 11 | U5 | 99991111 | `1565216_11` |
| 12 | U6 | 20260906 | `1565217_12` |
| 13 | U6 | 99991111 | `1565218_13` |
| 14 | U8 | 20260906 | `1565219_14` |
| 15 | U8 | 99991111 | `1565220_15` |

45 s sonra: 5 koşuyor (`kolyoz22, 36, 47, 52, 55`), 11 öncelik sırası bekliyor.

## 2. İzleme

*(Koşu sırasında eklenecek.)*

### 22:34 — ilk iki dakika (5 görev koşuyor, 11 bekliyor)

| görev | düğüm | GPU | ilk çıktı |
|---|---|---|---|
| 0 (U0) | kolyoz22 | H100 80GB HBM3 | `ortak_bas` geçti, commit `24e513e`, `ek=` boş |
| 2 (U1) | kolyoz47 | **H200** | `ek=--onsel-disi-izin`, `! ONSEL DISI TASARIM … cikarim verisi DEGIL` |
| 4 (U2) | kolyoz55 | **H200** | aynı uyarı |
| 1, 3 | kolyoz36, kolyoz52 | — | koşuyor |

- `.err`'lerde bilinen `module: command not found` dışında satır **yok**; `launch failed/held` **yok**.
- **Karışık donanım:** görevler H100 ve H200'e düşüyor. İkisi de Hopper
  (`sm_90`) mimarisi; FP64 çekirdekler aynı derleme hedefiyle koşuyor. Yine de
  aynı varyantın iki tohumu farklı kartta koşabilir — tohum farkı yorumlanırken
  bu not akılda tutulmalı (bit düzeyi kıyas yapılmayacak; yargı tohum
  ortalamasıyla).

### 22:40 — 8 dakika

- 6 koşuyor (görev 0–5; görev 5 `kolyoz27`), 10 bekliyor, **düşen yok**; hiçbir
  görev henüz bitmedi → kaba bir görev **≥ 8 dk**.
- **Grup kotası:** `egitimg16` `GrpTRESMins cpu = 37 200 000`; kullanım
  (`sshare` RawUsage, CPU-saniye) `598 229 080` ≈ `9,97M` CPU-dk (~%27). U'nun
  tamamı en fazla `20 × 16 × 600` = `192 000` CPU-dk (sınırın ~%0,5'i) → kota riski yok.
- **Açık risk — orta süre sınırı:** `is_U_model.slurm` 20 görevin hepsine
  `--time=10:00:00` veriyor. Orta merdiven kabadan kat kat pahalı; kaba süre
  ölçülmeden orta'nın 10 saate sığdığı **bilinmiyor**. **Kural (orta
  gönderilmeden önce):** kaba görevlerin `Elapsed`'inden ve parçacık sayısı
  oranından orta süresi kestirilir; `≥ %60 × 10 sa` çıkarsa orta gönderilmeden
  süre sınırı yükseltilir (yeni commit + yeniden sabitleme), süre aşımıyla GPU
  saati yakılmaz.

### 22:45 — orta şimdi gönderildi (kural değişikliği ve gerekçesi)

Kullanıcı 24 saat yok ve "U çözülsün" dedi. Orta'yı kaba bitene kadar
bekletmek, orta'yı 24 saat geciktirirdi. Sıralama zinciri **8 GPU** sınırından
kalmaydı; sınır **20** ve `16 kaba + 4 orta = 20` → sınırın içinde. Kaba süre
ölçülemediği için orta süre sınırı **üretilen betikte** `10:00:00 →
1-00:00:00` yapıldı (`kolyoz-cuda` azamisi `3-00:00:00`, QoS sınırı yok).
**Kod aynı** (`24e513e`): çalışma dizinine dokunulmadı (bekleyen kaba görevler
sabit commit denetimiyle koşuyor; dizin değişseydi 92 ile dururlardı). Plan:
TRUBA `kampanya/sira_U_orta_simdi.json`, depoda `truba/sira_bitis3_U_orta.json`.
Gönderim öncesi 4 betik denetlendi (süre satırı tek ve `1-00:00:00`, dizi 16–19,
u1 yok, atomik yazım, exclude).

| görev | varyant | tohum | iş |
|---|---|---|---|
| 16 | U0 orta | 20260906 | `1565222_16` |
| 17 | U0 orta | 99991111 | `1565223_17` |
| 18 | U8 orta | 20260906 | `1565224_18` |
| 19 | U8 orta | 99991111 | `1565225_19` |

### 22:46 — ilk beş kaba görev BİTTİ (süre ölçüldü)

| görev | durum | `Elapsed` | sürücü duvarı | düğüm |
|---|---|---|---|---|
| 0 U0 | COMPLETED 0:0 | 13:17 | 794 s | kolyoz22 |
| 1 U0 | COMPLETED 0:0 | 13:29 | 802 s | kolyoz36 |
| 2 U1 | COMPLETED 0:0 | 13:18 | 792 s | kolyoz47 |
| 3 U1 | COMPLETED 0:0 | 13:11 | 784 s | kolyoz52 |
| 4 U2 | COMPLETED 0:0 | 13:19 | 792 s | kolyoz55 |

Hepsinde `tamamlanan 1/1, dusen 0`, `npz` ~2,0 MB. Kaba görev **~13 dk** → 10 sa
sınırı çok geniş; orta için 24 sa kabadan ~110 kat pahalılığa kadar yeter.

**Ara bakış — KİLİTLİ YARGI DEĞİL** (`u_model_raporu.py`, 5 koşu,
`kampanya/S_U_ara_2248.json`):

| varyant | sim β−1 | gözlem β−1 ± σ_β | z | |
|---|---|---|---|---|
| U0 (2 tohum) | 0,946 | 2,121 ± 0,341 | +3,4 | ALTINDA |
| U1 `Y₀ = 10 Pa` (2 tohum) | 1,049 | 2,121 ± 0,341 | +3,1 | ALTINDA |
| U2 `Y₀ = 1 Pa` (**1 tohum**) | 1,007 | 2,117 ± 0,341 | +3,3 | ALTINDA |

- Rapor gerçek veride **KAPSAM: EKSİK (8)** yazdı ve "V kararı verilmez" dedi
  → A88 düzeltmesi sahada çalıştı.
- Plato anında taban `β ≈ 1,95` (24 ms keşfin model üst sınırı ~1,85).
- `Y₀`'ı `1e5 → 1–10 Pa` düşürmek `β−1`'i yalnız `+0,06 – +0,10` artırdı.
  Banda girmek için `β−1 ≳ 1,44` gerekiyor. Kalan varyantlar (μ_f, Pe/Ps,
  `ρ = 1500`, U8) koşuyor; U6/U8'de gözlenen β da kütleyle birlikte düşer.

## 3. Sonuç

*(Kaba bitince `u_model_raporu.py`; orta 16–19 gönderilir; ikisi bitince kilitli
yargı. Satırlar silinmez.)*
