# KAYIT-065 — Literatür paketi koda girdi, Protokol W kilitlendi (2026-09-17)

**Kapsam:** U/V sonrası kurtarma · **Durum:** kod + protokol hazır, ilk koşu
gönderildi · **Kaynak:** [`LITERATUR-DART-SIMULASYONLARI.md`](../LITERATUR-DART-SIMULASYONLARI.md),
[ADR-0050](../adr/ADR-0050-literatur-paketi-gec-evre-ve-olcum.md),
[PROTOKOL-W](../truba/PROTOKOL-W-KIYAS.md) · **Öncül:** [KAYIT-064](KAYIT-064_2026-09-17_V-sonuc-model-gozleme-ulasmiyor.md)

---

## 0. Neden bu kayıt

KAYIT-064 "model gözleme ulaşmıyor" dedi. Kullanıcı önce kurtarma planını,
sonra *"aynı simülasyonu yapanları oku"*, ardından *"bulduğun her şeyi koda
ekle, sonra ilk testlere başlayalım"* dedi. Bu kayıt o günün işini tutuyor.

## 1. Literatür ne söyledi

Yaklaşık 20 çalışma tarandı (L1–L20). Başarılı DART modellerinin üç ortak
özelliği bizde eksikti:

| | onlar | biz (U/V) |
|---|---|---|
| süre | 30 dk – 2 sa | **0,1–0,2 s** |
| geç evre | düşük ses hızlı malzeme şeması | **yok** |
| kohezyon | en iyi uyum < birkaç Pa (taranan 0–500 Pa) | önsel **≥ 1e3 Pa** |

L1 (Raducan & Jutzi 2022, Tablo 2; küre 75 m, `f = 0,6`):
`Y₀ = 50/10/1/0 Pa` → `β = 3,63 / 4,18 / 4,66 / 4,93`. Bizim `Y₀ = 10 Pa`
koşumuz 0,1 s'de `β ≈ 2,05`.

Ayrıca: küre mermi `β`'yı `%10–20` **fazla** veriyor (L9); elipsoit hedef
küreden `%15–21` **yüksek** (L1); yeniden şekillenme gözlenen `β`'yı
`%6–13` **düşürüyor** (L16); `β` tek başına iç yapıyı belirlemiyor (L2, L11,
L15).

## 2. Koda giren (ADR-0050; hepsi varsayılan KAPALI, eski yollar bit-aynı)

| ne | nerede | sınav |
|---|---|---|
| geç evre şeması (`P = A_geç μ`, enerji terimleri 0, `G` ve `S` aynı oranda) | `WarpSolid3D.gec_evreye_gec` | `test_gec_evre` (18) |
| uzak kaçanı dondurma | `WarpSolid3D.uzak_kacanlari_dondur` | aynı dosya |
| `β` iki yöntem + ejekta koni açısı | `observables/beta_iki_yontem.py` | `test_beta_iki_yontem` (10) |
| elipsoit kaçış ölçütü | `momentum_defteri.disarida_maskesi` | aynı dosya |
| üç küre mermi (%88 + 2 × %6, 2,215 m) | `setup/impactor.coklu_kure_mermi` | `test_coklu_kure_mermi` (8) |
| ileri modele bağlama + CLI | `forward.py`, `faz5_ensemble_merdiven.py` | `test_forward_adr0050` (12) |
| gözlenen `β`'ya yeniden şekillenme (yan yana) | `period_interface` | `test_adr0050_gozlem_ve_karar` (13) |
| gözlem sabitleri (Cheng, ejekta kütlesi, koni) | `observables/dart_gozlemleri.py` | aynı |
| tarih eşleme `I < 3` + model eksikliği | `inference/tarih_esleme.py` | aynı |
| blok çözünürlük tanısı | `setup/blok_cozunurluk.py` | aynı |

**Ölçülen (yerel, Warp CPU):** geçişte `c_s` `~6 m/s`'e iniyor, `dt` **50
kattan fazla** büyüyor; `e_kin + e_int` geçişte **tam sürekli**; kaba DART
sahnesinde 4e-4 s'lik uçtan uca koşu geçerli çıktı.

**Erken zaman uyarısı (ölçüldü):** `t = 4e-4 s`'te `β_km = 0,0004` ama
kaçan-momentum `1,0`. Neden: mermi hâlâ `~6 km/s` gittiği için enerjice
bağsız sayılıyor. Bu yüzden `mermi_bagsiz_kesri` alanı eklendi; `1`'e
yakınken `β_km` **okunmaz**.

## 3. Protokol W (koşudan önce kilitli)

Soru: **kodumuz yayımlanmış bir SPH sonucunu yeniden üretiyor mu?**
L1'in sahnesi (küre 75 m, `ρ 1600`, homojen, mermi 500 kg / `ρ 1000` /
6 km/s, öz-yerçekimi açık) bizim kodla koşulacak.

- Ölçüt: `oran = (β_biz − 1)/(β_L1 − 1)` için **`0,5 – 2,0`** (faktör 2),
  **eğilim** (`1 Pa > 10 Pa > 50 Pa`) ve `t_geçiş` **sağlamlığı** (`≤ %20`).
- GENEL: TUTTU / KISMİ / TUTMADI; yorum tablosu W §6'da (TUTMADI → Faz D).
- Bilinen farklar önceden yazıldı: `Y₀ = 0` koşulmuyor, gerinimle kohezyon
  kaybı yok, çözünürlük `~30×` düşük.
- Rapor: `scripts/w_kiyas_raporu.py` (kilitli, 10 sınav).

## 4. Gönderilen

**W0 — zamanlama koşusu**, iş `1566860`, `is/is_W0_zamanlama.slurm`
(`Y₀ = 10 Pa`, `t_geçiş = 0,2 s`, `t_end = 2 s`, tek GPU). **Bilimsel sonuç
değildir**: yalnız hızı ölçer; W'nin `t_end`'i W §3.2 kuralıyla o ölçüme
göre seçilecek.

TRUBA deposu `f193083`'e güncellendi, `SABIT_COMMIT` yenilendi.

## 5. Açık kalanlar

- W0'ın ölçtüğü hız → `t_end` seçimi → W1–W6 (3 `Y₀` × 2 geçiş anı).
- Gerinimle kohezyon kaybı (L1'de var, bizde yok) — W KISMİ çıkarsa ilk aday.
- Merdivenin 2× sıçramaları yerine kademeli kabuk (L9 Spheral) — ölçülmedi.
- `Y₀ = 0` satırı için `θ` kısıtı (pozitif `Y₀`) gevşetilmeli mi: ADR gerekir.
