# KAYIT-075 — Havuzu kilitleyen **beş karar verildi** (2026-10-05)

**Kapsam:** A2, C1, A105, A109 ve posterior tarifi · **0 GPU-saat** ·
**Durum:** beşi de **KABUL EDİLDİ**, koda ve kilitli protokole geçti ·
**Kim karar verdi:** kullanıcı kararı Claude'a **devretti**
(*"kararları sen ver ve düzgün ver"*, 2026-10-05) · **Sonuç:**
[PROTOKOL-HAVUZ](../truba/PROTOKOL-HAVUZ-URETIM.md) yazıldı

---

## 0. Niçin bu kayıt var

Beş karar `~70` gündür açıktı ve üretim havuzunu (`~480 GPU-saat`)
kilitliyordu. Kullanıcı karar vermeyi istemediğini söyleyip yetkiyi
devretti. **Kararlar burada, gerekçeleriyle ve geri alma koşullarıyla.**

Bir ADR'nin "KABUL EDİLDİ" olması, onu **ben** kabul ettiğim için
tartışmaya kapalı değil demektir: her kararın altında onu **düşürecek
ölçüm** yazılı. Bu kaydın işi, ileride "neden böyle seçildi" diye
sorulduğunda cevabın **sonuçtan önce** yazılmış olduğunu göstermek.

## 1. A2 — `Y₀` önseli → **`[1e0 , 1e5] Pa`** (ADR-0053)

**Karar:** üretim uzayı `DART_UZAYI_S4` olur; `Y₀` alt sınırı `1e3 → 1e0 Pa`,
üst sınırı `1e7 → 1e5 Pa`. Eski `DART_UZAYI_S3` **silinmez**.

**Üç bağımsız gerekçe:**

| gerekçe | sayı |
|---|---|
| ölçülen `β(Y₀)` gözlemi buraya koyuyor | `644 Pa` (eski alt kenar `1e3`) |
| literatürün Dimorphos matris kohezyonu (L1/L2) | **`0 – 500 Pa`** — eski önselin **tamamen altında** |
| modelin **doğrulandığı** aralık | `1 – 50 Pa` (W2/UA/UY/UG/DY2/DK/DM/DT) |
| sekiz `β` adayının hepsi (C1'den bağımsız) | `21 – 4951 Pa`, en yakın kenara `1,31` dekad |

**Ve en önemlisi: bu karar önceden kaydedilmişti.** PROTOKOL-U §4
(2026-09-14, koşulardan önce) `U1`/`U2` için şu satırı taşıyor:
*"`Y₀` önseli (`≥ 1e3 Pa`) gerçek Dimorphos'u dışarıda bırakıyor →
**ADR: önsel alt sınırı `1 Pa`'ya**"*. DY2 aynı `θ` ile (`Y₀ = 10 Pa`)
gözleme ulaştı, yani satırın **koşulu sağlandı**. Reçeteyi uyguluyorum.

**Uygulama DO'ya bağlı** (ADR-0053 §4.4, PROTOKOL-HAVUZ §3.1): şu an
koşan DO, `644 Pa`'yı **interpolasyonla** sınıyor. DO `ONSEL GOZLEMI
ICERIYOR` derse **eski önsel korunur**. Bu kararsızlık değil **ön kayıt**:
kuralı koşudan önce yazdım ve sonucuna göre değiştirmeyeceğim.

**Bu kararı düşürecek şey:** DO'nun `ONSEL GOZLEMI ICERIYOR` yargısı.

## 2. C1 — gözlenen `β` → **`3,5418 (+0,188 / −0,247)`** (ADR-0054)

**Karar:** hedef `β` sabit bir sayı değil, **sahnenin kütlesinin
fonksiyonu**: `uretim_hedef_beta(M_sahne)` =
`cheng_beta(hedef_kutlesi = M_sahne)`. Üretim sahnesi (`4,2980e9 kg`) için
`β = 3,5418`.

**Gerekçe:**

1. **Eski hedef tutarsızdı.** PROTOKOL-U §1'in `3,12 ± 0,34`'ü **eski küre
   sahnesinin** kütlesinden (`4,16e9`) türemişti. `β = Δv·M/p` olduğundan
   gözlenen `β` kütleyle doğru orantılı; üretim sahnesi `4,298e9` ve aynı
   yoldan `3,2210` çıkıyor. A108'in kendi kuralını gözlem tarafında
   çiğniyorduk.
2. **Yayınlanan sayı kullanılır.** Cheng ve diğ. 2023 (*Nature* 616, 457;
   arXiv:2303.03464): `β = 3,61 (+0,19 / −0,25)`, `ρ_ref = 2400 kg/m³`.
   Bizim dairesel iki cisim yaklaşımımız tam yörünge çözümünü yenemez;
   kendi basitleştirmemizi "gözlem" diye sunmak savunulamaz.
3. **Sınavı ZORLAŞTIRIYOR.** Gözlem sd'si `0,34 → 0,188`'e **daralıyor**.
   Yani bu değişiklik modelin işini kolaylaştırmak için seçilmiş olamaz.
   Buna rağmen `I` `1,54 → 0,63`.

**Eski değer silinmez:** `3,12` ile hesaplanmış bütün yargılar (W, W2, U/V,
DY, DY2, DK, DM, DT) **olduğu gibi** kalır. Yeni hedef **bundan sonraki**
protokollerde geçerli.

**Güzel bir yan okuma:** DY2'nin `β = 3,748`'i Cheng bağıntısında
`ρ = 2512 kg/m³`'e karşılık geliyor — yayınlanan makul aralığın
(`1500 – 3300`) içinde, eşit yoğunluk varsayımının yalnız `%4,7` üstünde.
Yani "modelimiz gözlemi `%20` aşıyor" demek yerine **"Dimorphos'un yığın
yoğunluğu `2512` ise modelimiz gözlemi tam veriyor"** demek daha doğru.

**Bu kararı düşürecek şey:** L16 (Nakano 2024) yeniden şekillenme
düzeltmesinin **tam metinle** teyidi. O düzeltme `β`'yı `3,02`'ye indirir
ve tabloyu değiştirir. `period_interface` onu şu an *"arama özeti, tam
metin teyidi bekliyor"* diye işaretliyor ve **teyit edilmemiş bir
düzeltmeyi sonucu kurtardığı için almak** tam olarak yapmamamız gereken
şey olurdu.

## 3. A105 — matris çekme dayanımı **KAPALI** (ADR-0056)

**Karar:** üretim `--matris-cekme-yok` ile koşar. Ölçülen `−%23` etki
**bütçeye eklenmez**; her raporda duran bir **koşullu duyarlılık** cümlesi
olarak yazılır (`dy_dart_raporu.KOSULLU_CEKME`).

**Gerekçe:**

1. **Fizik:** moloz yığını matrisi makroskopik ölçekte çekmeye dayanmaz.
   L1/L2 matrise çekme dayanımı **vermiyor**; **bloklara** veriyor
   (`~10 MPa`) ve bizim modelimizde bloklar ayrı malzeme olarak zaten var.
   Mohr-Coulomb uç kesmesinin izin verdiği `T_m = Y₀/μ_f ≈ 1,7 Y₀` kadar
   çekme, gevşek regolit için dayanağı olmayan bir ek dayanımdır.
2. **Zincir:** doğrulanmış bütün koşular (W2, UA, UY, UG, DY2, DK, DM, DT)
   bu ayarla koşuldu. Seçimi değiştirmek `~40 GPU-saat`'lik kıyas
   zincirini geçersiz kılar.
3. **`0,23`'ü bütçeye koymamanın sebebi:** bu bir **reddedilen model**,
   belirsizlik değil. Eklenirse payda `0,447 → 0,580` ve `I` `0,63 → 0,36`
   olur — yani **kendi sınavımızı kolaylaştırırdık**. Kendi sınavını
   kolaylaştıran bir "dürüstlük" dürüstlük değildir (ADR-0051 §2b'nin
   `AŞIRI TEMKİNLİ` tanısı tam bunun için var).

**Bu kararı düşürecek şey:** hiçbir ölçüm — çünkü karar fizik gerekçesine
dayanıyor, sonuca değil. DC koşusu **bedeli** ölçüyor (PROTOKOL-DY §8) ve
protokolün kendisi *"DC'de `β` daha iyi tuttu, çekmeyi açalım"* demenin
yasak olduğunu **koşudan önce** yazıyor.

## 4. A109 — bloklar **`r ∈ [14 , 56] m`, `q = 3`** (ADR-0057)

**Karar:** üretim blok topluluğu **sayı olarak** kilitli
(`rubble_generator.URETIM_BLOK`); varsayılan türetme
(`r_min = 2·spacing`, `r_max = 8·spacing`) **kullanılmaz**.

**İki ayrı gerekçe:**

1. **Çözülmüş bloklar, çözülmemişten iyidir.** U/V'nin modelinde
   (`1,7 – 6,5 m`) blokların kütlece **`%99,3`'ü tek parçacık** (A89).
   Orada `α_b` (blok gözenekliliği) hiçbir şey ifade etmiyor — tek
   parçacığın gözenekliliği yalnız bir yoğunluk çarpanı — ve `f` blok
   kesri değil yoğunluk düzensizliği. Yani `θ`'nın **iki ekseni tanımsız**
   olurdu. `1,7 m`'yi çözmek `~2700` kat parçacık ister; bütçe yok.
2. **Latent tuzak kapatıldı.** Varsayılan türetme `θ`'nın **fiziksel
   anlamını sayısal aralığa** bağlıyordu. Şu an hata üretmiyor (bütün
   kollar `--spacing 7.0` kullanıyor ve merdiven yalnız kabukları
   inceltiyor → aynı cisim, karşılaştırmalar geçerli), ama `spacing` bir
   gün değişse `f` ve `α_b` **sessizce** başka bir şeyi ifade ederdi.

**Bedeli — ve açıkça yazıyorum:** `14 m`'lik iç bloklar hiçbir yüzey
gözleminde görülmedi; görülemezdi de, gömülüler. Varsayım şu: moloz
yığınının boyut dağılımı yüzeyde gördüğümüzden büyük ölçeklere uzanıyor.
Bu bir **varsayım**, sonuç değil. Bu yüzden her raporda **kapsam sınırı**
durur:

> Çıkarılan `(α_b, f)`, Dimorphos'un **`≳ 14 m`** ölçeğindeki **iç** blok
> topluluğunu tanımlar. Daly ve diğ. 2023'ün ölçtüğü **yüzey** blokları
> (`0,16 – 6,5 m`) bu çözünürlüğün **altındadır** ve çıkarımın erişiminde
> **değildir**.

Bu, iddiayı **küçültüyor** ama savunulabilir yapıyor. ISEF'te
"yüzeyde 6,5 m blok var, siz 14 m mi kullandınız?" sorusu gelecek ve
cevabı **önceden** yazılmış olacak.

**Bu kararı düşürecek şey:** havuzun ejekta ayrışması (KAYIT-073) `α_b`
ve `f` eksenlerinde de **götürme** gösterirse — o zaman blok ölçeği
seçimi posterioru değil **kapsamı** belirler ve A109 yeniden açılır.

## 5. Posterior tarifi (ADR-0058)

**Karar:** GP (`gp_uydur`) + **Bachoc** varyans kalibrasyonu +
`grid_posterior_hetero` + **ölçülmüş `R`** + **SBC kapısı**.

**Gerekçeler ölçülmüş:**

1. İkinci derece vekil `Y₀`'yu `AŞIRI TEMKİNLİ` yapıyor, GP yapmıyor
   (`n_sbc = 200`).
2. **Posterior makinesi doğru**: tam modelle (vekil yok) SBC her iki
   senaryoda **kusursuz kalibre** (KS `p` `0,29 – 0,95`). Hattın en pahalı
   parçası sınandı.
3. **`R = I` almak pahalı** ve beklediğimin tersi yönde: `ρ` `0 → 0,8`
   `α_b`'nin daralmasını `0,372 → 0,708` yapıyor (`Y₀` etkilenmiyor).
   Korelasyon arttıkça iki gözemlinin **farkı** keskinleşiyor ve `α_b` o
   yöne biniyor. Yani `R = I` bilgiyi şişirmiyor, **yanlış yere
   dağıtıyor** — `α_b` hakkındaki sonuç `R`'ye bağlı. `R` **ölçülecek**.
4. **SBC bir KAPI, denetim değil.** `YANLI` çıkarsa posterior
   **yayımlanmaz**; çare tasarımı sıkılaştırmak (`+24` nokta) ya da tarih
   eşlemeyle (Vernon) eleme. **Paydayı büyütüp geçmek yasak.**

**Bu kararı düşürecek şey:** havuzun gerçek vekiliyle SBC'nin `YANLI`
vermesi — ki o zaten kapının kendisi, yani karar kendi düşme koşulunu
içeriyor.

## 6. Dürüst değerlendirme

- **İyi:** beş karar da **ölçüme** dayanıyor, üçü (`A2`, `C1`, `A109`)
  önceki bir ön kaydın ya da birincil kaynağın uygulanması. Hiçbiri
  "sonuca bakıp seçtim" değil — DO/DC/DN **koşarken** verildi ve
  sonuçlarını görmedim.
- **Riskli:** `A109`'un `14 m` varsayımı en zayıf halka. Gözlemle
  desteklenmiyor, yalnız çözünürlükle gerekçeleniyor. Kapsam sınırı bunu
  örtmüyor, **açıkça söylüyor** — ama jüri buraya basacak.
- **Kabul edilen bedel:** `f_boulder`'ın çıkmayacağını **şimdiden**
  biliyoruz (prova: önsel-baskın). İddia "üç parametreyi çözdük" değil,
  **"`Y₀`'yu çözdük, `α_b`'yi kısmen, `f`'yi çözemedik ve niçin
  çözemediğimizi ölçtük"** olacak. Bu, zayıf bir sonuç değil **dürüst**
  bir sonuç — ve ölçülmüş bir negatif sonuç, uydurulmuş bir pozitiften
  iyidir.
- **Sırada:** DO/DC/DN bitince (bu akşam) PROTOKOL-HAVUZ §3.1'in kapısı
  okunur ve havuz gönderilir.
