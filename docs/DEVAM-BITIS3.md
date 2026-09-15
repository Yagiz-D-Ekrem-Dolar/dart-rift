# DEVAM — Bitiş 3 devir notu (2026-09-15)

Bu belge, bir Claude oturumunun bildiği her şeyi bir sonrakine (başka hesap
dahil) aktarmak için yazıldı. Kısa kurallar kök dizindeki `CLAUDE.md`'de.
Güncellerken **satır silme**; tarihli not ekle.

## 0. Yeni oturuma başlarken

1. `CLAUDE.md` → bu belge → `docs/BITIS3-DURUM.md` → `docs/FAZ4-SIKINTI-RAPORU.md` başı.
2. `git log --oneline -20` ile son işleri gör.
3. TRUBA'ya dokunmadan önce §3'teki hesap durumunu ve §4 prosedürünü oku.

Önerilen ilk mesaj (kullanıcı için):
> "dart-rift deposundaki CLAUDE.md ve docs/DEVAM-BITIS3.md'yi oku, durumu
> Türkçe özetle, sonra §6'daki sıradaki işe geç."

## 1. Tek paragraf durum

Yazılım ve çıkarım zinciri hazır ve sınanmış (GPU SPH çözücü, gözlem
operatörleri, vekil model, dış doğrulamalı kalibrasyon, kilitli protokoller,
~2100 sınav, lint temiz). **Ana bilimsel engel:** gerçek DART `β = 3,12 ± 0,34`,
model önsel boyunca en fazla `β ≈ 1,85` üretiyor (24 ms keşif) → gerçek veriyle
posterior henüz kurulamıyor. Bunu **Protokol U** (hangi model bileşeni `β`'yı
gözleme taşır) cevaplayacak; hiçbiri taşımazsa koşullu **Protokol V**
(yerçekimi/hasar/0,2 s). 14 Eylül'de TRUBA işlerinin çoğu iptal oldu; U hiç
koşmadı. Yeni TRUBA hesabı bekleniyor.

## 2. Bilimsel durum

### Kilitli sonuçlar

| konu | sonuç |
|---|---|
| Sayısal tutarlılık | `ara` akma kipi Δt bağımlılığını kaldırıyor (J1); A80 dayanım kesmesi + A83 yoğunluk tabanı patlamaları gideriyor |
| Ayırt edilebilirlik (N) | kesmeli 48 θ havuzu: Y₀ ve f görünür |
| Kalibre çıkarım (P-v4b, 24 ms, kaba ve orta) | sentetik gözlemle **Y₀ ve f çözülüyor, α_b çözülmüyor** (4-kat dış doğrulama) |
| Çözünürlük (M) | mutlak gözlenebilirler **yakınsamıyor** (β−1 kaba→ince 0,74→0,64→0,46); Y₀ kontrastı dayanıklı (M2 H_Y), α_b/f değil |
| Zaman (T) | β 0,1–0,2 s'de platoya ulaşıyor; 24 ms platonun ~%80'i |

### Gerçek DART (keşif, 24 ms)

- Gözlenen β (sahne hedef kütlesi ~4,16e9 kg ile, `dart_beta_budget`): `3,12 ± 0,34`
  (`σ² = ΔT yarı-bandı² + (0,105 β)²`; 0,105 = basit iki-cisim arayüzü ile
  yayımlanmış ~3,6 arasındaki fark).
- Model β aralığı: kaba-72 `1,25–1,85` (+5,2σ), orta-72 `1,27–1,72` (+6,2σ) → ÖNSEL DIŞI (YUKARI).
- Kütle duyarlılığı: gözlemi bandın alt ucuna indiren kütle oranı 0,71–0,76
  (ρ* ≈ 1270–1370). **Varsayım:** model β_max yoğunluktan bağımsız sayıldı —
  gerçek cevap U6/U8'den gelecek.
- Literatür karşılaştırması yapılmadı (yapılacak; kaynaklar doğrulanmalı).
  Hatırlanan: Cheng ve diğ. 2023 (β ~3,6), Raducan ve diğ. 2024 (çok düşük
  yüzey dayanımı) — **teyit edilmedi.**

### Protokol U / V

| | U | V |
|---|---|---|
| soru | parametre ayarı β'yı yükseltir mi | eksik fizik/süre mi |
| değişen | Y₀ 10/1 Pa, μ_f 0,2/0,05, Pe/Ps 1e5/1e7, ρ 1500, birleşik U8 | yerçekimi, hasar, 0,2 s; V4 = U'nun en yakını + ikisi |
| iş | 20 görev (0–15 kaba, 16–19 orta U0/U8), ≤10 sa | 10 görev kaba, ≤24 sa |
| koşul | her durumda | yalnız U "HİÇBİR VARYANT ULAŞMIYOR" ve kapsam TAM ise |
| yargı | `|z| ≤ 2` BANDA ULAŞIYOR | aynı |

Denetlendi (2026-09-15): U bayrakları çözücüye gerçekten ulaşıyor (malzeme θ
başına değiştirilmeden `WarpSolid3D`'ye gidiyor; ρ `sahne_parametreleri`nde
korunuyor). Üretim malzemesi `μ_f 0,6, Pe 1e6, Ps 1e8` (`faz44_dart_yakinsama._malzeme`).

## 3. TRUBA ve hesap durumu

- **Çalışma alanı (13 Eylül'den beri):** `/arf/scratch/egitimg16u4/driftclaude`.
  `pylib/` altında açılmış warp 1.15.0 wheel; `ortak_bas.sh` yeniden yazıldı;
  iş betikleri `is/` altında depodaki `truba/*.slurm`'ün **u4 yollarına sed ile
  çevrilmiş kopyaları**. Gönderim kaydı `$KOK/gonderimler.txt`. Eski u1 verisi
  (G1/G2/I) u4'ten okunamaz.
- **14 Eylül 19:20:** Mt 8–35, Q2/Q3/Q5/Q6, U (tamamı), N3i 6–13, Pgen
  1561234/35 ve bağımlı D/HT **iptal**. **Tamamlanan ama okunmayan:** Pgen
  1561231 (ince-48), 1561232, 1561233 (orta-72). Mt 0–7 ve 12–20 çıktıları
  doğrulanmalı.
- **MCP durumu:** `ardababatrubamcpi` (u4) kullanıcı kararıyla yasak. İkinci MCP
  (`5aa843e9`) `egitimg16u5` olarak açılıyor: u4 "base dir dışı", u1 izin yok,
  u5'te proje verisi yok, **shell aracı yok** (`truba_submit` yalnız betik yolu
  alır). Kullanıcı **yeni hesap** verecek. u5 ev dizininde başka projeler var —
  içlerine bakılmaz.
- Mekanik: `scontrol hold/update` TRUBA'da süre sınırı hatası veriyor;
  `scontrol requeuehold` çalışan işte çalışıyor. CPU rapor adımları için
  `srun --jobid=<koşan iş> --overlap -n1 -c4`. Bekleyen işler `AssocGrpCpuLimit`
  gösterebilir.

### Yeni hesap kurulum listesi

- [ ] Çalışma alanı yolu kararı; `git clone` (GitHub `main`)
- [ ] `pylib/` (warp 1.15.0 wheel açılmış), `ortak_bas.sh`, modül yükleme sınaması
- [ ] Tek görevlik duman sınavı (kısa `t_end`) — GPU, warp, yazma izinleri
- [ ] Gerekli eski veriler (U için gerekmez; Mt/Q için havuzlar) erişilebilir mi
- [ ] Plan JSON'una `"kok"` yaz; `betikler --kuru` benzeri kontrol

## 4. Gönderim prosedürü (8 GPU, sıralı)

1. Plan: `truba/sira_bitis3_U.json` (U_kaba 0–15, sonra U_orta 16–19). Başka
   adım eklerken `tests/test_sira_plani.py` betik/dizi/GPU tutarlılığını sınar.
2. Kuyruktaki GPU sayısını oku (çalışan + bekleyen).
3. `python scripts/sirali_gonderici.py betikler --plan truba/sira_bitis3_U.json
   --durum kampanya/SIRA.json --kullanilan-gpu <N> --cikti-dizini <dizin>`
   → boş yuva kadar tek-görev betiği (`--array=i` ve export'lar içine yazılı,
   `kok` uygulanmış, CRLF temiz). Görevler `HAZIRLANDI` sayılır.
4. Betikleri TRUBA'ya yükle, **tek tek** gönder, dönen kimliği
   `sirali_gonderici.py kaydet --durum ... --anahtar U_kaba:3 --is <id>` ile yaz.
5. İş bitince `kaydet --hal BITTI` (ya da `HATA`); tekrar 2'ye dön.
6. `butce --plan ...` kalan üst sınır GPU-saati verir.

## 5. GPU bütçesi

**Şimdiye kadar:** kesin sayı bilinmiyor. Kayıtlı parçalar: bazı kampanya
hesapları (`108`, `78` GPU-saat); grup CPU-dakika kotası 7,2M → 37,2M (bütün
`egitimg16` grubu, bizim payımız değil). Ölçmek için TRUBA'da
`sacct -X -P -n -S 2026-07-01 -o JobID,JobName,Elapsed,AllocTRES,State`
çıktısını `scripts/gpu_saat.py` ile topla.

**Bundan sonra (üst sınır = iş sayısı × süre sınırı; gerçek genelde daha az):**

| iş | görev × sınır | GPU-saat (üst) | 8 GPU duvar (üst) |
|---|---|---|---|
| U | 20 × 10 sa | 200 | ~30 sa |
| V (koşullu) | 10 × 24 sa | 240 | ~48 sa |
| kaba havuz (yeni model, 0,1 s) | 24 × 12 sa | 288 | ~36 sa |
| orta havuz | 48 × 12 sa | 576 | ~72 sa |
| Mt çözünürlük | 36 × 16 sa | 576 | ~72 sa |
| M2t (düşük öncelik) | 24 × 16 sa | 384 | ~48 sa |
| raporlar (Pgen×2, D, HT) | — | ~40 | — |
| kararlılık taraması + A86 | — | ~50 | — |
| **toplam (V ve M2t hariç)** | | **~1 730** | |
| **toplam (hepsi)** | | **~2 350** | |

## 6. Yapılacaklar (U/V sonrası tam liste)

**Etiketler:** 🖥️ TRUBA · 💻 yerel · ⭐ TRUBA gelmeden yapılabilir

0. **U/V kararı:** 🖥️ U raporu (kapsam TAM?) · 💻 U0/U8 orta: ulaşma çözünürlükle kayboluyor mu · dal seçimi
1. **Modeli kilitle:** 💻 ADR · üretim bayrakları / yeni uzay + sınavlar · yeni protokolü koşudan önce kilitle · 🖥️ kararlılık taraması
2. **Veri (🖥️):** kaba havuz · orta havuz · Mt · M2t (düşük) · önbellek ısıtma + krater nan tanısı
3. **Doğrulama:** N ayırt · P-v4/P-v4b kalibrasyon (**düşerse dur**) · Mt yakınsama + σ_çöz (TAM, kesin) · Q §4 esas havuz
4. **Gerçek veri:** D posterior · 💻 kütle duyarlılığı (model tepkisiyle) · 💻 β≈3,6 senaryosu · HT mühürlü ön kayıt → `docs/onkayit/`
5. **Sağlamlık:** 🖥️ A86 kök sebep · 💻 tohum duyarlılığı · 💻⭐ çözünürlük savunma şekli · 💻⭐ sahne–Dimorphos eşleme belgesi
6. **Literatür (💻⭐):** karşılaştırma tablosu (kaynakları doğrula) · sınırlılıklar bölümü
7. **Rapor (💻):** Bitiş 3 final · şekiller · tekrarlanabilirlik paketi
8. **Yarışma (💻):** ⭐ savunma notu · poster + 10 dk anlatım + jüri soruları · yapay zekâ kullanım beyanı · ⭐ İSEF/TÜBİTAK kural ve tarih kontrolü · özet
9. **Negatif dal:** V süre sınırı ölçümü · teşhis raporu · koşulsuz Hera kaydı · model geliştirme planı
10. **Hera dönemi:** mühürlü tahminle karşılaştırma · ölçülen kütleyle β/posterior güncelleme

## 7. Riskler (U/V başarısızlığı dışında)

1. Çözünürlük artınca β düşüyor → kabada ulaşan varyant ortada banttan çıkabilir (**en olası**).
2. Yalnız uç varyant (Y₀ = 1 Pa) ulaşırsa önsel genişletme gerekçe ister (literatürle desteklenebilir; doğrula).
3. Yeni fizikte sayısal kararsızlık (A80/A83 türü) → OKUNMAZ.
4. V yerçekimiyle 24 sa sınırına sığmayabilir.
5. Yeni modelde kalibrasyon düşebilir.
6. Gözlenen β sistematiği (3,12 vs ~3,6; kütle ölçülmemiş).
7. 8 GPU + ortak kuyruk: tam yeniden koşu 1–2 hafta.
8. A86 krater operatörü bazı koşularda yüzey bulamıyor → HT tahminlerinin bir kısmı eksik kalabilir.
9. Beklenti: gerçek veride tek gözlem (β) var → en iyi senaryo Y₀ kısıtı + Hera öngörüsü; α_b çözülmez.

## 8. Öğrenilen dersler (tekrar etme)

| ders | nerede |
|---|---|
| `sbatch --export=ALL,D="a,b"` virgülü ayırıcı sayar → `+` kullan, sayıyı denetle | A84 |
| Izgara aralığında birikim: uç düğümler yarım hücre; düzeltmeyi uç kantilde de sına | A85, A87 |
| Rapor/karar "bulduğunu" değil "beklediğini" saymalı (Mt kapsam, U BEKLENEN, Mt/M2 `kesin`) | A88 |
| Betiklerde sessiz varsayılan yok (`${X:-...}`, `[ -f ] &&`) → `ZORUNLU_EXPORT`, exit | 2026-09-15 |
| Önbellek anahtarı iç import kapanışını kapsamalı (AST sınavı) | `test_onbellek_bagimlilik` |
| Write üzerine yazar → önce ad kontrolü | kilitli `yakinsama_raporu.py` ezilmişti |
| ruff B007 döngü sonrası kullanımı görmez | `kacis.py` NameError |
| PowerShell çift tırnak + git; WSL bash; CRLF | `commit -F`; Git Bash; `gorev_betigi` LF yazar |
| Sınavda boş iddia yazma (`"import" in m`, `... if False else True`) | AST taraması temiz |
| Toplu iptalden önce kullanıcıya sor; 32 GPU'ya çıkmak kullanıcıyı çok kızdırdı | 14 Eylül |

## 9. Açık kusurlar

- **A86** kök sebep: `M2_ince_b_sahne99991111`'de merkez ışında doluluk φ
  pencere boyunca 0,5'i kesmiyor. Sebep artık `gozlem_vektoru(d, sebepler=)`
  ile yazılıyor; operatör kilitli, dokunulmadı.
- Sıkıntı raporu sayaçları `tests/test_sikinti_raporu.py` ile tutarlı tutulur.

## 10. Yarışma notları

- Kodun büyük kısmı Claude ile yazıldı: **yapay zekâ kullanım beyanı** ve
  kullanıcının her modülü kendi cümleleriyle anlatabildiği bir **savunma notu**
  gerekli (en büyük risk bu).
- Güçlü yanlar: gerçek görev verisi, önceden kilitli kurallar, mühürlü Hera
  öngörüsü, dürüst negatif sonuçlar. Zayıf yanlar: çözünürlük yakınsaması, tek
  gözlem, literatür karşılaştırması eksik.

## 11. Bu oturumun commit'leri (2026-09-15)

`790fdcd` sıralı gönderici · `7316250` A85/A86/A87 · `a2fe96b` U planı + bütçe ·
`d476961` Mt kapsam (EKSİK HAVUZ) · `ca4f038` tek-görev betiği · `72cd933` U/V
kapsam + V betiği · `eb78768` A88 · `d7f7d0e` Mt/M2 `kesin` · `cb6c175` zorunlu
export · `a17c072` `kok` · `df5c75a` önbellek bağımlılığı + lint · `4fef505` boş iddia.
