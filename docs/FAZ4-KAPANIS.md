# FAZ 4 — **KAPANIŞ** (2026-08-18)

> **FAZ 4 kapandı.** Kapı `G4` `2026-08-11`'de **10/10** geçti
> ([G4 kapı raporu](G4-KAPI-RAPORU.md), [KAYIT-048](defter/KAYIT-048_2026-08-11_G4-gecildi.md)).
> Bu belge kapanışı ilan eder, teslim edileni sayar ve **neyin
> bilerek ertelendiğini** yazar.

---

## 1. Kapı

| # | ölçüt | eşik | ölçülen | |
|---|---|---|---|---|
| A1 | mermi çapı / yerel aralık | `≥ 2` | `2,03906` | GEÇTİ |
| A2 | `r_ince / R_mermi` | `≥ 3` | `66,5573` | GEÇTİ |
| A3 | ek yerinde kütle sapması | — | `3,48e-4` | GEÇTİ |
| B1 | ardışık çözünürlükte `β` farkı | — | `8,43e-4` | GEÇTİ |
| B2 | `β` durulmuş | — | `1` | GEÇTİ |
| B3 | A′ ince kola yakın | — | `1` | GEÇTİ |
| B4 | enerji sapması eğimi | — | `−2,39e-3` | GEÇTİ |
| C1 | parametre kapsaması | — | `1` | GEÇTİ |
| C2 | en dar bant / önsel | `< 0,50` | `0,221` | GEÇTİ |
| C3 | gürültüyle genişleme | — | `1` | GEÇTİ |

---

## 2. Teslim edilen

| | |
|---|---|
| **İki aşamalı çözünürlük** (ADR-0043) | `λ₁ = 19` çekirdek → Lagrange'cı kabalaştırma → `λ₂ = 2`; üç seviyeli |
| **Parçacık başına `h`** (ADR-0041) | A′; beş seçenek ölçümle ikiye indi |
| **`Ω ≡ 1`** (ADR-0042) | cebirsel sonuç; sabit `h` yeterliliği küp **ve** DART'ta ölçüldü |
| **Kabalaştırma** | kütle/momentum/enerji `~1e-15`; `mermi_kesri` kesir olarak taşınır |
| **Çıkarım hattı** | tasarım → vekil (kapalı LOO `q2`) → ızgara posterior → G4-C |
| **Depo sağlığı** | CI dört ayrı job, araç zinciri sabit, `v0.4.0` yayında |

---

## 3. Kapının bedeli — **kapanışın parçası**

`C2`'yi geçiren şey eşik gevşetmesi **değil**: uzay üç parametreden
**bire** indirildi (ADR-0046 S1).

> **İddia daraldı:** *"iç yapıyı çıkardık"* → **"matris gözenekliliğini
> çıkardık"**. `f_boulder` artık serbest değil — ve Hera onu
> görüntüleyecek. Kapının geçmesi bu kaybı **telafi etmiyor**.

---

## 4. Bilerek ertelenen — ve neden meşru

`G4` motorun **yakınsadığını** ve **çıkarımın işlediğini** kanıtlar.
*Doğru* `β` ürettiğini kanıtlamaz; ikisi ayrı sorular ve ikincisi kapı
ölçütü **değildi**.

| | konu | neden ertelendi |
|---|---|---|
| [#6](https://github.com/Yagiz-D-Ekrem-Dolar/dart-rift/issues/6) | `β` merminin sekmesini ölçüyor (A17/A12) | Çözümü **ADR** gerektiriyor: ya gözlenebilirin tanımı (`d > 2R` kontrol yüzeyi) ya modelin ejekta üretimi değişmeli. Kapı ölçütlerinin hiçbiri buna bakmıyor. |
| [#7](https://github.com/Yagiz-D-Ekrem-Dolar/dart-rift/issues/7) | Krater çapı gözlenemiyor (A11) | `λ₂ = 2` ADR-0043'te **kilitli**; değişikliğin ensemble bütçesine doğrudan maliyeti var. Gözlenebilir derinliğe çevrilerek (ADR-0045) kapı zaten geçildi. |

A17 kapanışta **ölçülü** bırakılıyor, tahmin olarak değil:

| | ölçülen |
|---|---|
| kaçan **mermi** kütlesi | `579,40 kg` — merminin tamamı |
| kaçan **hedef** kütlesi | **`0,0000e+00 kg`** |
| **hedef payı** | **`0,0000`** |
| `β` (yalnız mermiden) | `1,4112` |

Elenen adaylar — hepsi ölçümle: koşu süresi (`0,2 → 600 s`, `3000×`),
mukavemet (`Y0` `1 → 2,15e6 Pa`, altı mertebe, rejim geçişinin
`6,14 Pa` iki yanı dahil), yerçekimi, gözeneklilik (`+%7,5`),
çözünürlük (`−%17`).

> Hepsi aynı yere çıkıyor ve orası **ADR-0028'de zaten yazılıydı**:
> kontrol yüzeyini geçen madde hedef ejektası değil merminin geri
> sekmesi.

---

## 5. FAZ 5 nereden başlar

1. **#6 bir ADR ile karara bağlanmalı.** `β`'nın gözlenebilir tanımı
   FAZ 5'in ensemble'ının **girdisi**; belirsiz bırakılırsa üretilen
   bütün posterior'lar aynı belirsizliği taşır.
2. **ADR-0046'nın daralttığı iddia** FAZ 5'in kapsamını belirler:
   şu an çıkarılan şey matris gözenekliliği, *iç yapı* değil.
3. Depo tarafı hazır: CI yeşil, sürüm etiketli, açıklar issue olarak
   görünür.

> Kapanış kuralı gereği: bu belge FAZ 4'ün **başarısını** ilan ederken
> eksiklerini gizlemiyor. `G4` geçti; `β`'nın doğruluğu geçmedi ve
> geçtiği iddia edilmiyor.
