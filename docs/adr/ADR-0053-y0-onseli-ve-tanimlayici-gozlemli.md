# ADR-0053 — `Y₀` önseli gözlemi içermiyor; `Y₀`'yu tanımlayan gözlemli `M_ejekta`

**Durum:** ÖNERİ (karar kullanıcıda — **A2'nin cevabı**) · **Tarih:** 2026-10-04
**Öncül:** KAYIT-067 (W2 `Y₀` serisi), KAYIT-070 §1–§2 (gerçeklem sd'leri,
şekil betimleyicileri), KAYIT-072 (DY2 `MODEL GÖZLEME ULAŞIYOR`),
ADR-0044 (`DART_UZAYI_S3`), `inference/recovery.py` `C2` çakılma kuralı
**Kod:** `inference/onsel_denetimi.py` · **Sınav:**
`tests/test_onsel_denetimi.py` (19) · **Ölçüm:** PROTOKOL-DO (kilitli)

---

## 1. Bağlam — neden havuzdan **önce**

Üretim çıkarımının varsayılan uzayı `DART_UZAYI_S3`:

| eksen | alt | üst |
|---|---|---|
| `boulder_alpha0` | `1,00` | `1,30` |
| **`Y₀`** | **`1,0e3 Pa`** | **`1,0e7 Pa`** (log) |
| `f_boulder` | `0,05` | `0,50` |

Bu sınırlar ADR-0009'dan (genel malzeme) geliyor. Ama **model doğrulamamızın
tamamı** `Y₀ = 1 – 50 Pa`'da yapıldı (W2, UA, UY, UG, DY2, DK) — yani üretim
önselinin **tamamen dışında**. Bu, tek başına bir uyarı işareti.

`recovery.py`'nin `C2` ölçütü şöyle der (haklı olarak): *gerçek değer önselin
dışındaysa posterior sınıra dayanır, aldatıcı biçimde dar görünür ve bu eksen
**bilgilendirici sayılmaz*** (KAYIT-030 sınıfı). Yani önsel yanlışsa, 650
GPU-saatlik havuzun ana çıktısı olan `Y₀` posterioru **kendi kapımızdan
geçemez**.

## 2. Ölçüm — `β(Y₀)` güç yasası

W2 kıyas sahnesi, `t_geçiş = 1,0 s` (üretim), `600 s`, aynı `θ` (yalnız `Y₀`
değişiyor). Koşulardan okundu, uydurulmadı:

| `Y₀` | `β` | `M_ejekta` | `t50` | `t90` |
|---|---|---|---|---|
| `1 Pa` | 4,3889 | `5,671e7` | `1,674 s` | `25,76 s` |
| `10 Pa` | 4,0699 | `3,029e7` | `1,010 s` | `11,42 s` |
| `50 Pa` | 3,4938 | `1,596e7` | `0,461 s` | `4,42 s` |

`b = β − 1 = C · Y₀^p` uydurması: **`p = −0,0760`**, `C = 3,465`,
en büyük bağıl artık `%5,3`.

Tersine çevirince — gözlem `β = 3,12` hangi `Y₀`'ya düşüyor?

| yöntem | `Y₀` |
|---|---|
| güç yasası, `t_geçiş = 1,0 s` (üretim) | **`644 Pa`** |
| güç yasası, `t_geçiş = 0,2 s` | `210 Pa` |
| yalnız yerel eğim (`10 → 50 Pa`) | `176 Pa` |

Üçü de **`1e3 Pa`'nın altında**. Önselin kenarlarında modelin ne verdiği:

| önsel kenarı | öngörülen `β` | gözlem bandı `3,12 ± 0,34` |
|---|---|---|
| `Y₀ = 1e3 Pa` (alt) | `3,050` | bandın **içinde**, `0,2σ` altında |
| `Y₀ = 1e7 Pa` (üst) | `2,019` | bandın **altında**, `−3,2σ` |

**Kilitli yargı (`onsel_denetle`): `ÖNSEL GÖZLEMİ İÇERMİYOR`.**

Yani: önselin **üst `4` dekadı** gözlem tarafından tamamen eleniyor, posterior
kütlesi **alt kenara yığılır** ve `Y₀` ekseni `pinned` çıkar → `C2` onu
bilgilendirici saymaz. Havuz koşar, sonuç "`Y₀ ≤ 1 kPa`, önsel kenarı" olur.

> **Dürüstlük notu:** `644 Pa`, ölçülen aralığın (`1 – 50 Pa`) üst ucundan
> **`1,11` dekad** uzakta bir **dışdeğerlemedir** (`cok_uzak = True`) ve
> `p` küçük olduğu için kaldıraç büyük: `p`'deki `%10` hata `Y₀`'da `~%30`
> kayma demek. Bu yüzden karar **ölçümle** doğrulanacak → PROTOKOL-DO.

## 2a. Literatür de aynı yere bakıyor (2026-10-04, birincil arama)

L1/L2'nin kurduğu malzeme: matris dayanımı = **kohezyon** (sıfır basınçta
kayma dayanımı), aralık **`0 – 500 Pa`**; bloklara ayrıca `~10 MPa` çekme
dayanımı. Raducan ve diğ. 2022b ilk modelleri **kohezyonsuz**
(`Y₀ = 0 Pa`, iç sürtünme `f = 0,55`) yığınlara koştu.

Bizim `matrix_Y0` bunun **tam karşılığı**. Yani:

> Üretim önselinin alt kenarı (`1e3 Pa`), literatürün Dimorphos için
> kullandığı **bütün aralığın üstünde**. Önsel, literatürün hiç
> denemediği bir bölgede yoğunlaşıyor.

Önerilen `[1e0, 1e5] Pa`, literatürün `0 – 500 Pa` aralığını (sıfır hariç,
log ölçek sıfırı alamaz) ve modelimizin doğrulandığı `1 – 50 Pa`'yı
**içeriyor**, üstte `2` dekad pay bırakıyor.

## 2b. Bu karar **önceden kaydedilmişti** (PROTOKOL-U §4, 2026-09-14)

Bu ADR'nin önerisi yeni bir fikir değil; **koşulardan önce yazılmış** bir
yorum tablosunun uygulanmasıdır. PROTOKOL-U §4, `U1` (`Y₀ = 1e1 Pa`,
"önsel dışı" diye işaretli) ve `U2` (`1e0 Pa`) varyantları için şu satırı
taşıyor:

| sonuç | anlamı | sıradaki adım |
|---|---|---|
| `U1/U2 ulaşıyor` | `Y₀` önseli (`≥ 1e3 Pa`) gerçek Dimorphos'u dışarıda bırakıyor | **ADR: önsel alt sınırı `1 Pa`'ya**; N/P yeniden |

**Dürüst okuma:** U/V'nin kendi yargısı `HİÇBİR VARYANT ULAŞMIYOR` çıktı
(KAYIT-064), yani bu satır U/V'de **tetiklenmedi**. Ama o koşular `0,1–0,2 s`'de
kesilmişti. Geç evre modelinde **aynı `θ`** (`Y₀ = 10 Pa`, yani `U1`'in
değeri) DART sahnesinde **gözleme ulaşıyor** (DY2, KAYIT-072). Yani satırın
**koşulu** artık sağlanıyor ve reçetesi — önsel alt sınırı `1 Pa` — bu ADR'nin
önerisiyle **birebir aynı**. Karar sonradan uydurulmuş değil.

## 2c. Karar **C1'den bağımsız** (en önemli nokta)

Gözlenen `β` olarak hangi sayının kilitleneceği (**C1**) hâlâ açık. Bu ADR'yi
C1'e bağımlı kılmamak için her aday ayrı ayrı çevrildi
(W2 serisi, üretim `t_geçiş`):

| gözlenen `β` adayı | kaynak | ima edilen `Y₀` | eski önsel `[1e3, 1e7]` | **önerilen `[1e0, 1e5]`** |
|---|---|---|---|---|
| `3,748` | DY2 modelinin kendi değeri (kıyas) | `21 Pa` | **dışında** | içinde |
| `3,600` | yayınlanan, Cheng ve diğ. 2023 (tam yörünge) | `44 Pa` | **dışında** | içinde |
| `3,320` | arayüz bandı üst (`ΔT − 1σ`) | `196 Pa` | **dışında** | içinde |
| `3,223` | arayüzün kendi türettiği (`M = 4,3e9`) | `346 Pa` | **dışında** | içinde |
| `3,125` | arayüz bandı alt (`ΔT + 1σ`) | `625 Pa` | **dışında** | içinde |
| **`3,120`** | **PROTOKOL-U'da kilitli hedef** | **`644 Pa`** | **dışında** | içinde |
| `3,019` | L16 yeniden şekillenme (`125 s`) | `1223 Pa` | içinde | içinde |
| `2,816` | L16 yeniden şekillenme (`250 s`) | `4951 Pa` | içinde | içinde |

İki sonuç:

1. **Yeniden şekillenme düzeltmesi uygulanmadıkça, hiçbir aday eski önselin
   içinde değil.** Eski önseli kurtaran tek senaryo, `period_interface`'in
   kendi notuyla *"arama özeti, tam metin teyidi bekliyor"* diye işaretlediği
   L16 (Nakano ve diğ. 2024) düzeltmesidir — yani adayların **en az
   yerleşmiş** olanı.
2. **Önerilen önsel bütün adayları içeriyor**, en yakın kenara `1,31` dekad
   boşlukla. Yani **önsel kararı C1 çözülmeden verilebilir** ve C1 sonradan
   nasıl kapanırsa kapansın önsel yeniden açılmaz. Adayların tamamı
   `2,37` dekada yayılıyor; `5` dekadlık önsel bunu rahat alır.

> Bu, ADR'nin dairesel olmadığının da kanıtı: önsel, **tek bir** gözlem
> sayısına göre seçilmiyor; sekiz adayın **hepsini** kapsayacak biçimde ve
> literatür + modelin doğrulandığı aralık gerekçesiyle seçiliyor.

## 3. İkinci ölçüm — `Y₀`'yu hangi gözlemli **tanımlıyor**

Aynı üç koşudan, her gözlemli için `v = C · Y₀^p` ve "`1σ`'ya karşılık gelen
`Y₀` çarpanı" (`duyarlilik_tablosu`):

| gözlemli | gözleniyor mu | `p` | `1σ` → `Y₀` çarpanı | dekad |
|---|---|---|---|---|
| `t90` | **hayır** (tanı) | `−0,444` | `×1,51` | 0,18 |
| `t50` | **hayır** (tanı) | `−0,322` | `×1,76` | 0,25 |
| **`M_ejekta`** | **evet** (L17) | **`−0,321`** | **`×1,96`** | **0,29** |
| `β` | **evet** (PROTOKOL-U) | `−0,076` | **`×12,41`** | **1,09** |

**`β` tek başına `Y₀`'yu ancak `×12` (bir dekaddan fazla) içine sıkıştırıyor.
`M_ejekta` aynı işi `×1,96` ile, yani `6,3 kat` daha iyi yapıyor.**

Sebep fizikte: `β` bir **oran** ve `M_ejekta × hız` ile `M_ejekta`'nın
hız dağılımı arasındaki değiş-tokuşla kısmen sabitleniyor; `M_ejekta` ise
dayanıma doğrudan bağlı (daha güçlü matris → daha az malzeme kopuyor).

Üst sınır denemesi: `M_ejekta`'nın bütçesine küre/elipsoit farkı da
(`%56`, KAYIT-072 §3) eklenirse çarpan `×4,45`'e çıkar — **yine `β`'dan
`2,8` kat iyi**, ama `ESIK_CARPAN_TANIMLI = 3,0` eşiğini aşar ve yargı
`Y0 GOZLEMLILERLE TANIMLANAMAZ` olur. Yani `M_ejekta`'nın şekil terimi
**ölçülmek zorunda** (şu an yalnız `β` için ölçüldü).

`t50`/`t90` daha da duyarlı ama **DART için ölçülmüş karşılıkları yok**:
posteriora giremezler, yalnız mekanizma tanısı olurlar (KAYIT-072 §3).

## 3b. **Niçin** `M_ejekta` daha iyi — ölçülen sebep (KAYIT-073)

`β`'nın `Y₀`'ya zayıf bağlı olması bir *götürme*:

    β − 1 = K · M_kaçan · v_ort · kos_ort / p_mermi      (K⁻¹ = 0,8347 ± 0,0052)

| çarpan | `Y₀` üssü |
|---|---|
| `M_kaçan` | `−0,3221` |
| `v_ort` | `+0,1866` |
| `kos_ort` | `+0,0585` |
| **toplam** | `−0,0769` |
| `β − 1`'in bağımsız ölçülen üssü | `−0,0760` (`%1,3` uyum) |

Dayanım artınca kaçan kütle `%32`/dekad düşüyor, ama kaçan daha hızlı
(`+%19`) ve daha toplu (`+%6`); `β` geriye `%8`/dekad bırakıyor.
`M_ejekta`'nın `6,3` kat kazancı buradan: **götürmeye katılmayan, en dik
çarpan odur.** Ayrıntı ve sınavlar: KAYIT-073,
`observables/ejekta_ayrismasi.py`.

Aynı ayrıştırma üçüncü gözlemlinin nerede olduğunu da söylüyor:
`(β, M_ejekta)` üç çarpandan ikisini sabitler, serbest kalan **yönelim**
(`kos_ort`) ve o **A95** yüzünden gözlemle kıyaslanamıyor.

## 4. Karar (öneri)

1. **`Y₀` önseli aşağı taşınır:** `Y₀ ∈ [1e0, 1e5] Pa` (log, 5 dekad).
   Gerekçe: (a) literatürün Dimorphos aralığını kapsıyor (L1/L2: birkaç
   `Pa` – `500 Pa`), (b) modelin **doğrulandığı** aralığı (`1 – 50 Pa`)
   içeriyor, yani vekil dışdeğerleme yapmıyor, (c) ölçülen `644 Pa`'yı
   `2,8` dekad üstü ve `2,8` dekad altı boşlukla içeriyor →
   `onsel_denetle` yargısı `ÖNSEL GÖZLEMİ İÇERİYOR`.
   **Eski `[1e3, 1e7]` tanımı silinmez** (ADR-0044'ün `DART_UZAYI` emsali):
   karar geri alınabilir ve gerileme sınavları koşabilir kalır.
2. **Posterior `β` ile yetinmez:** `M_ejekta` ikinci gözlemli olarak girer.
   `grid_posterior` zaten çok gözlemli; eksik olan **karar**dı. `β` tek
   başına `Y₀`'yu bir dekaddan iyi veremez; ölçüm bunu gösteriyor.
3. **`M_ejekta`'nın şekil terimi ölçülür** (DY2/DK'dan zaten var: `%56` üst
   sınır; gerçek şekil modeline karşı ölçüm ayrıca gerekir). Ölçülmezse
   `M_ejekta`'nın kazancı `6,3` değil `2,8` kat yazılır — yine de kazanç.
4. **Karar ölçümle kilitlenir:** `644 Pa` bir dışdeğerleme olduğu için
   PROTOKOL-DO iki koşuyla (`Y₀ = 500 Pa` ve `5000 Pa`, DART sahnesi)
   aralığı genişletir ve yargı **interpolasyonla** verilir. DO'dan önce
   önsel **değiştirilmez**.

## 5. Reddedilen seçenekler

- **Önseli hiç değiştirmemek.** Posterior alt kenara çakılır, `C2` düşer,
  havuzun ana çıktısı yok sayılır. 650 GPU-saatin karşılığı "`Y₀`, önsel
  kenarında" olur.
- **Önseli `644 Pa`'ya ortalamak** (ör. `[1e2, 1e4]`). Gözlemin kendi
  türetildiği sayıya göre önsel seçmek **dairesel**dir ve posteriorun
  genişliğini yapay olarak küçültür. Önsel, gözlemden **bağımsız**
  gerekçeyle (literatür + modelin doğrulandığı aralık) seçilir.
- **`β`'yı tek gözlemli tutup `Y₀`'yu "zayıf tanımlı" ilan etmek.** Dürüst
  ama gereksiz: `M_ejekta` ölçülü bir gözlemli ve `6,3` kat kazanç veriyor.
  Elde varken kullanmamak savunulamaz.
- **`t50`'yi posteriora sokmak.** DART için ölçülmüş karşılığı yok; modelden
  modele karşılaştırma gözlem yerine konamaz.

## 6. Sonuçları

- `DART_UZAYI_S3` **değişmez** (ADR kabul edilene kadar); yeni uzay yanına
  eklenir ve varsayılan **karar sonrası** döner.
- Havuz tasarımı `Y₀` ekseninde 5 dekada yayılır; `log = True` olduğu için
  nokta sayısı değişmez.
- `kalibrasyon.sbc_calistir` ve `tanimlanabilirlik.posterior_daralma`
  yeni uzayla koşar; SBC'nin `PIT` düzgünlüğü önselin doğru seçilmesine
  **bağlı** olduğu için bu ADR kalibrasyonun ön koşuludur.
- Risk: `Y₀ = 1 Pa` civarı neredeyse dayanımsız; `t_adım` küçülüp maliyet
  artabilir. DO'nun `500 Pa` kolu bunu *ters* yönde sınar (daha güçlü matris
  → daha hızlı koşu beklenir); `1 Pa` ucu W2'de zaten koşuldu, sorun çıkmadı.
