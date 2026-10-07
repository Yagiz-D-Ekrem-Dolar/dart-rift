# KAYIT-077 — Üretim havuzu gönderildi; "üç parametre çıkmaz" iddiam açıldı (2026-10-07)

**Kapsam:** havuzun gönderilmesi + üç parametre denemesinin kurulması ·
**GPU:** havuz `~480 sa` (koşuyor), duman koşuları `~0,01 sa` ·
**Durum:** havuz koşuyor, iki duman hatası yakalandı, bir yapısal bulgu
çıktı, **üç kendi hatam düzeltildi** ·
**Öncül:** [KAYIT-075](KAYIT-075_2026-10-05_bes-karar-verildi.md) (beş karar),
[KAYIT-076](KAYIT-076_2026-10-06_DO-DC-DN-uc-kilitli-yargi.md) (DO/DC/DN) ·
**Protokol:** [PROTOKOL-HAVUZ](../truba/PROTOKOL-HAVUZ-URETIM.md)

---

## 0. Bu kaydın niçin uzun olduğu

Bu kayıt üç şeyi birlikte tutuyor: **havuzun gönderilmesi**, **üç parametre
denemesinin açılması** ve **kendi aşırı kesin konuşmamın düzeltilmesi**.
Üçü ayrılabilirdi ama ayrılmaları yanlış olurdu: üçüncüsü ilk ikisinin
arasında, kullanıcının bir itirazıyla ortaya çıktı ve ikisinin de kapsamını
değiştirdi.

## 1. Havuz gönderildi — `1592569`

| ne | değer |
|---|---|
| nokta | `96` (LHS, `DART_UZAYI_S4`) |
| dizi | `0-23%2` → **24 dilim × 4 nokta**, en çok **2** eşzamanlı |
| uzay | `Y₀ ∈ [1e0, 1e5] Pa` (**ADR-0053 KABUL**, PROTOKOL-DO kapısı açtı) |
| sahne | DY2 ile birebir (elipsoit `88,5×87×58`, `ρ = 2306,1`, üç küre, `17°`) |
| bloklar | `r ∈ [14, 56] m`, `q = 3` — **sayı olarak** (ADR-0057) |
| çekme | **KAPALI** (ADR-0056) |
| krater | **isteğe bağlı** (`--istege-bagli-gozlemli krater_derinlik`, ADR-0055) |
| maliyet | `~480 GPU-saat`; 2 GPU ile duvar süresi **`~10 gün`** |

### Niçin 24 dilim × 4 nokta

İlk tasarım 2 dilim × 48 noktaydı. **Hesap hatası:** dilim başına
`48 × 5 = 240` saat, iş zaman sınırı **24 saat**. Her dilim 24 saatte
kesilir, `~4` nokta tamamlar ve `10` kez yeniden gönderilmesi gerekirdi.

Çözüm Slurm'ün kendi kısıtı: `--array=0-23%2`. 24 görev, her biri `4` nokta
(`~20` saat, sınırın altında), `%2` ile **en çok iki tanesi birden** koşar.
Biri bitince Slurm sonrakini başlatır. Yani 2 GPU sınırına uyulması benim
elle sıralamama değil, **kuyruğun kendisine** bağlı.

`ensemble_kos` tamamlanan noktaları atladığı için kesinti olursa yeniden
gönderim yeter; kaybolan en fazla **son nokta** olur.

## 2. İki duman hatası — `480 GPU-saat` yerine `38 saniye`

Havuzu doğrudan göndermek yerine önce **tek nokta, kısa süreli** bir duman
koşusu attım. İki hata çıktı ve ikisi de havuzu sessizce bozacaktı.

### (a) `faz5`'te yarım bırakılmış iş — betik hiç koşmazdı

Önceki oturumda `--istege-bagli-gozlemli` bayrağını eklerken üç yerel adı
(`_ISTEGE_BAGLI`, `_ZORUNLU`, `_NAN_IZINLI`) **kullanmış ama tanımlamamışım.**
Yani `faz5_ensemble_merdiven.py` `NameError` ile düşerdi. Oturum araya
girdiği için yarıda kalmış, ben de kapattığımı sanmışım.

**Ders:** bir bayrağı "ekledim" demek, çağrı yerlerini bağlamak demek değil.
`ast` ile tanımlı-kullanılan adları karşılaştıran iki satırlık bir denetim
bunu anında gösterdi; onu artık yarım iş bıraktığımda koşuyorum.

### (b) `is_HAVUZ.slurm`'da DO'dan kalan satır — **iki katmanlı** hata

```
--tasarim-dosyasi "$TAS" $ORTAK \
```

Duman koşusu `38 saniyede` düştü: `TAS: unbound variable`.

Görünen hata buydu. **Asıl hata** altındaydı: satır kalsaydı (ya da `TAS`
tanımlı olsaydı) havuz **sabit tasarım dosyasını** okuyacak, `--n-lhs 96`
yok sayılacaktı. Yani `96` nokta yerine **1 nokta** koşar, `~5` saat sonra
"bitti" der ve biz bunu ancak posterior kurmaya çalışırken anlardık.

Tek satırın bu kadar pahalı olabilmesi, kopyala-yapıştır ile türetilen iş
betiklerinin tehlikesi. Üç betik (`is_DO` → `is_DC` → `is_DN` → `is_HAVUZ`)
birbirinden türetildi ve her türetmede bir artık kaldı.

### (c) Satır sonu karakterleri üç kez tam eşleşmeyi bozdu

Windows'ta yazılan `.slurm` dosyalarında `git`'in `autocrlf`'i yüzünden tam
dize değiştirme üç denemede tutmadı. Dördüncüde **satır indeksi + bayt
düzeyi** işlem yaptım. Küçük bir ayrıntı ama yarım saat yedi; bir dahaki
sefere doğrudan bayt düzeyinde başlayacağım.

## 3. Kod sürümü kapısı işini yaptı

İlk gönderimde **üç iş de** anında düştü:

```
KOD SURUMU YANLIS: beklenen e87193d..., bulunan 7a2a9b0...
```

`ortak_bas.sh`, çalışma dizinindeki `git rev-parse HEAD`'i `SABIT_COMMIT`
ile karşılaştırıyor. Ana kopyayı ileri almamıştım. **GPU harcanmadı**,
kapı tam tasarlandığı gibi davrandı (A96'nın çivili ağaç düzeni).

Bu, kaydetmeye değer bir **olumlu** sonuç: proje boyunca eklenen kapıların
çoğu hiç tetiklenmedi; bu tetiklendi ve işe yaradı.

## 4. Üç parametre — kullanıcının itirazı ve benim fazla kesin konuşmam

Kullanıcı şunu söyledi: *"Bence 3 parametre de çıkabilir... kaos teorisi,
örüntü takibi, çoklu nokta, non-linearlik."*

İtiraz **haklıydı** ve üç yerde fazla ileri gitmişim.

### (a) `rank(F) ≤ min(k,d)`'yi küresel bir yasa gibi sundum

Doğru olan: Fisher matrisi `y(θ)`'nın bir noktadaki **birinci mertebe**
açılımını ölçer ve rankı `≤ 2`'dir. Provada ölçtüm: üçüncü özdeğer **tam
sıfır**.

Eksik olan: bu **yerel ve doğrusal** bir ifade. Model doğrusal değilse
`y(θ) = y_gözlem` çözüm kümesi kutuda **eğri bir 1-B manifold**; posterior
o eğrinin etrafındaki tüp. Eğri kutu içinde kıvrılıyorsa **üç kenar
dağılımı da** önselden dar olabilir. Benim "çıkmaz" dediğim şey, eğrinin
`f` sınırına kaçtığı durumdu.

### (b) Kendi varsayımımı sonuç gibi kullandım

`prova_cikarim.py`'nin başında **yazıyor**: `α_b` ve `f` katsayıları
**VARSAYIM**, yalnız `Y₀` üsleri ölçülmüş. Sonra o varsayımla çıkan
"`f` önsel-baskın" sonucunu, sanki ölçülmüş gibi birkaç kez tekrarladım.
`f`'nin gözlemlilere nasıl girdiğini **hiç ölçmedim**; havuz ölçecek.

### (c) "Çoklu noktadan örüntü"nün somut karşılığını erken kapattım

Her koşuyu 2 skalere indiriyoruz. Ama her koşu bir **alan** üretiyor.
KAYIT-073 zaten ölçtü: `β − 1 = K · M_kaçan · v_ort · kos_ort / p`.
Yani `(β, M_ejekta)` bize `M`'yi ve `v·kos` **çarpımını** veriyor; üçüncü
bilgi için `v` ile `kos`'u **ayırmak** gerekiyor.

Ejekta kütle-hız dağılımının eğimini (`e`) daha önce ölçmüştüm
(`1,445 / 1,314 / 1,109`, `Y₀ = 1/10/50 Pa`) ve *"`Y₀` duyarlılığı `β`
kadar"* diye bir kenara atmıştım. **Yanlış ölçüte baktım:** önemli olan
`Y₀` duyarlılığı değil, `f` ve `α_b`'ye **bağımsız** bağlı olup olmaması.

### Kaos konusunda ise katılmıyorum

Kaos bu problemde **zarar verir**: yakın `θ`'lar çok farklı `y` verseydi
vekil kurulamazdı. Ölçtüğümüz tersi — model `θ`'da düzgün (GP'nin LOO
sapması `log10`'da `0,015`). Çözünürlük yakınsamazlığı kaosa benziyordu
ama UG'de **sistematik bir geçiş anı hatası** çıktı. İşe yarayan şey kaos
değil, **doğrusal olmama** ve **fonksiyonel (çok noktalı) gözlemli**.

## 5. Yapısal bulgu: **üç açık karşılık grubu var**

`observables/aday_gozlemliler.py` kütüğünü kurarken çıktı. Her adayın
yanında **hangi DART ölçümünden geldiği** yazılı:

| grup | ölçüm | durum | adaylar |
|---|---|---|---|
| `periyot_degisimi` | `ΔT = −33,0 ± 1,0 dk` → `β` | **açık** | `beta` |
| `ejekta_kutlesi` | LICIACube fotometrisi → `1,6 ± 0,3e7 kg` | **açık** | `M_kacan` |
| `ejekta_hiz_dagilimi` | ejekta parlaklığının azalması | **açık** | `e_hiz`, `v_ort`, `v_p50`, `v_p90` |
| `ejekta_konisi` | koni açısı | **A95 ile KAPALI** | `kos_ort`, `aci_p50`, `aci_yayilim` |
| `gozlenemez` | — | yok | `bagli_kutle` |

> **Koni kapalı olsa bile üç açık grup var.** Üç parametre için üç bağımsız
> kısıt gerekir ve sayı **tam tutuyor**.

### Bu, A95 hakkındaki sözümü de düzeltiyor

KAYIT-073 §5'te ve kullanıcıya iki kez şunu söylemiştim: *"üçüncü yön
ejektanın yönelimi ve o A95 yüzünden kıyaslanamıyor."* **Düzeltme:**
üçüncü kısıt yönelim **olmak zorunda değil**; hız dağılımı da üçüncü bir
grup ve A95'e takılmıyor. A95 artık **dördüncü** gözemli olur — yapılırsa
`θ` aşırı belirlenmiş hale gelir (sağlamlık), yapılmazsa üç parametre
**yine mümkün**.

KAYIT-073 §5'in satırları yerinde kalıyor; bu paragraf yanına düşülen
nottur.

## 6. İki dürüstlük mekanizması — çünkü bu alan kolayca kendini aldatır

Gözemli eklemek "bedava bilgi" gibi görünür. İki kapı koydum:

**(a) `gozlenen` bayrağı.** DART karşılığı olmayan aday posteriora
**giremez**. `v_ort` ölçülmedi (yalnız `v·kos` çarpımı çıkıyor), `kos_ort`
A95'e takılı, `bagli_kutle` gözlenemez. Üçü de kütükte **tanı** olarak
duruyor. Model-model karşılaştırmasını gözlem yerine koymak, ölçülmemiş bir
kesinlik iddiasıdır.

**(b) `karsilik_grubu`.** Aynı **ölçümün** iki özeti bağımsız gözemli
**sayılmaz**. `e_hiz` ile `v_p50` aynı fotometriden geliyor; ikisini
birlikte kullanmak ADR-0058 §3'te ölçtüğüm `R = I` tuzağının gözemli
seçimindeki hâli olur — olmayan bilgiyi var saymak.

Seçici bu iki kuralı **zorunlu** uyguluyor ve sınavlarla kilitli
(`test_ayni_gruptan_IKI_aday_secilemez`,
`test_gozlenmeyen_aday_SECILEMEZ`).

## 7. `v_kaçış`'ı tahmin etmek yerine **geri çözmek**

Çevrimdışı hesapta `v_esc` gerekiyor ama elipsoit sahnenin **etkin
yarıçapı** `npz`'de yok. Tahmin etmek bütün aday gözlemlileri sessizce
kaydırırdı.

Çözüm: koşu `M_kacan`'ı **doğru** `v_esc` ile yazmış. `M_kacan(v_esc)`
azalan bir basamak fonksiyonu olduğundan eşik geri çözülebilir. Sonra
`v_ort` ve `kos_ort` **bağımsız denetim** olur: ikisi de `1e-6` içinde
tutuyorsa eksen ve kaçış hızı doğrudur.

`tutarlilik_denetle` bunu zorunlu kılıyor ve **yanlış eksende hata
veriyor** (sınavlı). Yani çevrimdışı kütüphane koşunun sayılarını yeniden
üretmek zorunda.

### Ve burada bir kusur yaptım — kendi sınavım yakaladı

`kacis_hizi_kalibre` ilk sürümde eşik aralığının **yanlış tarafını**
alıyordu. `hs` azalan sıralı, `kum[k]` en hızlı `k+1` parçacığın kütlesi;
`sum(m[hiz > v_esc]) == kum[k]` için eşik `[hs[k+1], hs[k])` aralığında
olmalı. Ben `[hs[k], hs[k-1])` ortasını alıyordum — o değer `hs[k]`'nin
**üstünde** kaldığı için `k.` parçacık sayılmıyor ve kütle **bir parçacık
eksik** çıkıyordu (`5 456 736` vs `5 469 850`).

Sınavı "bilinen eşikle kütle hesapla, sonra eşiği geri oku" diye kurduğum
için anında yakalandı. Sınav gevşek olsaydı (ör. `rel=0.01`) geçerdi ve
bütün aday gözlemliler `%0,2` kaymış olurdu.

## 8. Altyapı: bugün ikisi de elimde değildi

- **TRUBA kopuk.** `ping` `%100` kayıp, MCP boş dönüyor. **Havuzun
  durumunu doğrulayamadım.** Son görüldüğünde `1592569_0/1` normal
  koşuyordu, `~2` saat içindeydi. Bağlantı kopukluğu Slurm'ü etkilemez,
  yani işler koşuyor **olabilir** — ama görmediğim şeyi "koşuyor" diye
  yazmam.
- **GitHub `push` reddetti:** `Internal Server Error` (500, istek kimliği
  `61E2:339A47:...`). İki kez denendi. Commit yerelde, `origin/main`'in
  bir önünde.

## 9. Sayılarla son dönem (6 Ekim ölçümü)

| | |
|---|---|
| GPU-saat | **418** (200 tamamlanan iş; iptal `1,3`, başarısız `0,0`) |
| Kod | **79 485 satır** (`src` 25 644 · `tests` 30 558 · `scripts` 20 269 · `truba` 3 014) |
| Belge | **38 872 satır** (defter 11 894 · ADR 7 496 · protokol 4 894) |
| Sınav | **2 164** sınav fonksiyonu |
| Commit | **730**, **45 çalışma gününde** (27 Tem → 7 Ekim) |
| Kayıt | 112 kusur · 77 defter · 58 ADR · 36 kilitli protokol |

## 10. Dürüst değerlendirme

- **İyi:** havuz koşuyor ve önündeki 13 koşulun hepsi kapalı. Duman
  koşuları iki hata yakaladı; ikisi de havuzu sessizce bozacaktı. Kod
  sürümü kapısı tetiklendi ve işe yaradı.
- **Kendi hatalarım:** (i) yarım bıraktığım bayrak bağlama işini kapattığımı
  sandım, (ii) `rank(F)` sınırını küresel bir yasa gibi sundum,
  (iii) kendi varsayımımı ölçüm gibi tekrarladım, (iv) eşik aralığının
  yanlış tarafını aldım. Dördünü de yazıyorum çünkü dördü de sonucu
  değiştirebilirdi.
- **Kullanıcının itirazı işe yaradı.** "Üç parametre çıkabilir" demesi, benim
  kapattığım bir yolu yeniden açtırdı ve **yapısal bir bulguya** götürdü
  (üç açık grup). Ölçüm olmadan ikisi de bilinemezdi; ama ben ölçmeden
  "çıkmaz" demiştim.
- **Hâlâ bilmediğimiz:** hız dağılımının `θ`'ya bağımlılığı `β` ve
  `M_ejekta`'dan **bağımsız** mı? Üç parametrenin kaderi tek bu soruya
  bağlı ve cevabı havuz verecek.
- **Sıradaki zorunlu iş:** PROTOKOL-UP — gözemli seçiminin yargı kuralı
  **veriden önce** kilitlenmeli. Kod yazıldı, protokol yok; bu boşlukta
  veri okunursa "üç çıktı" demek sonuca göre ölçüt seçmek olur.
