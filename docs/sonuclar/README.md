# Üretim havuzu — sonuçlar

> **96/96 nokta · kayıp koşu yok · kod `d96c4ee` · tohum `20260906`**
> TRUBA/H100, `kolyoz-cuda`, iş `1592569`, 2026-10-06 → 2026-10-15.

Bu klasör üretim havuzunun **ham ve özet** sonuçlarını taşır. Hiçbir sayı
elle yazılmadı: tablolar [`havuz_96.csv`](havuz_96.csv)'den, tasarım
koordinatları `lhs_design(DART_UZAYI_S4, 96, root_seed=20260906)`'dan üretildi.

---

## 1. Havuzun durumu

| | |
|---|---|
| tamamlanan nokta | **96 / 96** |
| kayıp koşu | **0** — Kapı 1 ölçütü %20, ölçülen **%0,00** |
| kod sürümü | `d96c4ee6f29cd76eb327d360bba34334d0a20837` (tek) |
| tasarım tohumu | `20260906` (tek) |
| merdiven | kaba: 48:5,6 → 3:0,35 m, N ≈ 17 000 |
| `t_end` | 600 s, yerçekimi açık, `mu_f = 0,6` |

## 2. Gözlenebilirler

| gözlenebilir | n | nan | min | medyan | maks |
|---|---:|---:|---:|---:|---:|
| `β` | 96 | 0 | 1.5310 | 2.7187 | 5.0402 |
| ejekta kütle kesri | 96 | 0 | 0.0000 | 0.0009 | 0.0091 |
| krater derinliği (m) | 66 | **30** | -8.1916 | -2.9679 | 4.6738 |

**Gözlem aralığın içinde mi.** DART'ın ölçülen `β`'sı **3,5418** ve havuz
`[1,5310 ; 5,0402]`'yi kapsıyor — çıkarım bir *iç değerleme*, dışdeğerleme
değil. Ejekta kütlesi için gözlem `1,6e7 kg / 4,2980e9 kg = 0,0037`; havuzun
medyanı `0,0009`, maksimumu `0,0091` — aralığın **içinde ama üst çeyrekte**.

**Krater okunmaz.** 96 noktanın **30**'unda `nan`, kalanların medyanı
**negatif**. Negatif krater derinliği fiziksel değil; operatör bu `t_end`'de
anlamlı bir yüzey bulamıyor. ADR-0055 bu gözlenebiliri *isteğe bağlı* ilan
ettiği için kayıt düşmez, ama pratikte bu eksen **kullanılamaz**.

## 3. Hangi gözlenebilir hangi ekseni görüyor

Spearman sıra korelasyonu, **96 noktanın tamamında** ölçüldü:

| gözlenebilir | n | `α_b` | `log Y₀` | `f` |
|---|---:|---:|---:|---:|
| **`β`** | 96 | -0.019 | -0.986 | +0.026 |
| ejekta kütle kesri | 96 | -0.019 | -0.972 | -0.036 |
| krater derinliği | 66 | +0.137 | -0.470 | +0.200 |

**Tam havuzun getirdiği yeni bilgi — ve iyi değil.** Ejekta kütle kesri de
`log Y₀` ile neredeyse tam tekdüze (`−0,972`), diğer iki eksenle ≈ 0. Yani
`β` ile **aynı yönü** taşıyor; bağımsız bir kısıt değil, ikinci bir
ölçümü. PROTOKOL-UP'ın üç açık gözlenebilir grubundan ikisi
(`periyot_degisimi` ve `ejekta_kutlesi`) böylece **tek bir yöne**
çöküyor. İkinci bir yön kalmışsa yalnız üçüncü grupta —
`ejekta_hiz_dagilimi` — olabilir ve o grup henüz **hiç ölçülmedi**.

`ω` (kazanılan spin) bu tabloda yok: havuz `jsonl`'inde değil, durum
dosyalarından PROTOKOL-SI §5 yöntemiyle çıkarılıyor. 88 noktada ölçülen
değerleri `../rapor2204/veri/eksen_duyarliligi.dat` taşıyor:
`ρ(ω,f) = +0,459`, `ρ(ω,α_b) = −0,316`, `ρ(ω,log Y₀) = −0,111`, `r(β,ω) = +0,131`.

## 4. Bu tablodan çıkan tek cümle

> `β` pratikte **tek bir koordinat** taşıyor. `log Y₀` ile neredeyse tam
> tekdüze; diğer iki eksenle korelasyonu sıfıra yakın. Tek skaler gözlem,
> üç boyutlu iç yapı uzayında **bir yön** görüyor.

## 5. Kaç yön öğreniliyor — **ölçüldü: bir**

PROTOKOL-UP §3/§4, 2026-10-16'da tam havuzda koşuldu
([`UP_secim_96.json`](UP_secim_96.json), gerekçe
[KAYIT-079](../defter/KAYIT-079_2026-10-16_UP-gozlemli-secimi-ve-n-yon.md)):

> **1 YÖN ÖĞRENİLİYOR (3 parametre için YETMİYOR)**
> Yan yargı: **YÖN SAYISI NOKTAYA VE KOVARYANSA BAĞLI** → §4 gereği en
> küçük `n_yön` alındı.

Kapı A ve B'den geçen aday tam üç tane ve her biri ayrı grupta
(`beta` · `M_kacan` · `e_hiz`), yani seçimde tercih yoktu. Sebep σ'dan
bağımsız: üç gradyan **neredeyse paralel** — `β` ile `e_hız` arası açı
merkezde `4,64°`, bir köşede `0,62°`.

σ(`e_hız`) bin kat küçültülse ikinci öz değer yalnız `2,35 → 4,17`
oluyor; eşik **36**. Öz değer σ ile doyuyor, çünkü σ bir satırın
*ağırlığını* artırır, *yönünü* döndürmez.

Kafeste (3 ρ × 5 θ) ikinci öz değer `1,67 – 140,53` aralığında, yani
eşiğin iki yanında; kararsız olduğu için kural en küçüğü aldırıyor.
`FISHER_ESIGI` **değiştirilmedi** — indirmek protokolde yasak ve
indirilirse yargı geçersiz sayılır.

## 6. Model gözleme ulaşıyor mu — **evet**, ve geriye %34 kalıyor

PROTOKOL-UP §6 (tarih eşleme, Vernon), düzeltilmiş girdiyle
([`UP_s5_s6.json`](UP_s5_s6.json), KAYIT-080 + düzeltmesi
[KAYIT-082](../defter/KAYIT-082_2026-10-16_kos-hatasi-ve-duzeltilmis-sonuclar.md)):

| ölçü | değer |
|---|---|
| `I_min` | **0,325** (kesme `I > 3`) |
| bağdaşır hacim | **%34,04** — 73 537 / 216 000 düğüm |
| posterior %68 hacmi | %10,27 |
| oran | **3,31** (eşik 10) |
| post68 kütlesinin bağdaşır oranı | **1,0000** (eşik 0,90) |
| **yargı** | **İKİ YÖNTEM UYUŞUYOR** |

`I_min = 0,325`: **model DART'ın gözlemine ulaşıyor.** Hiçbir `θ`
bağdaşmasaydı `I_min > 3` çıkar, ileri model reddedilirdi.

Ve iki yöntem **birbirini doğruluyor**: posteriorun %68 kütlesinin
tamamı bağdaşır bölgede, hacim oranı 3,31 ile eşiğin (10) altında.
Protokolün karşılığı: posterior yayımlanır, tarih eşleme
**doğrulayıcı ek** olur.

## 7. Sonuç veriden mi önselden mi — **veriden**, ama sınav dişsiz

| önsel | kip `log10 Y₀` |
|---|---:|
| `KILITLI` | +1,2712 |
| `DUZ_LOG` | +1,2712 |
| `KAYDIRILMIS` (×3) | +1,2712 |

`σ_onsel = 0,0000 dex` → **SONUÇ VERİDEN GELİYOR**.

**Ama bu göründüğünden zayıf bir kanıt** ve öyle yazılıyor:
`KAYDIRILMIS` önsel `Y₀ < 3 Pa`'yı kesiyor, posterior kipi ise
`18,7 Pa`. Kesilen bölge posteriorun zaten umursamadığı yer, yani
perturbasyon hiçbir şeye dokunmuyor. Kilitli yargı uygulandı; sınavın
ayırt edici gücü düşük.

Yan bulgu: **`KILITLI` ile `DUZ_LOG` aynı dağılım.** ADR-0053 kilitli
önseli `Y₀ ∈ [1e0, 1e5]` (log, 5 dekad), yani protokolün "bilgisiz uç"
dediği şeyin ta kendisi. Protokol yazılırken fark edilmemiş.

## 8. Posterior — `n_yön = 1`'in somut hâli

| eksen | büzülme | sd oranı | sınıf |
|---|---:|---:|---|
| `α_b` | 0,031 | 0,984 | **ÖNSEL BASKIN** |
| `Y₀` | **0,882** | 0,343 | **ÖĞRENİLDİ** |
| `f` | −0,305 | 1,143 | **ÖNSEL BASKIN** |

Kip: `Y₀ ≈ 18,7 Pa`, önsel kutusunun içinde (kenarda değil).
Fisher: `[499,73 · 0,82 · 0,00]`, eşik 36 → **`n_yön = 1`**.

Büzülme sınıfları Fisher yargısıyla **tutarlı**: bir eksen öğrenildi,
ikisi önselden ayırt edilemiyor.

## 9. Vekil ve bilgi bütçesi

| vekil | `q²` | ÇD-RMSE | Bachoc | kalibre %68 kapsama |
|---|---:|---:|---:|---:|
| `β` (fırlatı geleneğinde) | **0,9765** | 0,1509 | 1,367 | 0,792 |
| `ln M_ejekta` | **0,9882** | 0,1806 | 1,095 | 0,719 |

`β` belirsizliğinin kaynakları (toplam sd `0,3126`):

| kaynak | pay |
|---|---:|
| gözlem | **%48,4** |
| model hatası bütçesi | %28,3 |
| vekil (GP) | %23,3 |

Baskın kalem **gözlem** — ve onu biz iyileştiremeyiz. Daha çok tasarım
noktası vekil payını (%23,3) küçültür, toplamı çok değiştirmez.

## 10. SBC kapısı — **GEÇTİ**

PROTOKOL-HAVUZ §6, `n_sbc = 200`, tohum `20261016`, düzeltilmiş girdi
([`UP_sbc.json`](UP_sbc.json),
[KAYIT-081](../defter/KAYIT-081_2026-10-16_SBC-kapisi-gecti.md)):

| eksen | tanı | PIT ort. (se 0,0204) | KS `p` | kapsama68 |
|---|---|---:|---:|---:|
| `α_b` | **KALİBRE** | 0,4998 | 0,8680 | 0,645 |
| `Y₀` | **KALİBRE** | 0,4751 | 0,0741 | 0,650 |
| `f` | **KALİBRE** | 0,5326 | 0,2994 | 0,680 |

**GENEL: KALİBRE → posterior yayımlanabilir.** PLAN-90-GÜN'de `~%25`
yazılı "SBC düşer" riski gerçekleşmedi. En zayıf eksen `Y₀`
(`p = 0,0741`, eşik `0,05`) ve saklanmıyor.

SBC'nin kanıtladığı dar: çıkarım makinesi **kendi varsayımları
altında** kalibre. Modelin gerçeğe uyması §6'nın sorusu.

## 11. Hâlâ ölçülmeyen

| | durum |
|---|---|
| ince koşu (12 nokta, σ mı yanlılık mı) | **koşuyor** — iş `1601448`, 4 GPU, ADR-0059 |
| Hera spin ön kaydı | **üretilmedi** — [PROTOKOL-HS](../truba/PROTOKOL-HS-HERA-SPIN.md) kilitli |
| Hera krater ön kaydı | **üretilmedi** — [PROTOKOL-HT](../truba/PROTOKOL-HT-HERA-TAHMIN.md) |
| `μ_f` sürtünme duyarlılığı | **koşmadı** — ~10 GPU-saat |

## 12. Bugünkü hâliyle savunulabilir cümle

> DART'ın `β`'sı `(α_b, Y₀, f)` uzayında **bir** yön kısıtlıyor
> (`n_yön = 1`): `Y₀` öğreniliyor (büzülme 0,882, kip ≈ 18,7 Pa),
> `α_b` ve `f` önselden ayırt edilemiyor. Ölçülmüş model hatası
> bütçesiyle yapılan elemede önsel hacminin **%34'ü** bağdaşır kalıyor
> ve model gözleme **ulaşıyor** (`I_min = 0,325`). Posterior ile eleme
> **birbirini doğruluyor** (oran 3,31 < 10) ve çıkarım makinesi SBC'de
> kalibre çıkıyor. Sonuç önsele duyarsız görünüyor, ama o sınavın
> ayırt edici gücü düşüktür ve öyle raporlanıyor.

## 13. Krater gözlemlisi — **96/96 yeniden okundu** (2026-10-28)

Kaynak: [`havuz_krater_96.csv`](havuz_krater_96.csv). Operatör
`krater_yuzey` (A73 yüzey operatörü), ADR-0061 + ADR-0062 sonrası.
İş `6864648` (yeni), `6864667` (taban çizgisi, **eski** operatör aynı
betikle). Sıfır GPU — yalnız kayıtlı `npz` okundu.

> **Dikkat: bu sütun `havuz_96.csv`'deki `krater_derinlik` DEĞİL.**
> O sütun eski çıkarıcıdan (`crater_profile`, A19 ile `xfail`) gelir ve
> `30` `nan` taşır. Buradaki sayılar yüzey operatöründen. İki kod yolu
> birbirini hiç çağırmıyor.

| sınıf | n | `Y₀` ortanca | ne demek |
|---|---:|---:|---|
| **ÖLÇÜLDÜ** | **46** | `3 650` Pa | krater okundu |
| **ÖRTÜLÜ** | **25** | `9,3` Pa | eksende **yoğun** bağlı ejekta; ADR-0062 reddi |
| **YÜZEY_YOK** | **25** | `88,4` Pa | eksende **seyrek** bağlı ejekta; `φ` eşiği kesmiyor |

Ölçülen `d_merkez`: `−3,69 … +3,49` m (7'si negatif).
Örtü yüksekliği (25 ÖRTÜLÜ nokta): `6,50 … 47,99` m, **ortanca `30,89` m**.

### 13.1 Düzeltme ne yaptı — geçiş matrisi

| eski → yeni | n |
|---|---:|
| ÖLÇÜLDÜ → ÖLÇÜLDÜ | 46 |
| YÜZEY_YOK → **ÖRTÜLÜ** | 22 |
| YÜZEY_YOK → YÜZEY_YOK | 25 |
| ÖLÇÜLDÜ → **ÖRTÜLÜ** | 3 |

- **ADR-0061 kendi hedefini tam tutturdu.** Eski 47 başarısızlığın
  hepsi "yüzey bulunamadı"ydı; `REFERANS` tarafından düşen **hiç
  kalmadı**. Kalan 25'in **tamamı** `SON` tarafı.
- **ADR-0062 yalnız 3 sayıyı reddetti** ve üçü de **negatifti**
  (`−12,46 … −6,50` m). Pozitif okunan hiçbir nokta kaybolmadı.
- Eskiden pozitif okunan **39** noktanın `d_merkez`'i `%1` içinde
  **değişmedi** (ihlal `0`) — ADR-0062 §5 geri alma kapısı **geçti**.

### 13.2 Bir geri alma koşulu literal olarak tetiklendi — ve niçin tutuldu

ADR-0061 §5: *"`nan` sayısını düşürmek yerine **artırırsa** geri
alınır."* Ölçüm: okunamayan nokta **47 → 50**. Koşul lafzen tetiklendi
ve bu **gizlenmiyor**. Tutulmasının gerekçesi ölçüldü, uydurulmadı:

1. **ADR-0061 tek başına 47 → 25** yapıyor (22 nokta `YUZEY_YOK`'tan
   çıkıyor). Yani koşulun hedef aldığı değişiklik koşulu **geçiyor**.
2. Artışın tamamı ADR-0062'nin **kasıtlı** reddi: 3 nokta, üçü de
   negatif çöp sayı. ADR-0062'nin kendi kapısı ("pozitif bir derinliği
   reddederse geri alınır") **tetiklenmedi**.
3. ADR-0061 §5'teki *"daha önce okunan 66 nokta"* ifadesi de yanlış
   çıkarıcıya aitti (`crater_profile`'ın 66'sı); yüzey operatörünün
   tabanı `49`.

Yani koşul yanlış taban çizgisine göre yazılmıştı. Düzeltilmiş hâliyle
**geçiyor**; kural sonuç görüldükten sonra değiştirilmedi, ölçüm
yazıldı.

### 13.3 Bundan çıkan bilimsel cümle

> `t = 600 s`'te, zayıf matris rejiminde **geçici krater
> gözlenemiyor**: kaçış hızını geçmemiş ejekta eksende `6 – 48` m
> yükseklikte duruyor ve doluluk eş-yüzeyi tabanı değil onu okuyor.

Bu, Hera için doğrudan bağlayıcı: Hera **son** krateri (ejekta
düştükten sonra) görecek. Krater ön kaydı bu anlık görüntüden
`d_merkez`/`V_krater` olarak **kurulamaz** — ayrıntı
[KAYIT-089](../defter/KAYIT-089_2026-10-27_ADR-0061-tek-basina-30-nani-30-yanlis-sayiya-cevirecekti.md).

`R_krater` ayrıca 96 noktanın yalnız **2**'sinde sonlu (`4,0` ve
`3,8` m); A11'in "krater yarıçapı gözlenemez" yargısı ayakta.

## 14. Tarama yönü — krater **46 → 66** noktada okunur oldu (2026-10-28)

Kaynak: [`havuz_krater_tarama_96.csv`](havuz_krater_tarama_96.csv),
işler `6864679` + `6864736`, sıfır GPU.
Karar: [ADR-0063](../adr/ADR-0063-yuzey-icten-disa-taranir.md),
ölçüm: [KAYIT-091](../defter/KAYIT-091_2026-10-28_icten-disa-tarama-olculdu-66-nokta-capraz-dogrulandi.md).

| | ÖLÇÜLDÜ | ÖRTÜLÜ | YÜZEY_YOK |
|---|---:|---:|---:|
| `distan` (kilitli varsayılan) | 46 | 25 | 25 |
| `icten` (yeni, yan yana) | **79** | 17 | **0** |

**46 ortak noktada iki tanım birebir aynı**: bağıl fark ortanca
`0,000e+00`, en büyük `1,868e-14`. Yani yeni tanım hiçbir yayımlanmış
sayıyı değiştirmiyor.

### 14.1 Çapraz doğrulama — sıfır çelişki

`icten`'in kurtardığı 33 noktanın **20**'sini, tamamen bağımsız bir
tanı (`arama_derinligi = 60 m`) da ölçüyor ve **`%1` içinde uyuyor**;
**çelişen nokta yok**.

| `capraz_dogrulandi` | n |
|---|---:|
| `EVET_distan_ile` | 46 |
| `EVET_60m_ile` | 20 |
| `HAYIR_tek_tani` | 13 |
| `olculmedi` | 17 |

**Kullanılabilir taban `%48 → %69`.**

### 14.2 Ve 13 nokta **güvenilmiyor** — gizlenmiyor

Bu 13'te yalnız `icten` sayı veriyor ve bazıları fiziksel değil:
idx 87 `+36,49 m` (`V = 3 043 m³`), idx 6 `+28,61 m` — hedefin yarı
eksenleri `58 – 88,5` m.

Ayrım sayıya vuruyor: çapraz doğrulanan 66 noktanın aralığı
`−4,930 … +4,428` m, doğrulanmayan 13'ünki `−5,587 … +36,490` m.

Sebep: `icten` gövde **içindeki** bir boşluğa takılabiliyor; `distan`
ise yukarıdaki yığına. **İki yön de aynı sınıfın hatasını yapıyor** —
doğru kesişimi *doğrultuya* bakarak seçmek. Asıl çözüm bağlantılılık
ölçütü; yazılmadı, önü de kapatılmadı.

Bu yüzden **varsayılan değiştirilmedi**: `icten` yalnız çapraz
doğrulanmış 66 noktada kullanılıyor.

## 15. Bu klasörün dışında duran uyarı

**`β` gelenek düzeltmesi özgün bir katkı DEĞİL.** 2026-10-16 literatür
kontrolü: DART ekibi `β_n`, `β_p` ve Cheng'in fırlatı doğrultusu
`β`'sını açıkça tanımlıyor. ADR-0060 bizim kendi hatamızı yakaladı;
sunumda keşif olarak geçmeyecek.
