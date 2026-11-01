# KAYIT-092 — Doluluk hipotezim **çürüdü**; mühür atıldı; geç döküm gönderildi

**Tarih:** 2026-11-01 · **İşler:** `6867334` (doluluk tanısı, 0 GPU),
`1639229_[0-3]` (geç döküm, **4 GPU**)
**Öncül:** [KAYIT-091](KAYIT-091_2026-10-28_icten-disa-tarama-olculdu-66-nokta-capraz-dogrulandi.md),
[ADR-0063](../adr/ADR-0063-yuzey-icten-disa-taranir.md)
**Mühür:** `docs/onkayit/ONKAYIT_HERA_KRATER_uretim66.json`
(SHA-256 `1b3b811e…`)
**Protokol:** [HT EK-2](../truba/PROTOKOL-HT-EK2-2026-11-01.md)

---

## 1. Tek cümle

13 noktanın savunulamayan değer vermesini "SPH birim bölünmesi
bozuluyor" diye açıklamayı denedim; **ölçüm bu açıklamayı çürüttü**
(`AUC = 0,203`, yani ters). Açıklamadan önce yazdığım bağlantılılık
kipini de geri aldım. Krater ön kaydı elde olanla mühürlendi ve asıl
soruyu sınayacak geç dökümlü koşu gönderildi.

## 2. Hipotez ve niçin makul görünüyordu

Eksendeki doluluk profilleri basıldı (`10 m` adımla, merkezden dışa):

| idx | `Y₀` (Pa) | son durumda `φ` |
|---:|---:|---|
| 1 | 58 708 | `0,94 0,98 1,05 0,90 1,14 1,17 0,34 0,00` |
| 2 | 1 266 | `0,94 0,98 1,04 0,89 1,18 1,14 0,36 0,01` |
| 6 | 5,76 | `0,86 0,67 0,65 **0,46 0,48** 0,77 0,74 0,59` |
| 87 | 1,35 | `0,82 0,72 0,60 **0,29** 1,33 **3,13** 1,80 1,00` |
| — | referans (96'sında da) | `0,95 0,96 1,05 0,92 1,09 1,19 0,44 0,00` |

SPH özdeşliği `Σ (m_j/ρ_j) W = 1` der: cismin içinde doluluk birdir.
Zayıf matriste `0,29`'a düşüyor, `3,13`'e çıkıyor. "O hâlde orada
bulunacak bir `φ = 0,5` yüzeyi yok, hangi yönden tararsan tara" —
makul görünüyordu.

## 3. 96 noktada ölçüldü — ve **çürüdü**

`scripts/tani_doluluk_birim_bolunmesi.py`, iş `6867334`.

Referans durum **denetim** olarak kullanıldı ve işini yaptı: iç maks
`φ` **`1,230 – 1,232`** (96 noktanın hepsinde, çok sıkı), iç min
`0,500 – 0,569`. Yani tanının kendisi sağlam.

Son durumda doluluk gerçekten bozuluyor: iç `φ` **`0,110 … 5,115`**,
`r(log₁₀ Y₀, iç min φ) = −0,433`. Bozulma gerçek ve `Y₀` ile ilişkili.

**Ama başarısızlıkları açıklamıyor:**

| küme | n | iç min `φ` ortanca | referans tabanının (`0,500`) altı |
|---|---:|---:|---:|
| çapraz doğrulanan (ÖLÇÜLDÜ) | 66 | **0,458** | **50/66** |
| `HAYIR_tek_tani` | 13 | 0,529 | 6/13 |
| `olculmedi` (krater okunamıyor) | 17 | **0,823** | **0/17** |

Krater **okunamayan** 17 noktanın iç dolululuğu en **sağlıklı** olanlar;
okunabilen 66'nın 50'si tabanın altında.
**`AUC(iç min φ; doğrulanan vs doğrulanmayan) = 0,203`** — ayırt edici,
ama **ters yönde**. Hipotezin öngördüğünün tam tersi.

İki absürt değerin ikisi de hipoteze uymuyor: idx 87'nin iç maks `φ`'si
`3,126` (uyar gibi) ama idx 6'nın `0,860`, yani referansın **altında**
— biri aşırı sıkışma, öteki aşırı genleşme. Tek bir mekanizma değil.

> **Ders.** Bir açıklama elimdeki beş noktada "görünüyor" diye doğru
> olmuyor. 96 noktada sayılınca ters çıktı. Önce ölçüp sonra
> açıklamanın karşılığı bu; tersi olsaydı rapora yanlış bir mekanizma
> girecekti.

## 4. Yazdığım `tarama="bagli"` kipi GERİ ALINDI

Hipoteze dayanarak bağlantılılık ölçütü yazdım: ışın boyunca eşik altı
aralıklardan **çekirdek desteğinden (`2h`) ince** olanları aşıp geç,
kalın olanı gerçek boşluk say. Sentetikte ölçtüm:

| senaryo | `distan` | `icten` | `bagli` |
|---|---|---|---|
| örtü yok | +0,9216 | +0,9216 | +0,9216 |
| örtü 30 m | ÖRTÜLÜ | +0,9216 | +0,9216 |
| iç boşluk 2,0 m | +1,0155 | +0,0000 | +0,0000 |
| iç boşluk 3,0 m | +3,9598 | YÜZEY_YOK | YÜZEY_YOK |

`bagli`, `icten`'den **hiçbir senaryoda farklı davranmıyor**. Ve §3'ten
sonra zaten çözemeyeceği belli: o da `φ`'nin anlamlı olduğunu
varsayıyor.

**Commit'lenmedi, geri alındı.** İşe yaramayan kod göndermektense
ölçüp kaldırmak doğrusu. Varsayılan `distan` ve `icten` olduğu gibi
duruyor (35/35 sınav geçiyor).

## 5. Krater ön kaydı MÜHÜRLENDİ

`ONKAYIT_HERA_KRATER_uretim66.json`, SHA-256
`1b3b811e260d86b2840361ec4fc0e1d4cbdaa4671e8353f04c8af68c27d67d42`.
Protokol HT (2026-09-14) + EK-1 (2026-10-28, öngörü hesaplanmadan
önce). 66/96 çapraz doğrulanmış nokta, koşul `POSTERIOR`, `20 000`
örnek, tohum `20260914`.

| gözlemli | q05 | q50 | q95 |
|---|---:|---:|---:|
| `V_krater` (m³) | **−46,3** | +34,1 | +504,0 |
| `d_merkez` (m) | −3,46 | +0,81 | +4,41 |

**Üç şerh kaydın gövdesinde**, ve kaydın değerinden önemli:

1. **Seçilim yanlılığı büyük ve ölçülü.** Kullanılan 66 noktanın `Y₀`
   ortancası `1 918` Pa, dışlanan 30'un `10,58` Pa, posteriorun kipi
   `18,7` Pa — vekil eğitim desteğinin **~2 dekad dışına** ekstrapole
   ediyor. Sebebi KAYIT-090: krater tam verinin işaret ettiği yerde
   okunamıyor.
2. **`V_krater` örnekleri negatife taşıyor** (`q05 = −46,3 m³`); hacim
   negatif olamaz. **Kırpılmadı** — kırpmak genişliği sahte biçimde
   daraltırdı. Oran kaydın içinde.
3. **HT §5 aynen geçerli:** bu *geçici* kraterdir, Hera *son* krateri
   ölçecek.

> Kayıt **dar değil geniş** ve bu bilinçli. İşlevi "Hera'nın krateri şu
> olacak" demek değil, **ne kadar bilmediğimizi Hera'dan önce
> kilitlemek**. Dar çıkması başarı değil hata işareti olurdu (EK-1 §3).

## 6. Geç dökümlü koşu GÖNDERİLDİ — 4 GPU

Kullanıcı 2026-11-01'de 4 GPU serbest bıraktı. İş `1639229_[0-3]`,
`kolyoz-cuda`, 1 GPU/görev, `--t-end 5000` (havuz: `600`).
Protokol [EK-2](../truba/PROTOKOL-HT-EK2-2026-11-01.md) **gönderimden
önce** yazıldı ve commit'lendi (`cb4a072`).

Dört nokta örtü yüksekliği aralığını kapsıyor ve posteriorun kipini
içeriyor: `16/96` (örtü `10,27` m), `20/96` (`30,89`), `84/96`
(`44,95`, `Y₀ = 18,57` Pa ≈ kip), `87/96` (`47,99`).

**Yargı önceden kilitli:** dört noktanın en az üçünde "ÖRTÜ AÇILDI"
çıkmazsa geç döküm yolu krater ön kaydı için yetersizdir ve bu yazılır.

### 6.1 `SABIT_COMMIT` sapması — denetlendi

Koşu `cb4a072` ile gidiyor, havuzun `SABIT_COMMIT`'i `d96c4ee`.
İki commit arasında değişen `src/` dosyaları sayıldı:
`anlik_plan.py`, `artik_korelasyonu.py`, `gozlemli_secimi.py`,
`ic_ice_tasarim.py`, `tarih_esleme.py`, `aday_gozlemliler.py`,
`beta_gelenegi.py`, `crater_shape.py` — **hepsi gözlemli ya da çıkarım
analizi**. `sim/`, `physics/`, `setup/`, `forward.py`'de **sıfır**
değişiklik. Yani geç dökümün fiziği havuzla **birebir aynı**; değişen
yalnız krateri okuma biçimi (ADR-0061/0062/0063), ki geç durumu
okuyabilmek için gereken tam da o.

Bu yüzden `is_GEC_DOKUM.slurm` `SABIT_COMMIT` eşitlik kapısını
**bilerek** koymuyor; kirli ağaç kapısı duruyor.

## 7. Kilitli yargılara etkisi — YOK

`krater_derinlik` ADR-0055 ile isteğe bağlı; posteriora girmiyor.
`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), mühürlü spin ön kaydı
(KAYIT-084) **etkilenmez**.
