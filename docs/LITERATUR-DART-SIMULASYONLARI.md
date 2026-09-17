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

---

## 7. Genişletilmiş tarama (2026-09-17, aynı gün)

Kullanıcı: *"sadece bunu değil genel fizik simülasyonu, benzer makalelere bak;
onlarda yarayan değişiklikleri A/B/C'den önce bizde yapalım."* "Teyit" sütunu:
**tam metin** = makale sayfaları okundu; **sayfa özeti** = yayıncı sayfasından
araç özeti; **arama özeti** = yalnız arama sonucu (birebir teyit edilmedi).

| # | çalışma | ne buldu (bizimle ilgili) | teyit |
|---|---|---|---|
| L8 | Raducan, Jutzi, Zhang, Ormö, Michel 2022, *A&A* 665, L10 — [arXiv:2209.02677](https://arxiv.org/abs/2209.02677) | Bern SPH, 160 m moloz küre, **2,5e6** parçacık (mermide 50); matris Drucker-Prager `Y = 0`, `f = 0,56`, %35 gözenek; bloklar `Y = 1e7 Pa`, çekme ~1 MPa, `f = 0,8`; bloklar pkdgrav/SSDEM çöküşünden. Geç evre şeması `t_geçiş = 5, 50, 500 s`, **2 saate kadar**. Blok kütle kesri **> %35**: `β ≈ 1,5–3,2` (homojen `4,3`'ten **%60'a kadar düşük**); **< %20**: çarpma noktası yakınındaki blok `β`'yı −%35 / +%15 değiştiriyor; çarpma yeri kaynaklı yayılma ~%60. En küçük çözülebilen blok yarıçapı 2,5 m (~30 parçacık). `v/U > 1e-2` ejekta "çözülmemiş" sayılmış. | tam metin (s. 1–4) |
| L9 | Owen ve diğ. 2022, *PSJ* 3, 218 — [doi:10.3847/PSJ/ac8932](https://iopscience.iop.org/article/10.3847/PSJ/ac8932) | Spheral/CTH/iSALE: **küre mermi β'yı gerçek DART geometrisine göre fazla veriyor** — zayıf hedefte %10–20, güçlüde %5–25. "Üç küre" modeli etkinin çoğunu yakalıyor; silindir yakalamıyor. Spheral: çarpma noktasında 5 cm, dışa doğru kademeli kabuklar. | sayfa özeti |
| L10 | Stickle ve diğ. 2023 LPSC #2563; 2025 *PSJ* 6, 38 — [doi:10.3847/PSJ/ad944d](https://iopscience.iop.org/article/10.3847/PSJ/ad944d) | DART IWG varsayımları: `ρ = 2400 ± 300`, blok SFD Dimorphos'tan, blok kayma dayanımı 1 MPa / çekme 1 kPa, **mermi = üç alüminyum küre** (L9). Gözlemler: periyot/hız değişimi, β, ejekta morfolojisi, ejekta kütlesi. Sonuç: yüzey dayanımı **birkaç Pa – onlarca kPa**, krater **~40–60 m**. | LPSC tam metin; PSJ arama özeti |
| L11 | Senel ve diğ. 2025, *PSJ* — [doi:10.3847/PSJ/addf31](https://iopscience.iop.org/article/10.3847/PSJ/addf31) (iSALE-3D) | Dimorphos neredeyse kohezyonsuz (< birkaç Pa), küresel yeniden yüzeylenme. **1–10 Pa'da yüzey eğriliği momentum aktarımını düz yüzeye göre %44 ± 10 azaltıyor.** 1–80 Pa homojen de, katmanlı/kümeli bloklu iç yapı da β = 2,2–4,9 ile uyumlu → **β tek başına iç yapıyı ayırt etmiyor.** | arama özeti |
| L12 | Senel ve diğ. 2025, *MNRAS* 545 — [doi:10.1093/mnras/staf2162](https://academic.oup.com/mnras/article/545/3/staf2162/8365559) | Yakın bloklar yalnız çarpma noktasından ~10 m (~16 mermi yarıçapı) içinde etkili; net β değişimi ≤ %8. | arama özeti |
| L13 | Dai ve diğ. 2024, *PSJ* 5 — [doi:10.3847/PSJ/ad72eb](https://iopscience.iop.org/article/10.3847/PSJ/ad72eb) | Yüzeyin hemen altındaki büyük blok "ters zırhlama" ile momentum aktarımını **%50'ye kadar artırabiliyor**; 60–75° eğik çarpmada keskin düşüş. | arama özeti |
| L14 | Jiao, Yan, Cheng, Baoyin 2024, *MNRAS* 527, 10348 — [doi:10.1093/mnras/stad3888](https://doi.org/10.1093/mnras/stad3888) | **SPH–DEM hibrit**: erken evre SPH, geç evre bloklar DEM; DART'ın momentum aktarımı ve kütle atımını yeniden üretiyor; temas O(N)→O(N^2/3), yerçekimi ~100× hızlı. | arama özeti |
| L15 | Kumamoto ve diğ. 2022 — [arXiv:2209.11876](https://arxiv.org/abs/2209.11876) | 7 malzeme parametresinde **300+ 3B simülasyon**, ML; aynı hız değişimini birçok özellik birleşimi üretebiliyor → dayanımı ayırmak için **kütle ya da krater boyutu** gerekli. | özet sayfası |
| L16 | Nakano ve diğ. 2024, *PSJ* 5, 133 — [doi:10.3847/PSJ/ad4350](https://iopscience.iop.org/article/10.3847/PSJ/ad4350); inceleme [arXiv:2502.14990](https://arxiv.org/abs/2502.14990) | Dimorphos'un yeniden şekillenmesi (eksen oranı 1,06 → ~1,3) 33 dk periyot değişiminin **~125 s'sini (belirsizlikle ~250 s'ye kadar)** açıklayabilir, **aynı yönde** (kısaltıyor). İnceleme: yeniden şekillenme hesaba katılınca `ΔV_T = 2,42 mm/s` (diğer analiz 2,70); β yeniden hesaplanmamış; en büyük belirsizlik Dimorphos kütlesi; **Hera varışı Aralık 2026 sonu.** | Nakano arama özeti; inceleme özet sayfası |
| L17 | Lolachi ve diğ. 2025, *PSJ* — [doi:10.3847/PSJ/adec6b](https://iopscience.iop.org/article/10.3847/PSJ/adec6b); Dotto ve diğ. 2024, *Nature* — [doi:10.1038/s41586-023-06998-2](https://www.nature.com/articles/s41586-023-06998-2) | Ejekta kütlesi **1,6 ± 0,3 × 10⁷ kg** (LICIACube); ejekta konisi açıklığı **140 ± 4°** (başka analizde eliptik ~95° × ~133°); ejekta hızları onlarca m/s – ~500 m/s. | arama özeti |
| L18 | Herreros & Charnoz 2026 — [arXiv:2606.15459](https://arxiv.org/abs/2606.15459) | Kazılan kütlenin çoğunu taşıyan **1–9 cm/s** yavaş ejekta; yeniden toplanan kütlenin > %99'u 5 saatte Dimorphos'a dönüyor. | özet sayfası |
| L19 | Vernon, Goldstein, Bower (galaksi oluşumu) — [Stat. Sci. 29(1)](https://projecteuclid.org/journals/statistical-science/volume-29/issue-1/Galaxy-Formation-Bayesian-History-Matching-for-the-Observable-Universe/10.1214/12-STS412.pdf) | **Tarih eşleme (history matching):** `I = |E[f(x)] − z| / √(Var_vekil + σ²_gözlem + σ²_model)`; kesme `I < 3` (Pukelsheim 3σ). Model eksikliği (**model discrepancy**) terimi açıkça var. | arama özeti |
| L20 | Daly ve diğ. 2023 (arama özeti üzerinden) | DART, Dimorphos'un şekil merkezine < 25 m, yüzey normaline **~17°** açıyla çarptı. | arama özeti |

## 8. Bizde yapılacak değişiklikler — kanıta göre sıralı öneri

İşaret: β'ya beklenen etki yönü (↑ artırır, ↓ azaltır). Hiçbiri henüz
uygulanmadı; her biri ADR + koşudan önce kilitli protokol ister.

| öncelik | değişiklik | kanıt | β etkisi | maliyet |
|---|---|---|---|---|
| **1** | Geç evre hızlı entegrasyon şeması (EOS → `P = A(1 − ρ/ρ₀)`, `A ≈ 0,03–0,1 MPa`, kayma modülü orantılı) + öz-yerçekimi + **~1–2 sa** simülasyon | L1, L2, L3, L8 | **↑↑** (zayıf hedefte asıl momentum) | kod (GPU yok) + uzun koşular |
| **2** | `Y₀` önseli **0–500 Pa**; sürtünme `μ_f` sabit 0,6 yerine belirsiz (0,4–1,0; L2 en iyi 0,55) | L1 Tablo 2, L2, L11 | ↑ (Y₀ ↓); `μ_f` 0,4→1,0: `β` ~%25 düşer | tasarım/önsel |
| **3** | β **iki yöntemle**: kaçan momentum + yeniden toplanma sonrası kütle merkezi | L1, L2 | doğrulama | küçük kod |
| **4** | Kıyas sınaması: L1 küresi (75 m, 1600, 500 kg, 6 km/s, `Y₀ = 50/10/1/0`, `μ_f = 0,6`) Tablo 2'ye karşı; `t_geçiş` en az iki değer (L3, L8) | L1, L3, L8 | güven | ~4–8 kaba koşu |
| **5** | Mermi: tek küre yerine **üç alüminyum küre** (DART IWG) ya da en azından sistematik terim | L9, L10 | **↓ %10–20** | sahne kodu |
| **6** | Hedef şekli: küre `R = 81,9 m` yerine **basık elipsoit** (177×174×116 m) + hacim/kütle tutarlılığı (sahne hacmi şekil modelinin ~1,27 katı) | L1 (elipsoit `β` küreden %15–21 yüksek), L2, L11 | ↑ (şekil) / kütle eşlemesi | sahne kodu |
| **7** | Gözlenen β'ya **yeniden şekillenme sistematiği** (~125–250 s, aynı yön) — kilitli değerin yanına ayrı satır | L16 | gözlem `β − 1` **↓ ~%6–13** | belge/arayüz |
| **8** | **Ek gözlenebilirler**: ejekta kütlesi (1,6 ± 0,3e7 kg), koni açısı (~140°); depoda `M_ejekta`, `theta_ejekta` zaten var | L2, L10, L11, L15, L17 | β'nın ayırt edemediğini ayırmak | vekil/olabilirlik |
| **9** | Blok modeli: kütle kesri etkisi büyük; blok başına ≥ ~30 parçacık şartı; sahne tohumu = çarpma yeri belirsizliği → tohum sayısı artırılmalı | L8, L12, L13 | ↓ (yoğun blok) / ±%35 (yakın blok) | çözünürlük/koşu |
| **10** | Çözünürlük: düşük çözünürlük hızlı ejektayı ~%15 fazla veriyor (bizde kaba > orta ile **aynı yön**); geç evrede momentum yavaş ejektaya kaydığı için hassasiyet azalabilir; merdivenin 2× sıçramaları yerine kademeli kabuk (Spheral) düşünülmeli | L1, L9 | kaba ↑ yanlılık | ölçüm |
| **11** | Karar kuralı (yeni protokoller için, **geriye dönük değil**): tarih eşleme `I < 3`, paydada **model eksikliği** terimi (mermi geometrisi, açı, şekil, çözünürlük) | L19 | — | protokol |
| **12** | Çarpma açısı ~17° (sistematik terim) | L5, L13, L20 | küçük ↓ | düşük öncelik |

## 9. Bu tarama projeye ne söylüyor

- U/V'nin "ulaşmıyor" sonucu, literatürdeki başarılı DART modellerinin üç ortak
  özelliğinin bizde eksik olmasıyla uyumlu: **uzun süre + geç evre şeması + çok
  düşük kohezyon**. Bu bir açıklama önerisi; kıyas sınaması (öncelik 4) olmadan
  kanıt değil.
- Bazı düzeltmeler β'yı **düşürür** (üç küre mermi %10–20, yoğun blok, çözünürlük);
  bazıları **artırır** (süre, düşük Y₀, basık şekil); gözlenen β ise yeniden
  şekillenmeyle **düşer**. Net sonucu yalnız koşu söyler.
- L2, L11, L15: **β tek başına iç yapıyı belirlemiyor.** Literatür ejekta kütlesi,
  koni açısı, şekil değişimi ve (Hera ile) krater/kütle ekleyerek daraltıyor. Bizim
  posteriorumuz da yalnız β ile kalırsa en iyi ihtimalle `Y₀` üst sınırı verir.
- **Hera Aralık 2026 sonunda varıyor** (L16): mühürlü öngörü (Protokol HT) bundan
  önce depoya işlenmeli.
- **Özgünlük:** L2, L10, L11, L14 aynı soruyu farklı kodlarla çözdü. Katkımız:
  açık GPU (Warp) kodu, kalibre Bayesçi çıkarım + açık model eksikliği/çözünürlük
  terimi, koşudan önce kilitli protokoller, mühürlü Hera öngörüsü.
