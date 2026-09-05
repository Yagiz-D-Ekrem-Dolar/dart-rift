# DART-RIFT — uzman görüşü için brifing

**Tarih:** 2026-09-05 · **Depo:** `main`, commit `c94d74e`

**Amaç:** İleri model **krater açıyor ama ejekta üretmiyor.** Sebebini
bulmak.

---

## 0. Otuz saniyede

GPU SPH (warp-lang, fp64, deterministik) · Tillotson EOS · P-α
gözeneklilik · Lundborg mukavemet · Grady-Kipp hasar · Barnes-Hut
yerçekimi. Hedef: DART–Dimorphos çarpmasından iç yapıyı Bayes
çıkarımıyla sınırlamak.

**Doğrulanmış:** Sod (kesin Riemann çözümüne karşı), Sedov, Tillotson
Hugoniot'u, korunum, CPU↔GPU bit-eşitliği.

**Tıkanan yer:**

| ölçülen | değer |
|---|---|
| şok sıkışması | `%45,3` — Rankine-Hugoniot bandı `%45,6 – 74,3` **içinde** |
| momentum defteri artığı | `1,2e-14` (makine hassasiyeti) |
| krater derinliği | `1,03 m` |
| **kaçan hedef maddesi** | **`93,2 kg` — `16` parçacık** |
| `β_hedef` | `1,033` (gözlem `3,22`) |

Şok doğru, defter kapalı, krater var — **ama madde uçmuyor.**

---

## 1. EN ÖNEMLİ SORU: kazı akışı neden gelişmiyor

### Ölçülen zaman serisi

| `t` | sıkışma | krater | kaçan parçacık |
|---|---|---|---|
| `8,0e-3 s` | `%44,69` | `0,259 m` | `110` |
| `2,4e-2 s` | `%45,13` | `0,793 m` | `45` |
| `5,6e-2 s` | `%45,33` | `1,017 m` | `39` |
| `1,0e-1 s` | `%45,33` | `1,043 m` | `16` |
| `2,0e-1 s` | `%45,34` | `1,029 m` | `16` |

**Sıkışma `0,2 s` boyunca `%45`'te donuyor.** Şoklanan madde
gevşemiyor, genleşmiyor, akmıyor. Krater `~56 ms`'te doyuyor ve sonra
hafifçe **geri kapanıyor**.

### Sorular

1. **Bu davranış size ne söylüyor?** Şoklanan maddenin hiç gevşememesi
   hangi kusurun bilinen imzasıdır?

2. **P-α'nın geri dönüşsüzlüğü** kazıyı bu kadar baskılayabilir mi?
   `α₀ = 1,7564` (`%43` gözeneklilik) ile enerjinin ne kadarı kalıcı
   sıkışmaya gider? Sizin kodunuzda benzer gözeneklilikte kazı
   gelişiyor mu?

3. Bizim P-α parametrelerimiz: `Pe = 1e6 Pa`, `Ps = 1e8 Pa`,
   `α₀ = 1,7564`. **Dimorphos benzeri bir hedef için makul mü?**
   `Pe`'nin düşüklüğü sıkışmayı çok erken mi başlatıyor?

---

## 2. ZAMAN ÖLÇEĞİ — belki de en basit açıklama

Koşuyu `t_end = 0,2 s`'de bitiriyoruz. Ama krater oluşma süreleri:

| rejim | `a = 5 m` için süre |
|---|---|
| yerçekimi, `T ~ √(a/g)` | **`~347 s`** |
| mukavemet, `T ~ a/u` (`u = 1 m/s`) | **`~5 s`** |
| **bizim koşu** | **`0,2 s`** |

Dimorphos: `g = 4,15e-5 m/s²`, `v_esc = 0,082 m/s`.

Rejim geçişi (`ρ g a ~ Y₀`):

| `Y₀` | geçiş krateri |
|---|---|
| **`1e4 Pa` — bizim üretim matrisi** | `1,6e5 m` → **tamamen mukavemet rejimi** |
| `1e7 Pa` — bizim bloklarımız | `1,6e8 m` → mukavemet |
| `1 – 100 Pa` (moloz yığını kohezyonu) | `16 – 1 600 m` → **yerçekimi rejimi devreye girer** |

### Sorular

4. **`0,2 s` çok mu erken?** Kraterimiz `56 ms`'te doyuyor — bu gerçek
   doyum mu, yoksa akışın **erken ölmesi** mi? Bu ölçekte hangi
   `t_end` anlamlıdır?

5. Üretim değerlerimiz: **matris `Y₀ = 1e4 Pa` (`10 kPa`)**, bloklar
   `1e7 Pa`. **Moloz yığını matrisi için `10 kPa` çok mu yüksek?**
   Literatürde kohezyon `1 – 100 Pa` mertebesinde veriliyor; öyleyse
   rejim değişir, zaman ölçeği `~100 s`'e çıkar — ve `0,2 s`'de hiçbir
   şey görememizi açıklar mı?

6. Yerçekimini `0,2 s`'de etkisiz sayıp **kapalı** koşuyoruz. Uzun
   koşuda açmak zorunlu mu, yoksa balistik hesap yeterli mi?

---

## 3. EJEKTA ÖLÇÜSÜ — belki tanımımız yanlış

Ölçütümüz: `r > R` **ve** `v_r > v_esc`, `t = 0,2 s`'de.

Sonuç `16` parçacık, `93,2 kg`. Ve `93,2 / 16 = 5,83 kg` — tam olarak
**en ince parçacığın kütlesi**. Yani ölçü **ayrıklaştırma tabanında**.

### Sorular

7. **Profesyonel kodlar ejekta kütlesini/momentumunu nasıl ölçüyor?**
   Parçacık başına kaçış ölçütü mü, yoksa ejekta **hız dağılımını**
   ölçüp entegre mi ediyorsunuz? Tanımımız fazla mı katı?

8. `v_esc = 0,082 m/s` çok düşük bir eşik, buna rağmen yalnızca `16`
   parçacık geçiyor. **Makul mü**, yoksa akışın hiç doğmadığının
   göstergesi mi?

9. Housen & Holsapple ejekta ölçekleme yasalarıyla kıyas için hız
   dağılımının kuyruğunu ölçüp entegre etmek daha mı doğru olur?

---

## 4. ÇÖZÜNÜRLÜK — sayılarımız sizinkilerle uyuyor mu

Şok ancak `s ≤ 0,175 m`'de kuruluyor. Mermi yarıçapı `0,371 m` — yani
mermi yarıçapı başına `~2` parçacık.

| `s_min` | sıkışma |
|---|---|
| `3,50 m` | `%0,006` |
| `0,875 m` | `%1,68` |
| `0,350 m` | `%22,0` |
| `0,175 m` | `%40,5` |

Ayrıca inceltme arayüzünde ciddi bir sorun bulduk: tek basamaklı
inceltmede kütle oranı `8 000` ve şok arayüzü **geçemiyor** —
şoklanan parçacıkların **tamamı** ince seviyeden, kaba seviyede
**sıfır**. Kademeli merdivenle (`8×` basamaklar) düzeldi.

### Sorular

10. **Mermi yarıçapı başına kaç parçacık** gerekiyor? Literatürde
    standart bir ölçüt var mı?

11. Çok çözünürlüklü SPH'de **arayüz kütle basamağı** için pratiğiniz
    ne? `2:1` aralık (`8:1` kütle) yeterli mi?

12. `h_ij = (h_i + h_j)/2` kullanıyoruz. Arayüzde bu `7,35 m`'ye
    şişiyor. **Simetrikleştirilmiş çekirdek**
    (`½[∇W(h_i) + ∇W(h_j)]`) bu ölçekte fark yaratır mı?

---

## 5. ELEDİKLERİMİZ — doğru mu eledik

`t_end = 0,2 s`, tek değişken, defter her kolda `~1e-14` ile kapalı:

| kol | `β_hedef` | kaçan hedef |
|---|---|---|
| güçlü matris (`Y₀ = 1e8`) | `1,033146` | `262 kg` (`45` parçacık) |
| hasarlı (Grady-Kipp açık) | `1,033097` | `93,2 kg` (`16`) |
| **taban** | `1,033102` | `93,2 kg` (`16`) |
| yerçekimli | `1,033102` | `93,2 kg` (`16`) |
| zayıf blok (`1 Pa`) | `1,033116` | `93,2 kg` (`16`) |
| zayıf matris (`1 Pa`) | `1,033098` | `93,2 kg` (`16`) |

(Üretim matrisi `Y₀ = 1e4 Pa`; tabloda `1e8` ve `1 Pa` ona göre.)

`Y₀`'ı **sekiz mertebe** değiştirmek `β_hedef`'i `5e-5` oynatıyor.

**Düşük yapay viskozite** kolu (`α_av 1,0 → 0,1`): kaçan kütle `132`
kat arttı **ama** `Δβ` `24` kat **düştü**, ve kaçan `33` parçacığın
**hepsi kaba seviyeden** (`372,8 kg`, en incenin `64` katı). Bunu
*çözülmüş ejekta* saymadık.

**Gözeneksiz kol şok kuramadı**: `α₀ = 1` ile parçacık kütlesi `1,76`
kat büyüdü, mermi-hedef bağlanması bozuldu, sıkışma `%0,00`.

### Sorular

13. **`Y₀`'ın bu kadar etkisiz olması beklenen mi?** Şok basıncı
    `20,3 GPa`, üretim matrisi `Y₀ = 1e4 Pa` — **iki milyon kat** fark.
    Mukavemet yalnızca geç evrede mi belirleyici, ve bizim koşu
    (`0,2 s`) o evreyi hiç görmüyor mu?

    (`Y₀`'ın sahneye **doğru ulaştığını** doğruladık: `--Y0 1.0` ve
    `--Y0 1e8` matris değerini gerçekten değiştiriyor. Yani duyarsızlık
    bir bağlantı kusuru değil.)

14. Gözenekliliği kapatma hipotezini **temiz** nasıl sınarsınız?
    (Bizim denememiz çözünürlük telafisi yapmadığı için düştü.)

---

## 6. EN AÇIK SORU

> **Bu motor neden kazmıyor?**
>
> Şok doğru değerde, momentum defteri kapanıyor, krater açılıyor —
> ama `93 kg` madde kaçıyor ve `β = 3,22` için gereken `~10⁶ kg`.
>
> Sizce en olası **tek** sebep nedir, ve onu ayırt edecek **en ucuz
> deney** hangisi?

---

## Ek — yöntem hakkında

Her deneyin yargı kuralı **koşudan önce** commit'leniyor; protokol
değişirse versiyonlanıp gerekçelendiriliyor
(`docs/truba/PROTOKOL-v2.md`). `42` kusur ölçümleriyle kayıtlı
(`docs/FAZ4-SIKINTI-RAPORU.md`); çürütülen yorumlar silinmiyor,
**geçersiz** işaretleniyor (`docs/anlik/`).

Eleştiriniz yöntemi de kapsayabilir — özellikle *"şu ölçütü yanlış
kurmuşsunuz"* türü geri bildirim en değerlisi olur.
