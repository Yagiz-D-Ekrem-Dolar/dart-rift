# ADR-0055 — Gözlemli vektörü "ya hep ya hiç" olmaktan çıkar; krater kutusu ayrı çözülür

**Durum:** (1) **UYGULANDI** (açık opt-in, davranış değişmedi) ·
(2) ÖNERİ (karar kullanıcıda) · **Tarih:** 2026-10-04
**Öncül:** **A114** (ölçüldü: DY2'nin `y`'si `null`), ADR-0045 §5/§8/§10
(krater çapı öldü, derinlik yaşıyor), KAYIT-072, PROTOKOL-HT (Hera mührü)
**Kod:** `inference/forward.py`, `inference/ensemble.py` ·
**Sınav:** `tests/test_a114_istege_bagli_gozlemli.py` (7)

---

## 1. Bağlam

A114 ölçtü: üretim sahnesinin ilk gerçek koşusu (DY2) vekile girecek kaydı
**hiç üretmedi** — `y: null`. Sebep krater çıkarıcısının *haklı* reddi
(çarpma ekseni kutusunda `2` parçacık, gereken `5`). Aynı koşunun `β`'sı
(`3,748`) ve ejekta kesri kusursuzdu ve **onlar da çöpe gitti**.

İki ayrı şey var ve ayrı ayrı çözülmeli:

| # | sorun | niteliği |
|---|---|---|
| **(1)** | tek gözlemlinin reddi **bütün** kaydı düşürüyor | **sağlamlık**; hiçbir sayıyı değiştirmez |
| **(2)** | en iç kutu geometrik olarak aç (`n_bins = 8` → beklenen `1,5` parçacık) | **kilitli gözlemliyi** değiştirir |

## 2. Karar (1) — UYGULANDI, açık opt-in

`gozlenebilirleri_cikar(..., istege_bagli=())` ve
`ensemble_kos(..., nan_izinli=())` eklendi.

- `istege_bagli` içinde `"krater_derinlik"` varsa, krater çıkarıcısının
  `ValueError`'ı **yalnız o bileşeni** `nan` yapar; `β` ve ejekta kesri
  hesaplanıp döner. Gerekçe metni `forward.A114_UYARILARI`'na yazılır —
  **sessiz geçmez**.
- `ensemble_kos`'ta `nan_izinli` dizinlerindeki `nan` kaydı düşürmez;
  **zorunlu** bileşenlerden biri `nan` ise kayıt yine düşer (S4'ün dersi
  korunuyor: `β`'da `nan` affedilmez).
- **İkisinin de varsayılanı boş.** Yani bu commit hiçbir koşunun sonucunu,
  hiçbir kilitli yargıyı ve hiçbir geçmiş sayıyı **değiştirmiyor**. Üretim
  planı bunu açıkça istemek zorunda.

Neden `krater_derinlik` isteğe bağlı olabilir: **çıkarımda kullanılmıyor.**
DART, Dimorphos'un kraterini **görmedi** (Hera görecek). Krater derinliği
bir *öngörü hedefi* (PROTOKOL-HT), bir *kısıt* değil. `β` ve ejekta kesri
ise gözlenmiş kısıtlar (ADR-0053: `M_ejekta` `Y₀`'yu `β`'dan `6,3` kat iyi
sıkıştırıyor). Havuzun kısıtları yüzünden değil, **öngörüsü** yüzünden
ölmesi savunulamaz.

## 3. Öneri (2) — en iç kutu

Ölçülen (A114 tablosu; çarpma yönü kestirildiği için derinlikler gösterge):

| `n_bins` | en iç kutu | beklenen parçacık | DY2 | DK |
|---|---|---|---|---|
| **8 (üretim)** | `0 – 1,5°` | `1,5` | `3` → RED | `4` → RED |
| 6 | `0 – 2,0°` | `2,6` | `5` → RED | `12,98 m` |
| 4 | `0 – 3,0°` | `5,9` | `4,05 m` | `9,07 m` |

Üç seçenek:

- **(2a) `n_bins = 4`.** En ucuz. Ama beklenen sayı `5,9` — eşiğin
  `%18` üstünde; hâlâ bıçak sırtı. ADR-0045'in ölçtüğü sapma da burada en
  büyük (`2 m` gerçek krater → `1,844`, `−%7,8`).
- **(2b) Uyarlanır en iç kutu (önerilen).** En iç kutunun yarı-açısı
  `min_per_bin` parçacık toplanana kadar **büyütülür** ve ulaşılan açı
  raporlanır. Bıçak sırtı kalkar, yanlılık **ölçülebilir** olur (açı
  raporlandığı için). Kilitli gözlemliyi değiştirir → kullanıcı kararı,
  ve değişiklik **yan yana** (`derinlik_uyarlanir`) alan olarak girer;
  eski `depth` dokunulmaz.
- **(2c) Krateri havuzdan çıkar, HT'de daha yüksek çözünürlükte ölç.**
  Havuz `96` koşu; HT posteriorun `θ`'sında **birkaç** koşu. Orada orta
  merdiven (`4,5×` parçacık) karşılanabilir ve kutu 0 dolu olur.

- **(2d) Ölçüyü değiştir: `krater_yerdegistirme` (2026-10-04'te bulundu).**
  A19'un çaresi olarak **zaten yazılmış** ve sınavları geçiyor
  (kımıldamamış pürüzlü yüzeyde cebirsel olarak `0`, gerçek `12 m` çukuru
  görüyor, çözünürlükten bağımsız) — ama `src/` ve `scripts/` içinde
  **hiç kullanılmıyor**. Derinliği *yer değiştirmeden* ölçtüğü ve
  `−min(profil)`'i bütün kutulardan aldığı için **kutu 0 açlığına
  yapısal olarak bağışık**: A114'ün kök nedeni ortadan kalkar ve A19 de
  kapanır. Mevcut koşularda denendi: **hiç reddetmedi**. Ama üç koşuda
  `0,000 m` verdi ve sebebi doğru çarpma ekseni olmadan **söylenemez**
  (kestirilen eksenle ölçüldü). Bu yüzden **karar ölçüme bırakıldı:**
  iki ölçü artık her koşuda yan yana hesaplanıyor
  (`fizik_tani["krater_yerdegistirme"]`, ek maliyet yok) ve ilk gerçek
  karşılaştırmayı PROTOKOL-DO/DC verecek.

**Önerilen birleşim: (1) + (2c), (2b) ise HT'den önce.** Yani havuz
`krater_derinlik`'i isteğe bağlı sayar ve `nan` yazar; Hera öngörüsü için
krater, ayrı ve daha yüksek çözünürlüklü bir turda ölçülür. Bu, hem havuzu
kurtarır hem de krater gözlemlisini "ucuz ayarla zorlama" baskısından
çıkarır.

## 4. Sonuçları

- **Havuz kurtulur:** A114 olmadan koşuların kabaca yarısı `y: null`
  dönecekti ve düşenler *yanlı* seçilmiş olacaktı (çarpma ekseni çevresine
  daha az parçacık düşenler).
- **Vekil `krater_derinlik` için eksik veriyle çalışır.** Çok doğruluklu
  vekil (`cok_dogruluk.py`) bileşen başına eğitildiği için `β` ve ejekta
  kesri etkilenmez; krater vekili HT turunun verisiyle kurulur.
- **PROTOKOL-HT'nin ön koşulu değişir:** mühürlü krater öngörüsü, havuzun
  vekilinden değil **kendi** turundan gelir. HT yeniden yazılırken bu
  açıkça yazılacak (henüz yazılmadı).
- **Risk:** `nan` yazan koşu sayısı sessizce büyürse fark edilmemesi.
  Çare: `A114_UYARILARI` sayılır ve havuz raporu **beklediğini sayar**
  (kural 8) — kaç koşuda hangi gözlemlinin ölçülemediği yazılır.

## 5. Reddedilen seçenekler

- **Krater reddini `0`'a çevirmek.** 2026-08-09'da tam bu yapılıyordu ve
  ölçüldü: gerçek derinlik `2 → 12 m` değişirken rapor `0` diyordu. Geri
  dönmek kusuru geri getirmek olur.
- **`min_per_bin`'i `2`'ye düşürmek.** Kutu 0'ı "geçirir" ama `95.`
  yüzdelik iki parçacıktan okunur; sayı gürültüdür. Eşiği gevşetmek
  ölçümü düzeltmez, **görünür** yapar.
- **Varsayılanı değiştirip krateri hep isteğe bağlı saymak.** Sessiz
  davranış değişikliği olur ve bir gün gerçek bir krater gerilemesi
  `nan` olarak sessizce geçer. Opt-in şart.
- **Çözünürlüğü havuzda yükseltmek.** UY2 ölçtü: orta merdiven `4,5×`
  parçacık; havuz `~750` yerine `~3400 GPU-saat` olur. Bütçe yok.
