# SAVUNMA NOTU — DART-RIFT

**Kime:** araştırmacının kendisine. **Niçin:** `docs/DEVAM-BITIS3.md` §10,
projenin **en büyük riski** olarak şunu yazıyor — *"kullanıcının her modülü
kendi cümleleriyle anlatabildiği bir savunma notu gerekli"*.
**Tarih:** 2026-11-01 · **Eşlik eden belge:** [`YAPAY-ZEKA-BEYANI.md`](YAPAY-ZEKA-BEYANI.md)

> **Nasıl kullanılır.** §1 ve §4 **ezberlenir**. §3 bir kere okunur,
> sonra kapatıp kendi cümlelerinle yüksek sesle tekrar edilir — bu notu
> okumak savunma değildir, tekrar etmek savunmadır. §6'daki soruların
> **cevabı değil, cevabın kaynağı** ezberlenir: hangi dosyayı
> açacağını bilmek yeter.

---

## 1. Doksan saniyede proje (ezberlenecek)

> NASA'nın DART uzay aracı 2022'de Dimorphos adlı küçük bir astroide
> çarptı ve yörünge dönemini `33` dakika değiştirdi. Çarpmadan çıkan
> ejekta, aracın kendi momentumundan `β ≈ 3,6` kat fazla momentum
> aktardı. Bu `β` sayısı astroidin **içinin** ne kadar gözenekli ve ne
> kadar zayıf olduğuna bağlı — çünkü zayıf, gözenekli bir cisim daha
> çok malzeme fırlatır.
>
> Ben bu ilişkiyi tersine çevirmeye çalıştım: ölçülen `β`'dan iç yapıyı
> **çıkarmak**. Bunun için astroidi kendi yazdığım bir GPU parçacık
> simülasyonunda (SPH) `96` farklı iç yapıyla çarptırdım, çıkan `β`'ları
> bir vekil modele öğrettim ve Bayes çıkarımıyla hangi iç yapıların
> gerçek gözlemle bağdaştığını buldum.
>
> Sonuç: `β` üç parametreden **yalnız birini** kısıtlıyor — matris
> dayanımı `Y₀`. Gözeneklilik ve blok kesri tek bir ölçümden
> çözülmüyor; bunu kanıtladım ve kilitledim. Ve 2027'de Hera uzay aracı
> Dimorphos'a vardığında ölçeceği iki niceliğe (dönme hızı ve krater)
> **önceden mühürlü** öngörü bıraktım, SHA-256 ile çivili.

**Son cümle hiç atlanmaz** — jürinin aklında kalan şey o.

## 2. Neyi başardım, neyi başaramadım

Bu tablo **ilk önce** söylenir, sorulmayı beklemeden. Olumsuzu kendin
söylersen güç kazanır; jüri bulursa kaybeder.

| başardığım | başaramadığım |
|---|---|
| Gerçek görev verisiyle çalışan tam bir çıkarım zinciri | **Niceliksel yakınsama**: çözünürlük iki katına çıkınca `Y₀` eşlemesi `×3,22` kayıyor (yanlılık, saçılma değil) |
| `β`'nın kaç yön kısıtladığının **kanıtı** (`n_yön = 1`) | `α_b` ve `f`'yi çözmek — tek gözlemle **mümkün değil**, bunu gösterdim |
| Çıkarım makinesinin kalibre olduğunun sınavı (SBC, 200 tekrar) | `β`'yı doğrudan gözlemli olarak kullanmak (S9: her ölçekte ayrıklaştırma tabanında) |
| İki **mühürlü** Hera ön kaydı (dönme + krater) | Üç noktalı uzamsal yakınsama (S10: `R3` için `224` saat, sınır `48`) |
| Kazı akışını neyin durdurduğunun **mekanizma kanıtı** | Üretim modelinde granüler çekme (S12) |
| Olumsuz sonuçların hepsinin yayımlanması | — |

> **Tek cümlelik dürüst sınır:** *"Hesapladığım posterior bir **yöntem
> gösterimidir**, fiziksel öngörü değildir; `Y₀`'nın mutlak değeri
> yakınsamıyor."* Bu cümle `README.md`'de yazılı ve orada duruyor.

## 3. Modül haritası — her parçayı kendi cümlenle anlat

`src/dartrift/` altında `26 916` satır var. Hepsini bilmen gerekmiyor;
**yedi kutu** bilmen gerekiyor. Her satırın son kolonu senin
söyleyeceğin cümledir.

### 3.1 Çözücü — `warp_core/`

| dosya | ne yapar | senin cümlen |
|---|---|---|
| `kernel_fn.py` | Wendland C2 çekirdeği (FP64) | "Parçacıklar birbirini nokta gibi değil, yumuşak bir ağırlık fonksiyonuyla görüyor." |
| `density.py`, `forces.py` | SPH yoğunluk ve kuvvet toplamları | "Her parçacığın yoğunluğunu komşularından topluyorum, kuvveti de basınç farkından." |
| `eos_tillotson.py` | Tillotson hâl denklemi | "Kayanın basıncını yoğunluk ve iç enerjiden veren, çarpma hızlarında kullanılan standart denklem." |
| `porosity_palpha.py` | P–α gözeneklilik | "Gözenekli kaya önce **çöküyor**, sonra sıkışıyor; P–α bu iki evreyi ayırıyor." |
| `damage_gradykipp.py` | Grady–Kipp hasarı | "Kaya çekmede çatlıyor; çatlak yoğunluğunu Weibull dağılımıyla izliyorum." |
| `strength_lundborg.py` | Lundborg akma yüzeyi | "Basınç arttıkça dayanım artıyor ama bir tavana oturuyor; sürtünme katsayısı `μ_f = 0,6`." |
| `gravity_tree.py` | Barnes–Hut çekim | "Saatler süren geç evrede ejektanın geri düşmesi için kendi çekimi şart." |
| `timestep.py`, `integrator.py` | CFL adımı, zaman ilerletme | "Adım boyu ses hızının izin verdiği kadar; erken evrede `4,4` mikrosaniye." |

**Niçin GPU:** `96` noktanın her biri yüz binlerce adım. Ölçülen: `600`
saniyelik koşu `≈ 390 000` adım, nokta başına `~5` GPU-saat. CPU'da
proje bitmezdi.

### 3.2 Sahne kurulumu — `setup/`

| dosya | ne yapar | senin cümlen |
|---|---|---|
| `shape_mesh.py`, `scene.py` | Dimorphos'un gerçek şekli: `88,5 × 87,0 × 58,0` m yarı eksen | "Küre değil; DART'ın çektiği fotoğraftan gelen üç eksenli şekil." |
| `rubble_generator.py` | blok + matris karışımı | "İç yapı iki malzemeli: sert bloklar ve onları tutan zayıf matris." |
| `refine.py`, `coarsen.py`, `blok_cozunurluk.py` | merdivenli çözünürlük | "Çarpma noktası ince, uzak bölge kaba — yoksa parçacık sayısı patlıyor." |
| `impactor.py` | DART mermisi: `579,4` kg, `6 144,9` m/s, `17°` | "Mermi gerçek uzay aracının kütlesi ve hızıyla, alüminyum olarak." |
| `settling.py` | çarpma öncesi oturma | "Cisim kendi çekimi altında dengelenmeden çarpmazsam başlangıç gerilmesi sahte olur." |

### 3.3 Gözlenebilirler — `observables/`

Bu kutu **en çok soru gelecek** yer, çünkü ölçtüğüm şeyler burada.

| dosya | ne yapar | senin cümlen |
|---|---|---|
| `momentum_transfer.py`, `beta_gelenegi.py` | `β` hesabı | "`β = 1 + ejektanın geri tepmesi / merminin momentumu`. Geleneğe uygun tanım kullandım, kendi tanımımı değil." |
| `kacis.py` | kaçan parçacık ölçütü | "Bir parçacık, hızı kaçış hızını (`8,2` cm/s) aşıyor **ve** başladığı yerden iki çekirdek desteği uzaklaşmışsa kaçmış sayılıyor." |
| `ejecta_catalog.py`, `ejekta_ayrismasi.py` | kütle–hız dağılımı | "Ejektanın hız dağılımı ölçekleme yasasına uyuyor: `μ = 0,463 ± 0,016`, literatür `0,40–0,55`." |
| `crater_shape.py` | krater yüzeyi ve derinliği | §3.6'da ayrıntılı — **buraya hazırlıklı gel.** |
| `momentum_defteri.py` | momentum korunumu denetimi | "Toplam momentum kapanıyor: artık `1,15e-14`. Kapanmazsa sonuç okunmuyor." |
| `dart_gozlemleri.py` | gerçek DART sayıları | "Gözlem değerleri Cheng vd.'den: `β = 3,61` (`−0,25/+0,19`), hedef kütlesi `4,3e9` kg." |

### 3.4 Çıkarım — `inference/`

| dosya | ne yapar | senin cümlen |
|---|---|---|
| `design.py` | Latin hiperküp tasarımı, `96` nokta | "Parametre uzayını rastgele değil, dengeli tarayan bir tasarımla örnekledim." |
| `gp_vekil.py`, `surrogate.py` | Gauss süreci vekili | "`96` koşuyu her yere tekrar koşamam; aralarını bir Gauss süreciyle dolduruyorum ve o da kendi belirsizliğini veriyor." |
| `kalibrasyon.py` | vekil varyansının kalibrasyonu (Bachoc) | "Vekilin 'ne kadar emin olduğu' da sınandı; ham değeri kullanmadım." |
| `tanimlanabilirlik.py` | Fisher bilgisi, `n_yön` | "Üç parametrenin kaçının çözülebildiğini Fisher bilgi matrisinin özdeğerlerinden saydım: **bir**." |
| `tarih_esleme.py` | tarih eşlemesi (history matching) | "Her noktanın gözlemden kaç model-hatası uzakta olduğunu ölçüp eşiği aşanları eledim; `%34` bağdaşır kaldı." |
| `posterior.py` | ızgara posterioru | "Bayes posteriorunu ızgarada hesapladım — MCMC'ye gerek yok, üç boyut." |
| `onsel_denetimi.py` | önsel duyarlılığı | "Sonucun önsele ne kadar bağlı olduğunu ayrı ölçtüm ve o sınavın gücünün düşük olduğunu yazdım." |
| `ic_ice_tasarim.py` | iç içe tasarım | "İnce koşuları kaba havuzun **alt kümesi** olarak seçtim; yoksa çözünürlük karşılaştırması adil olmaz." |

### 3.5 Doğrulama — `validation/` (28 dosya)

Burada tek cümle yeter ama **güçlüdür**:

> "Çözücüyü hedef probleme uygulamadan önce cevabı bilinen problemlerde
> sınadım: Sod şok tüpü, Sedov patlaması, Riemann problemi, plaka
> çarpması, çekim alanı, korunum yasaları. `validation/` altında `28`
> ayrı sınav dosyası var. Bunlar geçmeden hedef probleme geçmedim."

Jüri "doğru çalıştığını nereden biliyorsun" dediğinde cevap bu.

### 3.6 Krater operatörü — **hazırlıklı gel**

Bu, projenin en öğretici hikâyesi ve jüri burayı sevecek.

**Olan şey:** Krater derinliği, havuzun `47`/`96` noktasında
okunamıyordu ve bu kusur (`A86`) bir yıl açık kaldı. Sebep bulundu:
doluluk alanının eş-yüzeyi iki durum için **ortak** pencerelenince,
yukarı fırlayıp kaçmayan malzeme pencereyi şişiriyor ve arama referans
yüzeye hiç inemiyordu.

**Düzeltme tek başına yanlış olurdu.** Pencere durum başına kurulunca
`nan` kalkıyor, ama yerine gelen sayı krater derinliği **değil**,
eksende duran örtünün tepesi. Sentetik levhada ölçtük: örtü `y` metreye
kaldırılınca derinlik `−(y + 0,913)` m, eğim `−1,000 ± 0,001`. Yani tek
başına yayımlansa **47 dürüst eksik, 47 yanlış sayıya** dönüşecekti.

**Çözüm iki adım:**
1. **Red kapısı** (ADR-0062): merkezde son yüzey, referans yüzeyin bir
   çekirdek desteği (`2h = 1,4` m) üzerindeyse derinlik **ölçülemez** ve
   sayı yerine sebep döner.
2. **Tarama yönü** (ADR-0063): yüzey artık **içten dışa** taranıyor;
   üstteki boşluk ve ondan sonraki ayrı yığın yapısal olarak ıskalanıyor.

**Sonuç:** krater `46` → **`66`/`96`** noktada okunuyor; yeni `20`
nokta bağımsız bir ikinci tanıyla **sıfır çelişkiyle** doğrulandı, eski
`46` nokta makine hassasiyetinde (`1,9e-14`) aynı kaldı. Kalan `13`'te
iki tanı ayrışıyor ve orada sayı **yayımlanmıyor**.

> **Senin cümlen:** "Bir ölçüm aracımın sessizce yanlış sayı
> döndürdüğünü buldum. Düzeltmenin kendisi de yanlıştı — onu da ölçtüm.
> Sonunda aracı iki bağımsız tanımla çapraz doğruladım ve uyuşmayan
> `13` noktayı **yayımlamadım**."

**Eşiğin uydurma olmadığını göstermen gerekirse:** çalışan noktalar
`+0,75`/`+0,89` m, düşenler `−46,4` m veriyor. Eşik `−1` ile `−45` m
arasında **herhangi bir yerde** aynı sınıflamayı verir. Ayarlanmış bir
sayı değil.

### 3.7 Mühürleme — `docs/onkayit/`

| dosya | ne |
|---|---|
| `ONKAYIT_HERA_SPIN_uretim96.json` | dönme hızı öngörüsü, SHA-256 `6464cf81…` |
| `ONKAYIT_HERA_KRATER_uretim66.json` | krater öngörüsü, SHA-256 `1b3b811e…` |

> **Senin cümlen:** "Hera 2027'de varmadan önce ne öngördüğümü yazdım,
> dosyanın SHA-256 özetini aldım ve commit'ledim. Veri geldiğinde
> öngörüyü değiştiremem — değiştirsem özet tutmaz. Bilim böyle
> yanlışlanabilir olur."

## 4. Ezberlenecek on sayı (ve nereden geldikleri)

| sayı | ne | kaynak |
|---|---|---|
| `β = 3,61` (`−0,25/+0,19`) | DART'ın ölçülen momentum çarpanı | `observables/dart_gozlemleri.py:46` |
| `96` | üretim havuzundaki iç yapı noktası (`96/96` kapandı) | `docs/sonuclar/` |
| **`n_yön = 1`** | `β`'nın kısıtladığı yön sayısı — **kilitli yargı** | [KAYIT-079](../defter/KAYIT-079_2026-10-16_UP-gozlemli-secimi-ve-n-yon.md) |
| `%34,04` · `I_min = 0,325` | tarih eşlemesinde bağdaşır hacim; model gözleme **ulaşıyor** | [KAYIT-080](../defter/KAYIT-080_2026-10-16_UP-onsel-duyarliligi-ve-tarih-eslemesi.md) |
| `Y₀ ≈ 18,7` Pa | posteriorun kipi (önsel kutusunun **içinde**) | `docs/sonuclar/README.md` §12 |
| `0,882` | `Y₀`'daki büzülme (önselden ne kadar öğrenildi) | aynı |
| `μ = 0,463 ± 0,016` | ejekta ölçekleme üsteli; Housen–Holsapple `0,40–0,55` | `README.md` S6 |
| `−15,19` MPa | matrisin **sahte** çekme dayanımı — ana mekanizma bulgusu | `README.md` cümle 1 |
| **`×3,22`** | çözünürlük iki katına çıkınca `Y₀` eşlemesindeki **yanlılık** | [KAYIT-085](../defter/KAYIT-085_2026-10-22_cozunurluk-farki-YANLILIK-cikti.md) |
| `66`/`96` | krateri çapraz doğrulanmış okunan nokta | [KAYIT-091](../defter/KAYIT-091_2026-10-28_icten-disa-tarama-olculdu-66-nokta-capraz-dogrulandi.md) |

**Hiçbir sayıyı hatırlamıyorsan:** "o sayı `docs/sonuclar/README.md`'de
yazılı, açıp gösterebilirim" demek **tam puan**lık cevaptır. Sayı
uydurmak sıfırdır.

### 4.1 En güçlü cümle — ve bir ucunun zayıf olduğu (2026-11-05)

Bu, projenin **genellenebilir** sonucudur ve §1'den sonra en çok işine
yarayacak cümledir:

> DART'ın ölçümü asteroidin iç yapısındaki üç bilinmeyenden
> **matris dayanımını** ölçüyor: öğrenilen yönün `Y₀` payı ortanca
> **`0,999`**, baskın eksen `90/96` noktada `Y₀`. İkinci yön tasarımın
> **hiçbir** noktasında öğrenilebilir eşiğe ulaşmıyor (`λ₂` maks
> `33,09`, eşik `36`); iki yön arasındaki bilgi farkı ortancada
> **`~300` kat**. Ve bunu **daha hassas ölçerek düzeltemezsin**:
> `σ`'yı `1000` kat küçültmek `λ₂`'yi yalnız `2,35 → 4,17` taşıdı,
> çünkü `σ` bir ölçümün **ağırlığını** değiştirir, **yönünü** değil.
> İkinci bir bilinmeyen için **gradyanı gerçekten farklı** bir ölçüm
> gerekir.

Kaynak: [KAYIT-097](../defter/KAYIT-097_2026-11-05_esdogrusallik-96-noktada-olculdu.md).
Bu Dimorphos hakkında değil **gelecek görevler için tasarım
ifadesi**dir — genellenebilir olan kısım tam bu.

**İki şeyi de söylemek zorundasın, yoksa yakalanırsın:**

1. **`n_yön = 1`'in *rankı* buluş değil, aritmetiktir.** Tek skaler
   ölçüm en çok bir birleşim verir; bunu `tanimlanabilirlik.py`'nin
   kendi belgesi yazıyor. Buluş olan şey **hangi** yön, **ne kadar**,
   ve hassasiyetin kurtarmadığı.
2. **Sıralamanın `f` ucu ZAYIF.** `Y₀ ≫ α_b ≫ f` diyoruz ama `f` (blok
   kesri) için doğru cümle *"önemsiz"* değil,
   **"bu tasarımda ölçülemiyor"**. Sebebi: üretim sahnesinde cisimde
   yalnız `~7` büyük blok var ve her `θ` noktasında **tek tohum**, yani
   `f`'i değiştirmek yerleşimi de değiştiriyor. Literatür (L8, tam
   metin okundu) blok kütle kesrinin `β`'yı `%60`'a kadar
   **değiştirdiğini** ölçüyor ve ona inanmak için sebep var.
   Ayrıntı: `docs/LITERATUR-DART-SIMULASYONLARI.md` §11.5; açık kusur
   **A109**.

> Jüri *"blok kesri önemsiz mi"* diye sorarsa cevabın **"hayır,
> ölçemedik"** olmalı. Bu ikisi aynı şey değil ve farkı bilmek
> güçlendirir.

## 5. Yöntem savunması — niçin bu biçimde kurdum

Jüri "neden bu kadar bürokrasi" diye sorarsa, cevap tek bir cümlede
toplanır: **sonucu gördükten sonra kural değiştirmemek için.**

| uygulama | ne sağlar | kanıt |
|---|---|---|
| **Protokoller koşudan önce** commit'lenir | sonuç beğenilmeyince eşik oynatılamaz | commit tarihleri `docs/truba/PROTOKOL-*.md` |
| **Mühürlü ön kayıt** (SHA-256) | öngörü, veri geldikten sonra düzeltilemez | `docs/onkayit/` |
| **Hiçbir satır silinmez** | düzeltme NOT olarak eklenir, hata görünür kalır | `CLAUDE.md` kural 5 |
| **Her rapor beklediğini sayar** | eksik kampanya sessiz geçmez | `CLAUDE.md` kural 8 |
| **Kusur kaydı açık** (`114` kayıt, `87` açık) | bilinen zayıflıklar gizlenmiyor | `docs/FAZ4-SIKINTI-RAPORU.md` |
| **Olumsuz sonuç yayımlanır** | S9/S10/S11/S12 düşük olarak duruyor | `README.md` |

> **Senin cümlen:** "Yarışma projelerinin en kolay hatası sonucu
> gördükten sonra kuralı değiştirmek. Ben kuralları koşudan önce
> yazıp commit'ledim; tarihler depoda. Bir kuralım sonuç gelince
> **aleyhime çalıştı** ve onu da yazdım — değiştirmedim."

Bu son cümlenin karşılığı gerçek: ADR-0061 §5'in geri alma koşulu
fırladı (`47 → 50`) ve kural yeniden yazılmak yerine olduğu gibi
kaydedildi ([KAYIT-090](../defter/KAYIT-090_2026-10-28_havuzda-krater-yeniden-okundu-ve-geri-alma-kapisi.md) §4).

## 6. Jüri soruları — dürüst cevaplar

### Kolay olanlar

**S: Niçin SPH, niçin sonlu elemanlar değil?**
Çarpma sonrası malzeme parçalanıp dağılıyor; ızgara tabanlı yöntemde
ızgara kopuyor. SPH ızgarasızdır, büyük deformasyonu doğal taşır.
Astroid çarpma literatürünün ana aracı da budur.

**S: Kaç parçacık?**
Merdivenli çözünürlük kullandım; üretim havuzunda kaba merdiven,
eksende `h = 0,70` m. Tam sayı `docs/COZUNURLUK-STANDARDI.md`'de.

**S: Doğru çalıştığını nereden biliyorsun?**
→ §3.5. Cevabı bilinen `33` doğrulama problemi, hedefe geçmeden önce.

**S: Neden `96` nokta?**
Latin hiperküp tasarımı; GPU bütçesiyle (nokta başına `~5` GPU-saat)
sınırlı. `96` nokta, üç boyutlu uzayda vekil eğitmeye yetiyor ve
`θ`-gruplu çapraz doğrulamayla sınandı.

### Zor olanlar — **buraya hazırlıklı gel**

**S: Posterior yakınsamıyorsa bu sonucun değeri ne?**
> Değeri **yöntem**de ve **olumsuz sonuç**ta. Üç şey gösterdim:
> (1) `β`'dan kaç yön çözülebileceğini **ölçtüm** — bir;
> (2) çıkarım makinemin kalibre olduğunu SBC ile sınadım;
> (3) yakınsamanın niçin başarısız olduğunu sayısal olarak belirledim —
> çözünürlük iki katına çıkınca `Y₀` eşlemesi `×3,22` kayıyor, ve bu
> saçılma değil **yanlılık** (`7/7`, `p = 0,0156`).
> Bunu bilmek, yakınsadığını sanmaktan iyidir. Hangi çözünürlüğün
> gerektiğini de artık biliyorum: ölçtüm, `224` saat, sınır `48`.

**S: Bu kodu sen mi yazdın?**
→ [`YAPAY-ZEKA-BEYANI.md`](YAPAY-ZEKA-BEYANI.md) §6. Tek cümle:
*"Kodu büyük ölçüde bir dil modeline yazdırdım; kurguyu, kararları ve
neyin yayımlanacağını ben belirledim. Modelin yanıldığı yerleri de
depoya yazdım — üç tanesini şimdi anlatabilirim."*
Üç tanesi: krater operatörünün `47` yanlış sayısı (§3.6), çürütülen
doluluk hipotezi (aşağıda), `kos` hatasıyla geri çekilen dört bulgu.

**S: Modelin bir hatasını anlat.**
> Krater okunamayan `13` noktayı "SPH'in birim bölünmesi bozuluyor"
> diye açıklamayı denedik. Beş noktada öyle görünüyordu. `96` noktada
> saydık: bozulma **gerçek** (iç doluluk `0,110–5,115`, referans
> denetimi `1,230–1,232` ile çok sıkı) **ama başarısızlıkları
> açıklamıyor** — krateri *okunamayan* noktaların iç dolululuğu en
> sağlıklı olanlar, ayırt edicilik `AUC = 0,203` ile **ters** yönde. O
> açıklamaya dayanarak yazılmış kodu da ölçtük, fark üretmediğini
> gördük ve **commit'lemeden geri aldık**.

**S: `α_b` ve `f`'yi çözemediysen proje başarısız değil mi?**
> Hayır — çözülemeyeceğini **gösterdim**, bu bir sonuçtur. Tek skaler
> gözlemle üç parametre çözülmez; bunu Fisher bilgi matrisinin
> özdeğerleriyle sayısal olarak kanıtladım (`n_yön = 1`, eşik `36,0`).
> Projenin başındaki beklenti buydu ve riskler listesine
> (`DEVAM-BITIS3.md` §7.9) **önceden** yazılmıştı. Hera'nın ikinci bir
> ölçüm getirmesi tam bu yüzden değerli.

**S: Krater öngörün çok geniş (`−46` ile `+504` m³), bu bir öngörü mü?**
> Geniş olması **bilinçli** ve kaydın gövdesinde yazılı. İşlevi
> "Hera'nın krateri şu olacak" demek değil, **ne kadar bilmediğimi**
> Hera'dan önce kilitlemek. Üç şerhi de kaydın içinde: seçilim
> yanlılığı (kullanılan noktaların `Y₀` ortancası `1 918` Pa, dışlanan
> `10,58` Pa, posteriorun kipi `18,7` Pa — yani vekil iki dekad dışına
> ekstrapole ediyor), negatif hacim örneklerinin **kırpılmadığı**, ve
> bunun *geçici* krater olduğu. Ön kaydın dar çıkması başarı değil,
> **hata işareti** olurdu ve bunu da koşudan önce yazdım (EK-1 §3).

**S: `β = 3,61` değeri hedefin kütlesine bağlı, kütle ölçülmedi.**
> Doğru ve bu benim de bildiğim bir sınır. Bu yüzden kütle
> tutarlılığını ayrı bir kapı olarak koydum: sahnenin kütlesi gözlem
> kütlesinden (`4,3e9` kg) `%5`'ten fazla saparsa "model ve gözlem aynı
> şeyi ölçmüyor" diye durur (`dart_gozlemleri.py`, `kutle_tutarliligi`).
> `β`'nın kütle ölçeğiyle nasıl değiştiğini de ayrıca hesapladım.

**S: Olumsuz sonuçları niçin yayımladın?**
> Çünkü yayımlamazsam sonuçlarım sınanamaz. Açık kusur sayımı `87` ve
> depoda yazılı. Bir projenin güvenilirliği, neyi bilmediğini söyleme
> biçiminden anlaşılır.

**S: Mühürlemek tam olarak ne demek?**
> Öngörüyü hesaplayıp bir JSON dosyasına yazdım, dosyanın SHA-256
> özetini aldım, özetle birlikte commit'ledim. Hera verisi geldiğinde
> dosyayı değiştirirsem özet tutmaz ve bu görünür olur. Yani öngörüyü
> sonradan "düzeltme" olanağımı **kendim elimden aldım**. İlaç
> denemelerinde ön kayıt (preregistration) aynı amaçla yapılır.

**S: Bir şeyi yeniden yapsan neyi değiştirirdin?**
> Çözünürlük yakınsamasını **en başta** ölçerdim. Onu geç ölçtüm ve
> `S11`'in düşmesi projenin en pahalı dersi oldu. İkinci olarak krater
> operatörünü ilk günden iki bağımsız tanımla çapraz doğrulardım —
> `A86` kusuru bir yıl açık kaldı.

## 7. "Bilmiyorum" demenin doğru biçimi

| yanlış | doğru |
|---|---|
| sayı uydurmak | "O sayıyı ezberlemedim, `docs/sonuclar/README.md`'de yazılı, açayım mı?" |
| "herhalde şöyledir" | "Ölçmedim. Ölçmek için şu koşu gerekir: …" |
| soruyu geçiştirmek | "Bu projenin bilinen bir açığı, kusur kaydında `A__` numarasıyla duruyor." |
| savunmaya geçmek | "Haklısınız, bu bir sınır. Niçin orada bıraktığımı anlatayım." |

Bilmediğini söylemek bu projede **tutarlı** davranıştır: bütün belge
düzeni (olumsuz sonuçlar, açık kusurlar, çürütülen hipotez) aynı şeyi
yapıyor. Jüri tutarlılığı görür.

## 8. On dakikalık anlatım iskeleti

| süre | ne | dayanak |
|---|---|---|
| `0:00–1:30` | Problem + §1'in doksan saniyesi | — |
| `1:30–3:00` | Yöntem: simülasyon → vekil → posterior (bir şema) | `docs/sekil/` |
| `3:00–4:30` | Çözücünün doğrulanması (Sod/Sedov/plaka) | §3.5 |
| `4:30–6:00` | **Ana bulgu:** `n_yön = 1`, `Y₀` öğreniliyor, `%34` bağdaşır | §4 |
| `6:00–7:30` | **Dürüst sınır:** `×3,22` çözünürlük yanlılığı | §2 |
| `7:30–9:00` | Mühürlü Hera ön kayıtları — yanlışlanabilirlik | §3.7 |
| `9:00–10:00` | Krater hikâyesi (araç hatası → çapraz doğrulama) | §3.6 |

Son sözü **mühür** ya da **krater hikâyesi** üzerine bırak; ikisi de
"bu öğrenci dürüst çalışıyor" izlenimi verir.

## 9. Hazırlık kontrol listesi

- [ ] §1 doksan saniye, kâğıda bakmadan
- [ ] §4'ün on sayısı
- [ ] **§4.1'in cümlesi** — ve `f` ucunun niçin zayıf olduğu
- [ ] §3.6 krater hikâyesi, kendi cümlelerinle
- [ ] §6'nın üç zor sorusu (yakınsama, "kodu sen mi yazdın", geniş öngörü)
- [ ] Modelin bir hatasını **anlatabilmek** (§6)
- [ ] Deponun gezinmesi: `README.md` → `docs/sonuclar/README.md` → `docs/onkayit/`
- [ ] [`YAPAY-ZEKA-BEYANI.md`](YAPAY-ZEKA-BEYANI.md) okunmuş ve kabul edilmiş
- [ ] 2204-A son tarihi: **4 Ocak 2027** · rapor `docs/rapor2204/rapor.pdf` (20 sayfa, sınır 20)

---

> **Eksik kalan yarışma işleri** (`DEVAM-BITIS3.md` §6.8): poster,
> özet, İSEF/TÜBİTAK kural ve tarih kontrolü. Bu belge "savunma notu"
> ve "yapay zekâ kullanım beyanı" maddelerini kapatır.
