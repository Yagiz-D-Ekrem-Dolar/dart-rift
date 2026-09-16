# KAYIT-062 — Orta'da da İKİ EKSEN; gerçek DART önselin dışında; Q/D/U/V/HT koşudan önce yazıldı; 32 GPU ve iptal (2026-09-14)

**Kapsam:** Bitiş 3 · **Durum:** GERİYE DÖNÜK yazıldı (2026-09-16) ·
**Kaynak:** [`SONUC-M-N-P-J-T.md`](../SONUC-M-N-P-J-T.md) §2e,
[`FAZ4-SIKINTI-RAPORU.md`](../FAZ4-SIKINTI-RAPORU.md) A84–A86,
[`BITIS3-DURUM.md`](../BITIS3-DURUM.md), [`DEVAM-BITIS3.md`](../DEVAM-BITIS3.md) §3, §12.1;
protokoller `docs/truba/PROTOKOL-{Q,D,U,V,HT}-*.md` · **Öncül:**
[KAYIT-061](KAYIT-061_2026-09-13_geriye-donuk-kilitli-sonuclar-gecesi.md)

---

## 0. Günün iki yüzü

Bilimsel olarak projenin **en iyi ve en zor** günü: sentetik çıkarım orta
çözünürlükte de tuttu, ama gerçek DART gözlemi modelin ulaşabildiği aralığın
**dışında** çıktı. Operasyonel olarak da en kötüsü: kuyrukta 32 GPU'ya çıkıldı,
kullanıcı haklı olarak itiraz etti, akşam işlerin çoğu iptal oldu.

## 1. Kilitli sonuçlar

**Orta, kesme + taban, 48 θ (Nok + N2ok + Nokd), 96 koşu:**

| yol | `α_b` | `log Y₀` | `f` | genel |
|---|---|---|---|---|
| **P-v4 GP** | BİLGİ YOK | **0,18 ÇÖZÜLÜYOR** | **0,24 ÇÖZÜLÜYOR** | **İKİ** |
| **P-v4b kuadratik** | BİLGİ YOK | **0,33 ÇÖZÜLÜYOR** | **0,31 ÇÖZÜLÜYOR** | **İKİ** |
| P-v4b GP | **0,34 AŞIRI GÜVENLİ** | | | KALİBRASYON DÜŞTÜ |

→ **Orta çözünürlükte de kaba ile aynı: `Y₀` ve `f` çözülüyor, `α_b`
çözülmüyor.** P-v4 GP'de `Y₀` genişliği `0,18`: önselin `%74`'ü eleniyor.

**T platosu (kesme + taban):** 24 ms değeri plato değerinin `%78–80`'i
(`β−1` Tot orta `0,651 → 0,817 → 0,820`); kaba ile orta platoları `%12` farklı
→ **Protokol Q** (plato anında yakınsama). A83 V1 (c) Tkt tamamlandı → KARARLI.
İnce (Ni + N2i) ve N3 kaba/orta: **66/66 görev, sıfır patlama**.

## 2. Kusurlar

| kayıt | ne | sonuç |
|---|---|---|
| **A84** | `sbatch --export=ALL,D="a,b,c"` virgülü değişken ayırıcı sayıyor | dört rapor (ince-48, kaba-72, orta-72, kaba-48 figür) **hata vermeden** yalnız ilk kampanyayı okudu (`46 koşu, 23 θ` …); aynı gece desen betiğin içinde olan `is_Pv4o_rapor` doğruydu (`96 koşu, 48 θ`) — farkı yakalayan o. Çare: `+` ayırıcı + `BEKLENEN_DESEN` (exit 4) + koşu sayısı denetimi; raporlar yeniden gönderildi. Kalıp: **"iş bitti" ≠ "doğru veriyi okudu"** |
| A85 | ızgara posteriorunun `%68/%95` aralıkları yarım bölme kayık | `40` düğümde `0,0128 u`; kilitli yargılara dokunulmadı; yeni kodda yamuk ağırlık (15.09'da uç düğüm hatası bulunacak → A87) |
| A86 | M2 ince `99991111`'de krater operatörü `nan` | `ValueError: eksen isininda yuzey bulunamadi (pencere 79,516..90,960 m)`; merkez ışında `φ` hiç `0,5`'i kesmiyor; istisna `gozlem_vektoru`'nda **sebepsiz** yutuluyordu. Kök sebep açık |

## 3. Gerçek DART gözlemi — keşif (24 ms, yargı değil)

| | değer |
|---|---|
| gözlenen `β` (depo arayüzü, sahne hedef kütlesi `4,164e9 kg`) | **`3,12 ± 0,34`** |
| model `β` aralığı, kaba-72 (144 koşu) | `1,25 – 1,85` → **ÖNSEL DIŞI (YUKARI), +5,2σ** |
| model `β` aralığı, orta-72 | `1,27 – 1,72` → **+6,2σ** |
| plato çarpanıyla en büyük model | `β − 1 ≈ 0,85 × 1,26 ≈ 1,07` → `β ≈ 2,1` < bandın `2σ` alt ucu `2,44` |

Kendi hatam (aynı gün düzeltildi, satırlar silinmedi): plato çarpanını `β`'ya
uygulayıp `~2,3` yazdım (doğrusu `β − 1`'e, `~2,1`); `2,78`'i `2σ` ucu sandım
(o `1σ` ucu).

**Okuma:** sentetik çıkarım zinciri çalışıyor; **model–gözlem köprüsü eksik.**

## 4. Koşudan önce yazılan protokoller

| protokol | soru | koşul |
|---|---|---|
| **Q** (Q1–Q6) | plato anında (0,1 s) yakınsama (Mt), kaba/orta posterior, ince-72, blok sahası, kontrast | §4 esas-sonuç kuralı: Mt YAKINSIYORsa esas = Q3 orta plato; değilse ince-72 24 ms |
| **D** | gerçek DART ile önsel kapsama (`2s`) + posterior | `σ² = ΔT² + (0,105 β)²`; `σ_çöz` Mt'den |
| **U** | hangi model bileşeni β'yı gözlem bandına taşır | Y₀ 10/1 Pa, μ_f 0,2/0,05, Pe/Ps, ρ 1500, birleşik; `\|z\| ≤ 2` |
| **V** | U ulaşmazsa: yerçekimi, hasar, 0,2 s | **koşullu** |
| **HT** | Hera krater öngörüsü, SHA-256 mühürlü ön kayıt | üzerine yazılamaz |

Destek kodu: `dart_gozlem_posterior.py`, `cozunurluk_hatasi.py`,
`bitis3_raporu.py`, `u_model_raporu.py`, `hera_tahmin.py`, gözlem önbelleği
(`gozlem_onbellek.py`, 8,1 s → 0,002 s, bit-aynı).

## 5. Operasyon: 32 GPU, sınır, iptal

- Kuyrukta **32 GPU**'ya çıkıldı. Kullanıcı: hesap **ortak**, bu kullanım etik
  değil. Sınır önce **10**, sonra **8**; "kuyruğa 90 iş yığma, biri bitsin
  diğerine geçelim". Toplu `scancel` önerim **reddedildi** → yıkıcı işlemden önce
  sorulur.
- **19:20:** Mt 8–35, Q2/Q3/Q5/Q6, U (tamamı), N3i 6–13, Pgen 1561234/35 ve
  bağımlı D/HT **iptal**. Tamamlanan: Pgen `1561231` (ince-48), `1561232`,
  `1561233` (orta-72) — u4'te kaldı, okunmadı.
- Sonraki gün kurallar koda döküldü (sıralı gönderici, KAYIT-063); 16 Eylül'de
  kullanıcı sınırı **20**'ye çıkardı (KAYIT-056).
