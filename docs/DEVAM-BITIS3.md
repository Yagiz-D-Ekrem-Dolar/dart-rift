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

> **Güncel (2026-09-16 22:35):** YağızTRUBA (`egitimg16u3`) kuruldu, duman
> sınavı geçti, **Protokol U kaba koşuyor**: 16 görev `1565205_0 … 1565220_15`,
> kod `24e513e`'ye sabit, durum `kampanya/SIRA_U.json`, günlük `gonderimler.txt`.
> Kaba bitince `U_orta` (16–19) `sirali_gonderici betikler` ile, sonra
> `u_model_raporu.py`. Ayrıntı ve iş kimlikleri: defter **KAYIT-056, KAYIT-057**.
> TRUBA notları: `kolyoz9` dışlandı (başlatma hatası); iş kabuğunda `module`
> yok (zararsız, `ortak_bas.sh` PATH'i kuruyor); tutulan iş `scontrol release`
> ile serbest bırakılamıyor → iptal + yeniden gönder.

> **Güncel (2026-09-17 19:00):** U (20/20) ve otomatik gönderilen V (10/10)
> bitti, kuyruk boş. **İkisinin de kilitli yargısı HİÇBİR VARYANT ULAŞMIYOR**
> (kapsam TAM). Bitiş 3 **negatif dalda** (§6 madde 9). Ayrıntı: defter
> KAYIT-064; sonuç JSON'ları `docs/olcumler/U_V_2026-09-17/`.

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
export · `a17c072` `kok` · `df5c75a` önbellek bağımlılığı + lint · `4fef505` boş iddia ·
`634c840` bu devir notu + `CLAUDE.md` + `gpu_saat.py`.

## 12. Kullanıcıyla son yazışmalar ve kararlar (2026-09-14/15)

Yeni oturum bunları **kullanıcıya yeniden sormadan** bilmeli.

### 12.1 TRUBA etiği — kullanıcının açık talimatları

- 14 Eylül: kuyrukta 32 GPU'ya çıkıldı; kullanıcı çok kızdı ("hesap ortak,
  etik değil"). Önce 10'a, sonra **en fazla 8 GPU** sınırı kondu.
- **Kuyruğa 90 iş yığılmaz**: `%N` kısıtlı dizi bile olmaz; biri bitince diğeri.
- `ardababatrubamcpi` kullanılmaz. Toplu scancel önerimi kullanıcı bir kez
  **reddetti** → yıkıcı işlemden önce mutlaka sor.
- Kullanıcı ikinci MCP'yi bağladı ("ayı gibi kullanma"); `egitimg16u5` çıktı,
  proje alanına erişemedi → hiçbir şey gönderilmedi. Kullanıcı **başka hesap
  verecek**; Claude aboneliği de bitmek üzere → başka Claude hesabına geçecek
  (bu belge o yüzden yazıldı).
- **2026-09-16:** kullanıcı kendi MCP'sini kurdu (**YağızTRUBA**, kullanıcı
  `egitimg16u3`, Slurm hesabı yine `egitimg16`, shell var; varsayılan hedef
  `arf`, GPU için `cuda`). **GPU sınırı 20'ye çıkarıldı** ("8 GPU fazlası da
  olur, 20'ye kadar okey"); kuyruğa yığmama kuralı sürüyor. u3'ten u4/u1
  alanları okunamıyor → yeni çalışma alanı kurulacak. Modül ortamı
  `gpu-2024.0`: Python 3.10.15, numpy 1.26.4, h5py, pydantic, yaml, pytest var;
  **Warp yok** (1.15.0 wheel indirmek için kullanıcı onayı istendi). Çıplak
  `python` modül sonrası bile sistem 3.9'a gidebiliyor → `ortak_bas.sh` ortam
  `bin`'ini PATH'in başına koymalı. u3 scratch'inde başka projeler var; dokunulmaz.

### 12.2 Kullanıcıya anlatılanlar (tutarlı kalsın)

- **U** = mevcut fiziğin ayarlarını çevirerek β'nın DART bandına çıkıp
  çıkmadığı; **V** = kapalı fiziği (yerçekimi, hasar, 0,2 s) açma, yalnız U
  başarısızsa. Harfler kısaltma değil, protokol sırası.
- Üç sonuç: (1) U/V ulaşır → model kilitlenir, havuzlar yeniden, gerçek veri
  posterioru + Hera ön kaydı; (2) ulaşır ama β tek başına kısıtlamaz → Hera
  gerekir; (3) hiçbiri → "model DART β'sını üretemiyor" teşhisi. Üçü de
  bilimsel çıktı, güçleri farklı.
- **Beklenti dürüstçe söylendi:** gerçek veride tek gözlem (β) var; en iyi
  senaryo **Y₀ kısıtı + mühürlü Hera öngörüsü**; α_b çözülmez, f zayıf.
- **Takvim** (hesap açıldıktan sonra, süre sınırı üst tahmini): kurulum ½ gün;
  U kararı ~1,5–2 gün; A yolu ilk gerçek posterior (kaba) ~3–4 gün; kesin
  Bitiş 3 ~6–8 gün; B yolu V kararı ~4 gün.
- **Tamamlanma:** zorluk ağırlıklı **~%70** (kaba tahmin); kalan kısmın en
  belirsiz adımı U.
- **Riskler:** §7 (en olası: çözünürlük artınca β düşmesi).

### 12.3 İSEF değerlendirmesi (kullanıcı sordu)

- Garanti verilmedi. En büyük risk bilimsel değil: **kodun büyük kısmı Claude
  ile yazıldı** → yapay zekâ kullanım beyanı ve kullanıcının her şeyi kendi
  anlatabilmesi (savunma notu) şart; kurallar güncel kural kitabından doğrulanmalı.
- Kullanıcının varsayımı ("jüri Claude'a izin verdi, sunum mükemmel") altında:
  proje kendi başına **yarışabilir**; derece gücü sonuca bağlı — Y₀ kısıtı +
  literatürle uyum + Hera öngörüsü → güçlü (kategori derecesi/özel ödül
  gerçekçi); β kısıtlamazsa orta-iyi; negatif sonuç orta.
- Projenin kendi zayıf yanları: çözünürlük yakınsaması yok, tek gözlem,
  literatür karşılaştırması eksik.
- **Düzeltilen yorum:** önce "yalnız Y₀ = 1 Pa ulaşırsa zor savunulur" dendi;
  sonra literatürde çok düşük yüzey dayanımı bulgusu (hatırlanan: Raducan ve
  diğ. 2024, **teyit edilmedi**) olabileceği için bunun **destek** olabileceği
  söylendi. Kaynak doğrulanmadan kullanılmamalı.
- Şansı artıracak işler (TRUBA'sız): literatür tablosu, çözünürlük savunma
  şekli, sahne–Dimorphos eşleme belgesi, tek sayfa Hera öngörüsü özeti.

### 12.4 Diğer kararlar ve cevaplar

- **Commit sayısı:** kullanıcı "commit sayım çok gözüksün" dedi. **Yapay/boş
  commit atılmayacağı** söylendi (geçmiş herkese açık, güvenilirliğe zarar).
  O an: 647 commit, son 7 günde 74; GitHub güncel. Öneri: sürüm etiketleri
  (`git tag`) + README'de faz zaman çizelgesi — **kullanıcı henüz cevaplamadı.**
- **GPU-saat:** geçmiş toplam bilinmiyor (kayıt yok; grup kotası bizim payımız
  değil) → `scripts/gpu_saat.py` ile `sacct`'tan ölçülecek. Gelecek üst sınır §5.
- **Belge envanteri:** defter 55 kayıt (27 Tem – 29 Ağu), ADR 49, protokol 24 +
  ölçüt 12, kanıt 16, anlık 3, kök belge 28.
- **Defter boşluğu:** 30 Ağustos – 15 Eylül için **defter kaydı yok** (M, N, P,
  Q, D, U, A80–A88 dönemi). KAYIT-056+ yazmayı önerdim — **onay bekliyor.**
  Yazılırsa yalnız mevcut raporlardan, kaynak göstererek.
- **Donanım:** TRUBA `kolyoz-cuda` H100 (bir ölçümde H200); yerel NVIDIA RTX
  3050 Laptop 4 GiB (Ampere, sürücü 610.64). Ölçülen: RTX 3050 H200'den 2,85×
  yavaş (µs/1000 parçacık, KAYIT-041); gerçek moloz koşusunda H100 ~15× hızlı
  (KAYIT-052). **Warp sürüm farkı:** yerel 1.16.0, TRUBA `pylib` 1.15.0 —
  tekrarlanabilirlik bölümüne yazılmalı.

### 12.5 Kullanıcı tercihleri ve iletişim

- Kısa, gündelik Türkçe yazıyor ("kanka", "devam"); cevapta önce net özet ister.
- "Durma, kod yaz, hatalarını kendin bul" diyor; ama TRUBA/GPU konusunda çok
  hassas — sınırı aşmak en büyük hata.
- Yüzde, takvim ve "başaracak mıyız" soruları soruyor → dürüst aralık ver,
  garanti verme, varsayımı açıkça yaz.
- Hedef: İSEF / TÜBİTAK sunumu.

### 12.6 Kullanıcıdan bekleyen kararlar

- [ ] Yeni TRUBA hesabı ve çalışma alanı yolu
- [ ] Defter kayıtları (KAYIT-056+) yazılsın mı
- [ ] Sürüm etiketleri + zaman çizelgesi eklensin mi
- [ ] Savunma notu ve literatür tablosuna başlansın mı

### 12.7 U/V ulaşmadı → kurtarma planı (2026-09-17, önerildi, onay bekliyor)

- Kullanıcı: "U ve V geçmiyorsa proje başarısız mı, nasıl çözeceksin?"
- **Ön bulgu (koddan, ölçülmedi):** `momentum_defteri.py` kaçışı `r > R` **ve**
  `v_r > v_esc` ile sayıyor → 0,1–0,2 s'de hâlâ `R` içinde olan yavaş ama kaçacak
  ejekta sayılmıyor olabilir (β'yı sistematik düşürür).
- **Önerilen fazlar:** A (GPU yok): A1 `R` şartsız kırpılmış momentum, A2 ejekta
  hız dağılımı + ölçekleme yasasıyla geç ejekta, A3 literatür doğrulama — önce
  **Protokol W** kilitlenir. B (~30 GPU-saat): zayıf θ'da 0,5/1/2 s. C: açık
  kapanırsa "SPH erken + ölçekleme geç" hibrit model, havuzlar yeniden, gerçek
  posterior. D: kapanmazsa nicel teşhis + koşulsuz Hera öngörüsü.
- **Kullanıcıya söylenen:** D = **asıl hedefte (gerçek veriyle iç yapı) başarısızlık**,
  ama proje çöp değil (doğrulanmış sentetik çıkarım zinciri + kilitli nicel
  teşhis); İSEF tavanı düşer. Hibrit modelde ölçekleme parametreleri SPH'nin
  kendi ejektasından ölçülmeli, DART'a ayarlanmamalı (yoksa β bedava tutar).
- **"~1 500 GPU-saat"** = §5 tablosundaki üst sınır (kaba 288 + orta 576 + Mt 576
  + rapor/kararlılık ~90; görev × süre sınırı). Ölçülen sürelerle (kaba 0,2 s
  yerçekimli ~0,9 sa, orta ~2 kat+) gerçekçi tahmin **~250–450** (ince süresi
  ölçülmedi); SPH'nin 1–2 s'ye uzaması gerekirse ×5–10 → bütçe aşılır, kapsam
  daraltılır. Karşılaştırma: U+V üst sınır 440, gerçek ~20.
- **C mi D mi (kullanıcı sordu, öznel tahmin):** D ~%40 · C ama zayıf (β tutar,
  posterior geniş / çözünürlük sorunu) ~%25 · C güçlü (gerçek veriyle Y₀ kısıtı)
  ~%35; her biri ±10. "A/B kesin olumlu gelsin" isteğine: **garanti verilemez**,
  sonuca göre kural değiştirmek savunmayı çökertir.
  - Lehine (zarf arkası, doğrulanmadı): nokta kaynak ölçeklemesiyle 0,2 s'de
    fırlatma hızı ~8 m/s, `v_esc ≈ 8 cm/s`; `p(>v) ∝ v^(1−3μ)`, μ ≈ 0,4 → geç
    yavaş ejekta momentumu ×~2,5 (açık ~×2). Y₀ = 1e3 Pa'da kesilme ~0,75 m/s →
    β ≈ 2,45; Y₀ ≲ 10 Pa → β ≈ 3,2. Literatürde zayıf hedefle DART β'sını
    üreten SPH çalışmaları var (hatırlanan: Raducan ve diğ. 2024, **teyit edilmedi**).
  - Aleyhine: (1) ölçekleme 0,1→0,2 s'de ~+%10 bekler, model −%4,5 verdi (sayısal
    sönüm şüphesi); (2) orta < kaba, hibrit bunu düzeltmez; (3) `R` içindeki hızlı
    maddenin çoğu kazı değil **cismin çınlaması** (önceden ölçüldü:
    `momentum_transfer.py` `kacis_bekleyenler` DÜZELTME notu, hedefin %26'sı,
    çarpma noktasında en düşük) → A1 saf "`R` şartını kaldır" yanıltır, uzaysal
    profil gerekir; (4) çarpan μ'ya çok duyarlı (0,36 → ×1,4; 0,45 → ×5) →
    "açık kapanır" ucuz doğru olabilir ama posterior genişler.
- **Kullanıcı "A'dan başlayalım" dedi**, sonra "aynı simülasyonu yapanlar var,
  oku, feyz al" → literatür okundu: [`LITERATUR-DART-SIMULASYONLARI.md`](LITERATUR-DART-SIMULASYONLARI.md).
  Ana bulgu: Raducan & Jutzi 2022 / Raducan ve diğ. 2024 (Bern SPH) DART'ı
  **30 dk – 2 sa** simüle etti (geç evrede düşük ses hızı şeması + öz-yerçekimi);
  75 m küre, `f = 0,6`: `Y₀ = 50 / 10 / 1 / 0 Pa` → `β = 3,63 / 4,18 / 4,66 / 4,93`.
  Bizim önsel `Y₀ ≥ 1e3 Pa` ve süre 0,1–0,2 s → açığın yönü süre + önsel kırpmasıyla
  uyumlu (hipotez). Faz A için öneri: geç evre şeması + L1 küre kıyas sınaması
  (kullanıcı onayı bekleniyor). W protokolü henüz **yazılmadı**; TRUBA'da
  30 koşunun `npz` durumları ve 50 noktalı β(t) eğrileri var (`*.durumlar/`).
- Kullanıcı "A/B/C'den önce genel literatüre de bak, yarayan değişiklikleri bizde
  yapalım" dedi → genişletilmiş tarama: `LITERATUR-DART-SIMULASYONLARI.md` §7–9
  (L8–L20). Öncelikli değişiklik listesi §8 (12 madde): geç evre şeması + öz-yerçekimi
  + 1–2 sa; Y₀ 0–500 Pa ve μ_f belirsiz; β iki yöntem; L1 kıyas sınaması; üç küre
  mermi (β ↓ %10–20); basık elipsoit + hacim/kütle eşleme; gözlenen β'ya yeniden
  şekillenme sistematiği (↓ %6–13); ejekta kütlesi/koni ek gözlenebilir; blok
  çözünürlüğü; merdiven kademeleri; tarih eşleme `I < 3` + model eksikliği terimi;
  17° açı. **Hera varışı Aralık 2026 sonu** → HT mührü öncesinde. Uygulama sırası
  için kullanıcı onayı bekleniyor.
- **Kullanıcı: "bulduğun her şeyi koda ekle, sonra ilk testlere başlayalım"**
  (2026-09-17 akşam) → yapıldı: ADR-0050 (kod paketi, hepsi varsayılan kapalı),
  PROTOKOL-W (kıyas sınaması, koşudan önce kilitli), `w_kiyas_raporu.py`,
  `truba/is_W0_zamanlama.slurm` ve `truba/is_W_kiyas.slurm`. Ayrıntı:
  **KAYIT-065**. TRUBA deposu `f193083`'e güncellendi, `SABIT_COMMIT` yenilendi.
  **W0 zamanlama koşusu `1566860`** (kolyoz1, H100) — bilimsel sonuç değil;
  `t_end` seçimi PROTOKOL-W §3.2 kuralıyla onun ölçtüğü hıza göre yapılacak,
  sonra W1–W6 (3 `Y₀` × 2 geçiş anı) sıralı gönderilecek.
  **Uyarı (kayıtlı):** `sbatch` yalnız `cuda` hedefinden (cuda-ui) ve `/arf/scratch`
  altından çalışıyor; arf arayüzünden `kolyoz-cuda` görünmüyor.
- **2026-09-18 (W sonucu ve sonrası, KAYIT-066):** W0 → `t_end = 600 s` (`dt` 219×,
  ~7,2 GPU-saat/koşu). **W kilitli yargısı OKUNMAZ**: 6/6 koşu yalnız momentum
  defterinden düştü → sebep **A92** (dondurulan parçacık gövdeyi tek yönlü
  çekiyordu; benim hatam, β'ya bakılmadan bulundu ve düzeltildi). A91 (rapor
  deseni), A93 (krater operatörü, tanı), A94 (geç evrede plastik iş tanısı eski
  `G` ile) de kapandı/kaydedildi. **PROTOKOL-W2** yazıldı (aynı kural, `W2_`
  öneki); önce **duman** `1567704` (5 s, kabul: donmuş ≥ 1 ve artık ≤ 1e-4).
  Kullanıcı: *"devam et, araştır, düzelt, kod geliştir, kusursuzlaştır"* →
  ayrıca eklendi: **çok doğruluklu vekil** (`inference/cok_dogruluk.py`,
  Kennedy–O'Hagan; Forrester sınamasında tek katmandan 4×+ iyi), **gerinimle
  kohezyon kaybı** (L1; seçenek, varsayılan kapalı, `--gerinim-yumusama-eps`),
  koni **kenar** açısı + HST/eliptik koni ölçümleri, çözünürlük araştırması
  (LITERATUR §10: literatürün tüm cisim SPH'si de çarpma çevresinde cppr < 1;
  bizim zayıf noktamız **uzak alan**, 3–4× kaba).
