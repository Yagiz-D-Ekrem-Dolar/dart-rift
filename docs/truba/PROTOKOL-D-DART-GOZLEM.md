# Protokol D — gerçek DART gözlemine uygulama

**Yazıldı:** 2026-09-14, **plato anı verisi (Q2/Q3/Q1) gelmeden ÖNCE**.
Kurallar `scripts/dart_gozlem_posterior.py` ve `scripts/cozunurluk_hatasi.py`
içinde kilitli; sınavları `tests/test_dart_gozlem_posterior.py`.

## 1. Soru

Simülasyonun kalibre edilmiş posterioru, **ölçülen** DART momentum
aktarımıyla hangi `(α_b, Y₀, f)` bölgesini seçiyor — ya da ölçülen değer
modelin önsel boyunca üretebildiği aralığın **dışında** mı?

## 2. Gözlem (depodaki arayüzden, dış sayı girilmedi)

`observables/period_interface.py`: ölçülen `ΔT = −33,0 ± 1,0 dk`
(`DIMORPHOS_SYSTEM`), `dart_beta_budget(p_imp, target_mass=M)`. `β` hedef
kütlesiyle yaklaşık orantılı olduğu için (yörünge hızı toplam kütleye de bağlı) gözlenen `β` **simülasyonun kendi hedef kütlesi** (havuzdaki
npz'lerin medyanı) ve mermi momentumu için hesaplanır.

`σ_β² = (ΔT bandının yarı genişliği)² + (0,105 β)²` — ikinci terim
arayüzün kendi belgesinde ölçülmüş dairesel yörünge / yayımlanan `β`
farkı (`%10,5`), sistematik olarak.

## 3. Gürültü terimleri (log10(β−1) biriminde)

- `σ_gözlem = σ_β / ((β−1) ln 10)`
- `σ_vekil` = θ-gruplu 4-kat artık sapması (P §4d ile aynı katlar).
- Aralıklar yamuk ağırlıklı orta nokta birikimiyle (A85; düz dağılımda
  `%16` sınırı tam `0,16`).
- `σ_çöz` = `RMS_θ(ȳ_üretim − ȳ_ince)`, Mt (0,1 s) kampanyasından
  (`cozunurluk_hatasi.py`). İnce merdiven de yakınsamamışsa **alt sınır**dır
  ve öyle yazılır. `kayma_oranı = std/|ort| < 0,5` → "SABİT KAYMA".

## 4. Yargı

1. **Önsel kapsama:** `s = √(σ_gözlem² + σ_vekil² + σ_çöz²)`; ızgara
   üzerinde vekil tahmininin en büyüğü/küçüğü ile karşılaştırılır.
   `y − 2s > ŷ_max` → **ÖNSEL DIŞI (YUKARI)**, `y + 2s < ŷ_min` →
   **ÖNSEL DIŞI (AŞAĞI)**, aksi **ÖNSEL İÇİNDE**.
2. **ÖNSEL İÇİNDE:** posterior; eksen başına bilgi oranı
   `genişlik68 / 0,68 < 0,5` → **KISITLANIYOR**.
3. **ÖNSEL DIŞI:** posterior hesaplanmaz; en yakın θ ve σ cinsinden fark
   raporlanır.

## 5. Uygulanan havuzlar

| çıktı | havuz | rol |
|---|---|---|
| `S_DART_Qo.json` | Q3 orta, 0,1 s (`Nto + N2to`) + `σ_çöz` (Mt orta) | Q §4'e göre esas olabilir |
| `S_DART_Qk.json` | Q2 kaba, 0,1 s (`Ntk + N2tk`) + `σ_çöz` (Mt kaba) | karşılaştırma |
| `S_DART_i72.json` | ince-72, 24 ms | **betimleyici** (24 ms plato değil) |

## 6. Yorum tablosu (veri gelmeden)

| sonuç | anlamı |
|---|---|
| ÖNSEL İÇİNDE, ≥ 1 eksen KISITLANIYOR | Bitiş 3: gerçek DART verisiyle iç yapı kısıtı |
| ÖNSEL İÇİNDE, hiçbiri | gözlem modelle uyumlu ama tek başına `β` iç yapıyı kısıtlamıyor; Hera krater verisi gerekli |
| ÖNSEL DIŞI (YUKARI) | model/önsel DART'ın `β`'sına ulaşmıyor: daha zayıf matris (`Y₀ < 1e3`), yerçekimi, uzun zaman ya da ejekta modeli eksik — ADR ile önsel/model genişletilir |
| ÖNSEL DIŞI (AŞAĞI) | model fazla momentum aktarıyor — aynı ADR sorusu ters yönde |

## 7. Bilinen sınırlar

- Tek gözlenebilir (`β`); ejekta kütlesi ve koni açısı kaynak değerleri
  depoda doğrulanmadığı için dahil **edilmedi**.
- Yerçekimi kapalı; `β` kaçış ölçütü `v_esc` eşiğiyle (A12).
- 0,1 s tek an; plato salınımı (`%2–4`) `σ_vekil`'e girer.
