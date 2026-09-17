# Literatür — DART/Dimorphos çarpma simülasyonları (2026-09-17)

**Neden:** U ve V kilitli olarak "model gözleme ulaşmıyor" dedi (KAYIT-064).
Aynı çarpışmayı simüle eden yayımlanmış çalışmalar okundu: ne yaptılar, biz
neyi farklı yapıyoruz, neyi almalıyız. Sayılar kaynaktan okundu; "teyit"
sütunu nasıl okunduğunu söyler (tam metin / özet sayfası / arama özeti).

## 1. Kaynaklar

| # | çalışma | kod | teyit |
|---|---|---|---|
| L1 | Raducan & Jutzi 2022, *PSJ* 3, 128 — [doi:10.3847/PSJ/ac67a7](https://iopscience.iop.org/article/10.3847/PSJ/ac67a7) | Bern SPH | tam metin (Tablo 2 satır satır, yöntem paragrafları) |
| L2 | Raducan ve diğ. 2024, *Nature Astronomy* 8, 445 — [arXiv:2403.00667](https://arxiv.org/abs/2403.00667) | Bern SPH | HTML yöntem bölümü |
| L3 | Raducan ve diğ. 2022, *Nat. Commun.* (Hayabusa2 SCI) — [arXiv:2212.04390](https://arxiv.org/html/2212.04390) | Bern SPH | HTML yöntem bölümü |
| L4 | Cheng ve diğ. 2023, *Nature* 616, 457 — [PMC10115652](https://pmc.ncbi.nlm.nih.gov/articles/PMC10115652/) | gözlem | tam metin |
| L5 | Raducan, Davison & Collins 2021 — [arXiv:2105.01474](https://arxiv.org/pdf/2105.01474) | iSALE-2D/3D | PDF s. 1–11 |
| L6 | Luther ve diğ. 2022, *PSJ* 3, 227 — [doi:10.3847/PSJ/ac8b89](https://iopscience.iop.org/article/10.3847/PSJ/ac8b89) | iSALE, Bern SPH, miluphcuda | özet sayfası (bitiş zamanı yazılı bulunamadı) |
| L7 | Stickle ve diğ. 2022, *PSJ* 3, 248 — [doi:10.3847/PSJ/ac91cc](https://iopscience.iop.org/article/10.3847/PSJ/ac91cc) | çok kodlu karşılaştırma | **okunamadı** (PDF metni çıkmadı) |

## 2. Gözlem (L4)

- `β = 3,61 (+0,19 / −0,25)` (1σ), Dimorphos yoğunluğu `2400 kg/m³` varsayımıyla;
  `1500–3300 kg/m³` için `β = 2,2–4,9`. Hız değişimi `Δv_T = −2,70 ± 0,10 mm/s`.
- Hacim (L2): `177 × 174 × 116 m`, `0,00181 km³`.
- **Bizim sahne:** küre `R = 81,94 m` (`V = 2,30e6 m³`, L2 hacminin ~1,27 katı),
  `ρ = 1800`, `M = 4,16e9 kg`. Kilitli gözlem `β = 3,12 ± 0,34` (depodaki arayüz).
  L4 `β − 1`'i kütleyle ölçeklenirse sahne kütlesinde `β ≈ 3,4–3,5` çıkar —
  **kaba tahmin, kilitli değer değil**; kütle/hacim tanımı farkı açıkça yazılmalı.

## 3. Onlar ne yaptı

### L1 — küre `a = 75 m`, `ρ ≈ 1600`, 500 kg alüminyum küre (ρ = 1000) 6 km/s

- Tillotson (bazalt) + P-α (%40 gözeneklilik) + LUND basınç bağımlı dayanım
  (`Y₀`, `f`), gerinim ≥ 1'de kohezyon kaybı; **öz-yerçekimi açık**.
- `5 × 10⁵` SPH parçacığı (çözünürlük sınaması `1e6`, `2e6`).
- **Hızlı entegrasyon şeması:** şok geçtikten sonra geç evre düşük hızlı granüler
  akış; *"low bulk sound speed material"* ile modellenir. Geçişte basitleştirilmiş
  Tillotson (enerji terimleri sıfır), `A ≈ 0,1 MPa`, kayma modülü orantılı küçültülür
  → zaman adımı büyür. DART için `t_geçiş ≈ 30 dk`; geçişli/geçişsiz koşu farkı
  ~1 sa'te "birkaç yüzdeden az".
- **Süre:** `Y₀ > 0` için 30 dk; `Y₀ = 0` için **2 saat** ("yavaş, kaçmayan ejektanın
  çoğu yeniden toplanana kadar").
- **β iki yolla:** (1) kaçış hızını aşan parçacıkların momentumu; (2) yeniden
  toplanmadan sonra cismin kütle merkezi hızı (Bruck Syal ve diğ. 2016).

**Tablo 2 (küre, dikey çarpma) — β:**

| `Y₀` \ `f` | 0,4 | 0,6 | 0,8 | 1,0 | sonuç |
|---|---|---|---|---|---|
| 50 Pa | 4,07 | 3,63 | 3,32 | 3,08 | krater |
| 10 Pa | 4,75 | 4,18 | 3,69 | 3,38 | krater |
| 1 Pa | 5,59 | 4,66 | 4,05 | 3,65 | deformasyon |
| 0 Pa | 5,98 | 4,93 | 4,27 | 3,82 | deformasyon |

Ölçülen hız üssü `μ = 0,36–0,39` (f arttıkça küçülür). Elipsoitler (`0 Pa`, `f = 0,6`):
`β = 5,97` (basık), `5,68` (uzun).

### L2 — DART'ın kendisi

- Şekil modeli elipsoidi, `ρ = 1500–3300`, matris gözenekliliği `%35–65`, bloklar
  (gözeneklilik %10, çekme ~10 MPa) hacimce `%0–50`; `Y₀ = 0–500 Pa`, `f = 0,4–0,7`.
- Mermi: "eşdeğer kütleli düşük yoğunluklu küre"; uzay aracı geometrisi basitleştirilmiş.
- Öz-yerçekimi (Didymos yok), **1 saate kadar**, L1'in geç evre şeması.
- β + ejekta konisi + ejekta kütlesi birlikte karşılaştırılmış.
- **Sonuç:** `Y₀` birkaç Pa'dan az, `ρ < 2400` (en iyi `2200`), `f ≈ 0,55`,
  bloklar ≲ %40; krater değil **küresel deformasyon**.

### L3 — Hayabusa2 SCI (şemanın ayrıntısı)

- Geçiş ölçütü `t_geçiş ≃ 10 · L / c_ses` (SCI için `0,1 s`); `A ≈ 0,027 MPa`;
  `P = A(1 − ρ/ρ₀)`; normal adım `dt < çözünürlük/c_s ≈ 1e-6–1e-7 s`.
- Sağlamlık: geçiş `0,5 / 0,8 / 1,4 / 2,0 s` → krater yarıçapları belirsizlik içinde aynı.
- ~`1e7` parçacık, ~1000 s.

### L5, L6 — ölçekleme ve kodlar arası uyum

- Nokta kaynak (Housen & Holsapple 2011): `v(r)/U = C₁ [r/a (ρ/δ)^ν]^(−1/μ) (1 − r/(n₂R))^p`,
  `M(<r)/m = (3k/4π)(ρ/δ)[(r/a)³ − n₁³]`; `μ` momentum (1/3) ile enerji (2/3) arasında.
- L5 (`Y₀ = 10 kPa`, `f = 0,6`, %20): ejekta momentumunun önemli kısmı `v/U ~ 1e-3 → 1e-4`
  (≈ 6 → 0,6 m/s) arasında birikiyor; krater 1 s'de hâlâ büyüyor.
- L6: `1,4–100 kPa`'da iSALE ve iki SPH kodu β'da `±5–10%` uyumlu (ezilme eğrileri
  eşlenince). SPH kodları hızlı ejektayı iSALE'den hızlı fırlatıyor.

## 4. Biz neyi farklı yapıyoruz

| | literatür (L1, L2) | DART-RIFT (U/V) | etkisi |
|---|---|---|---|
| süre | 30 dk – 2 sa | **0,1–0,2 s** | zayıf hedefte momentumun büyük kısmı sonra geliyor |
| geç evre | düşük ses hızı şeması | yok | uzun süre bizim hızımızla imkânsız (0,1 s ≈ 13 dk) |
| `Y₀` önseli | 0–500 Pa, en iyi < birkaç Pa | **≥ 1e3 Pa** (U1/U2 önsel dışı 10/1 Pa, yalnız 0,1 s) | önsel literatürün en iyi bölgesini dışarıda bırakıyor |
| öz-yerçekimi | açık | kapalı (V1/V3/V4 açık, 0,2 s) | kısa sürede etkisiz, geç evrede şart |
| β | kaçan momentum + kütle merkezi | kaçan momentum (`r > R`, `v_r > v_esc`) | L1 yöntem 1 ile aynı fikir |
| çözünürlük | 5e5 – 1e7 | kaba 1,7e4, orta 6,9e4, ince 4,9e5 (merdiven) | M: mutlak gözlenebilir yakınsamıyor |

**Okuma (yargı değil):** L1'de `Y₀ = 10 Pa, f = 0,6` → `β = 4,18` (saatler);
bizde `Y₀ = 10 Pa` → `β ≈ 2,05` (0,1 s). Hedefler aynı değil (kütle, yoğunluk,
mermi), ama açığın yönü ve büyüklüğü **süre kırpmasıyla** uyumlu. Bu bir
hipotezdir; bizim kodumuzla sınanmadan sonuç sayılmaz.

## 5. Alınacaklar (öneri — ADR/protokol gerekir)

1. **Geç evre şeması** (L1/L3): `t_geçiş`'te EOS → `P = A(1 − ρ/ρ₀)`, enerji terimleri
   sıfır, `A ~ 0,03–0,1 MPa`, kayma modülü orantılı; `compute_dt` zaten `c_long`
   üzerinden (`solver_solid.py`), adım kendiliğinden büyür.
2. **Öz-yerçekimi** geç evrede açık (`--yercekimi` var).
3. **Önsel:** `Y₀` alt sınırı 0–1 Pa'ya; `f` 0,4–1,0.
4. **β iki yolla** (L1): kaçan momentum ve yeniden toplanma sonrası kütle merkezi.
5. **Kıyas sınaması:** kendi kodumuzla L1'in küre sahnesini (75 m, 1600, 500 kg, 6 km/s,
   `Y₀ ∈ {50, 10, 1, 0}`, `f = 0,6`) koşup Tablo 2 ile karşılaştırmak — yeni modele
   güvenmenin ön şartı; geçiş zamanı iki değerle (L3 sağlamlık sınaması gibi).

## 6. Dürüst notlar

- L2 DART'tan zaten `Y₀ < birkaç Pa`, `ρ ≈ 2200`, blok ≲ %40 çıkardı. Bizim katkımız
  bağımsız GPU kodu + kalibre Bayesçi posterior + çözünürlük hata terimi + mühürlü
  Hera öngörüsü olmalı; "ilk kez biz bulduk" denemez.
- L2 β'nın yanında ejekta konisi ve ejekta kütlesini de kullandı; biz yalnız β
  kullanıyoruz → yoğunluk/blok kesri tek başına β'dan ayrışmayabilir.
- L7 okunamadı; L6'da simülasyon bitiş zamanı bulunamadı.
