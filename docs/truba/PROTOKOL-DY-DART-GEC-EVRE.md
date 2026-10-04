# Protokol DY — DART sahnesinin **geç evre modeliyle ilk** koşusu

**Yazıldı:** 2026-09-28, **DY koşusundan ÖNCE**. **Öncül:** KAYIT-064
(U/V: `HİÇBİR VARYANT ULAŞMIYOR`, en iyi `β ≈ 2,05` @ 0,2 s), PROTOKOL-UG
(üretim `t_geçiş = 1,0 s`), KAYIT-070 §3 (**A108** kütle tutarlılığı),
ADR-0050/0052. **Rapor:** `scripts/dy_dart_raporu.py` → `S_DY.json` (kilitli).

---

## 1. Neden

Geç evre modelinin **tamamı kıyas sahnesinde** doğrulandı (W2, UA, UY, UG,
A98–A105: 75 m homojen küre, dik çarpma, tek küre mermi). **Gerçek DART
sahnesi bu modelle hiç koşulmadı.** Bilinmeyenler: kararlılık, maliyet,
geçerlilik denetimleri ve — en önemlisi — `β`'nın nereye düştüğü.

U/V'nin negatif sonucu (`β ≈ 2,05`, gözlem `3,12 ± 0,34`) `0,2 s`'de
kesilmiş koşulardandı; W2 aynı anda `β ≈ 1,95` verip 600 s'de `3,7–4,4`'e
çıktı. **Soru:** aynı şey DART sahnesinde de oluyor mu?

## 2. Tasarım (tek koşu)

| ne | değer | gerekçe |
|---|---|---|
| şekil | elipsoit `88,5 × 87 × 58 m` | Daly ve diğ. 2023 |
| yığın yoğunluğu | **`2376 kg/m³`** | **A108**: bu hacimde `4,3e9 kg`'ı tutturan değer; gözlenen `β` bu kütleyle türetildi |
| mermi | **üç küre** (`%88 + 2 × %6`, `2,215 m` aralık), `579,4 kg`, `6144,9 m/s`, `ρ = 1000 kg/m³` | Daly Tablo 1; üç küre L9 (Owen 2022); yoğunluk L1/L2'nin "eşdeğer kütleli düşük yoğunluklu" pratiği (uzay aracı katı alüminyum değil) |
| çarpma açısı | `17°` (normalden) | Daly Tablo 1 |
| blok modeli | `SAHNE` varsayılanı (`r 14–42 m`, `f = 0,25`) | **A109 kilitli değil**; bu koşu varsayılanı kullanır ve seçimi *bağlamaz* |
| `θ` | `α_b = 1,15`, `Y₀ = 10 Pa`, `f = 0,25` | W2 kıyasıyla aynı `Y₀`; literatürün en iyi bölgesi (`< birkaç Pa – 500 Pa`) |
| merdiven / geçiş / süre | kaba, `t_geçiş = 1,0 s`, `600 s` | UG'nin kilitli üretim değeri |

**Kapsam dışı (bilerek):** çarpma yerinin merkezden `25 m` kaçıklığı
(`--nisan` ile ayrı ayarlanır), gerinim yumuşaması, çekme dayanımı (A105
kararı bekliyor). Bunlar bu koşuda **yok** ve sonuç öyle okunur.

Maliyet kestirimi `W2_Y10_g1p0`'dan (`3:56`) parçacık oranıyla: `~5 GPU-saat`.

## 3. Geçerlilik

`gecerli = True` (sonluluk, enerji `≤ %5`, momentum defteri `≤ 1e-3`,
kurucu sınır) **ve** `t = 600 s`. Değilse genel **OKUNMAZ** ve `β`
raporlanmaz.

## 4. Kilitli yargı

Gözlem bandı `period_interface.dart_beta_budget` ile: **`β = 3,12 ± 0,34`**
(`1σ`). Model tarafında **ölçülmüş** belirsizlikler paydaya girer
(`tarih_esleme.model_eksikligi_kaynakli`): `gerceklem_beta = 0,033`,
`cozunurluk_uzak = 0,004`, `plato = 0,01`, `carpma_yeri = 0,10`
(**`β − 1` üzerinden**, karelerin toplamı). Kesme Pukelsheim `3σ`:

    I = |β_model − 3,12| / √(σ_gözlem² + σ_model²)

| yargı | koşul |
|---|---|
| **MODEL GÖZLEME ULAŞIYOR** | `I < 3` **ve** `β_model ≥ 3,12 − 0,34` |
| **MODEL AŞIYOR** | `I ≥ 3` ve `β_model > 3,12` |
| **MODEL ULAŞMIYOR** | `I ≥ 3` ve `β_model < 3,12` |

> **Bu tek koşu `θ`'yı çıkarmaz.** Yalnız şunu söyler: geç evre modeli DART
> sahnesinde gözlemin *mertebesine* ulaşıyor mu. "Ulaşıyor" çıkarsa U/V'nin
> negatif dalı kapanır ve havuz anlamlı olur; "ulaşmıyor" çıkarsa havuzdan
> önce fizik tartışılır.

## 5. Kapı olmayan tanılar

`β` iki yöntem farkı, `impuls_sekli` (kıyas sahnesiyle **mekanizma**
karşılaştırması), `M_ejekta` (gözlem `1,6 ± 0,3e7 kg`), koni açıları
(**A95**: gözlemle kıyaslanmaz), blok çözünürlüğü, dondurulan sayı,
enerji sapması, duvar süresi, `kutle_tutarliligi`.

---

## 6. DY2 tekrarı ve DK şekil kontrolü (2026-09-29, **koşulardan ÖNCE**)

### 6.1 Neden tekrar

`DY_dart_g1p0` koşusu **§2'de yazılan sahneyi gerçekleştirmedi** (**A112**):
merdiven inceltmesi kabuğu küre olarak kurduğu için elipsoit, inceltmeden
sonra neredeyse küreye dönüştü (kısa eksen `58 → 73 m`) ve kütle `%5,5`
arttı. Koşu geçerliydi ve kilitli yargı hesaplandı (`MODEL AŞIYOR`,
`β = 4,719`) — ama o yargı **elipsoit DART sahnesine ait değil**.

**W → W2 emsali:** DY'nin yargısı kayıtta **olduğu gibi kalır** ve
**OKUNMAZ** sayılır; koşu `DY2` önekiyle tekrarlanır. §4'ün kuralı
**değişmedi**.

### 6.2 DY2'de değişen iki şey (ve yalnız bu ikisi)

| | DY | **DY2** |
|---|---|---|
| inceltme kabuğu | küre (A112) | **sahnenin şekli** (elipsoit) |
| yığın yoğunluğu | `2376` (yanlış hacimden, A111) | **`2307`** (kalibre: kurulan sahne `4,3000e9 kg`) |

Geri kalan her şey §2 ile aynı. Kod: A112 düzeltmesini içeren commit.

### 6.3 DK — şekil kontrol kolu (**yeni, kilitli**)

NUSAP soy kütüğü (KAYIT-070 §2) `hedef_sekli = 0,20` teriminin
**doğrulamasının sıfır** olduğunu gösterdi: başka bir kodun, başka bir
sahnede ölçtüğü sayı. DY2 zaten elipsoit koluyken, yanına **hacim-eşdeğer
küre** kolu konursa bu terim **bizim kodumuzda ölçülmüş** olur.

**DK:** DY2 ile aynı her şey; yalnız `shape = icosphere`,
`R = 76,44 m` (hacim-eşdeğer) ve yoğunluk aynı kütleyi (`4,3e9 kg`)
tutturacak şekilde kalibre.

**Kilitli ölçüm:** `σ_şekil = |b_elipsoit − b_küre| / b_elipsoit`
(`b = β − 1`, 600 s). Bu değer `MODEL_EKSIKLIGI_KAYNAKLI["hedef_sekli"]`
yerine **ölçülmüş** terim olarak geçer (eski `0,20` satırı yerinde kalır,
kaynağıyla birlikte).

**Yorum (koşudan önce):** `σ_şekil` büyükse (`> 0,15`) şekil, bütçenin
en büyük terimi olmayı sürdürür ve gerçek şekil modeline (`obj`) geçmek
gerekir; küçükse (`< 0,05`) küresel sahneler de savunulabilir ve bütçe
terimi küçülür.

### 6.4 Okuma notu (**koşulardan SONRA**, 2026-10-04 — kural değişmedi)

Ölçüm `σ_şekil = 0,0086` çıktı, yani §6.3'ün kilitli yorumunun "küçük"
dalı: **küresel sahneler savunulabilir**. Bu yorum olduğu gibi **geçerli
ve `β` için doğru**. Yanına düşülen not: aynı iki kol `β` dışındaki
gözlemlilerde ayrılıyor — `M_ejekta` `%56`, koni açısı `%46`, `t50`
**2,6 kat**. `M_ejekta`'da elipsoit gözleme `1,2σ`, küre `4,9σ` uzakta.

**Sonuç:** "küre savunulabilir" **yalnız `β` için** okunur; `β` dışındaki
hiçbir gözlemli için okunmaz. Üretim havuzu (zaten planlandığı gibi)
elipsoit sahnede koşar. Ayrıntı ve gerekçe: KAYIT-072 §3–§4.

---

## 7. DM ve DT — bütçenin kalan iki ödünç terimini ölçmek (2026-10-04, **koşulardan ÖNCE**)

### 7.1 Neden

DY2/DK, `hedef_sekli` terimini `0,20`'den **ölçülmüş `0,009`**'a indirdi
(§6.3, KAYIT-072). NUSAP soy kütüğünde (KAYIT-070 §2) doğrulaması **sıfır**
kalan iki terim var ve ikisi de DY2 sahnesinde tek koşuyla ölçülebilir:

| terim | şu anki değer | kaynağı |
|---|---|---|
| `mermi_geometrisi` | `0,15` | L9 (Owen 2022), **başka kod, başka sahne** |
| `gerceklem_beta` | `0,033` | U/V havuzu — **eski model**, `0,1–0,2 s` |

### 7.2 Tasarım (iki koşu, DY2 ile aynı her şey)

| kol | değişen tek şey |
|---|---|
| **DM** | mermi **tek küre** (üç küre yerine); kütle/hız/yoğunluk aynı |
| **DT** | sahne tohumu `99991111` (DY2: `20260906`); blok dizilimi değişir |

### 7.3 Kilitli ölçümler

`b = β − 1` (600 s). Her iki kol da `gecerli` ve 600 s'ye ulaşmış olmalı;
değilse ilgili ölçüm **OKUNMAZ** (terim ödünç değeriyle kalır).

- **`σ_mermi = |b_DY2 − b_DM| / b_DY2`** → `mermi_geometrisi` yerine geçer.
- **`σ_gerçeklem(DART) = |b_DY2 − b_DT| / (ortalama b) / √2`** →
  `gerceklem_beta` yerine geçer (iki örnekten sd kestirimi, KAYIT-070 §1
  ile aynı formül).

**Yorum (koşudan önce):** her iki terim de `< 0,05` çıkarsa bütçenin
ödünç kalan kısmı biter ve model eksikliği **tamamen ölçülmüş** olur;
`> 0,15` çıkarsa o terim bütçenin başatı olur ve ayrıca çalışılır.

---

## 8. DC — matris çekme dayanımının DART sahnesindeki bedeli (2026-10-04, **koşudan ÖNCE**)

### 8.1 Neden

**A105** kıyas sahnesinde ölçtü: Mohr-Coulomb uç kesmesi
(`T_m = Y₀/μ_f`) açılınca `β` `%23` düşüyor (`3,686 → 2,854` kaba;
`3,978 → 3,074` orta). [ADR-0056](../adr/ADR-0056-a105-matris-cekme-dayanimi.md)
üretimde çekmenin **kapalı** kalmasını öneriyor ve `−%23`'ü bütçeye
**eklemiyor**; yerine her raporda duran bir **koşullu duyarlılık** cümlesi
yazıyor. Ama o cümledeki sayı (`3,75 → ~2,89`) **kıyas sahnesinden
taşınmış bir orandır.** DC onu DART sahnesinde ölçer.

### 8.2 Tasarım (tek koşu)

DY2 ile **birebir aynı** (§2 + §6.2); değişen tek şey: `--matris-cekme-yok`
**kaldırılır**, yani matris çekmesi Mohr-Coulomb uç kesmesiyle **açık**
(`T_m = Y₀/μ_f`, `Y₀ = 10 Pa`, `μ_f = 0,6` → `T_m ≈ 16,7 Pa`).

Maliyet kestirimi DY2'den (`4:50:53`): **`~5 GPU-saat`**.

### 8.3 Geçerlilik

§3 ile aynı: `gecerli = True`, `t = 600 s`, `kutle_tutarliligi` tutarlı.
Değilse ölçüm **OKUNMAZ** ve ADR-0056'nın koşullu cümlesi kıyas sahnesinin
oranıyla (`−%23`) yazılı kalır.

### 8.4 Kilitli ölçüm ve yargı

`b = β − 1` (600 s). **`σ_çekme = |b_DY2 − b_DC| / b_DY2`.**

| yargı | koşul | sonucu |
|---|---|---|
| **ÇEKME KIYASLA AYNI** | `|σ_çekme − 0,23| ≤ 0,05` | koşullu cümle **ölçülmüş** sayıyla yazılır; kıyas sahnesinden taşıma gerekçelenmiş olur |
| **ÇEKME DART'TA DAHA ETKİLİ** | `σ_çekme > 0,28` | koşullu cümle büyür; ADR-0056 §4 yeniden açılır (seçim hâlâ fiziksel, ama bedeli daha büyük) |
| **ÇEKME DART'TA DAHA ETKİSİZ** | `σ_çekme < 0,18` | koşullu cümle küçülür; A105'in "çözünürlükten 4 kat büyük" uyarısı DART sahnesi için yumuşar |

**Bu ölçüm bir KAPI DEĞİL.** Hangi sonuç çıkarsa çıksın ADR-0056'nın
kararı (çekme **kapalı**) değişmez: o karar fiziksel gerekçeyle ve
koşulardan **önce** verildi. DC yalnız **bedelini** ölçer.

> Tersi yapılırsa — "DC'de `β` daha iyi tuttu, çekmeyi açalım" — sonuca
> göre model seçmiş olurduk. Kural 6 bunu yasaklıyor ve bu paragraf
> koşudan önce yazıldı.

### 8.5 Kapı olmayan tanılar

§5 ile aynı, artı **ejekta ayrışması** (KAYIT-073): çekme açıkken
`M_kaçan`/`v_ort`/`kos_ort` hangi yönde değişiyor? Götürme hâlâ var mı?
Bu, `−%23`'ün *hangi çarpandan* geldiğini söyler.

