# Protokol G — gözlenebilir iç yapıyı ayırt ediyor mu

**Yazıldı:** 2026-09-06, **koşudan önce** · **Dayanak:** rapor A46

---

## Bu sınav bugüne kadar **hiç geçerli yapılmadı**

A46: sürücü `sahne_taban=None` gönderiyordu, `build_scene`
varsayılanı `M0`, ve `M0` dalında blok yerleştirilmiyor. Yani
`θ = (boulder_α₀, matrix_Y₀, f_boulder)` üçlüsünün **iki bileşeni**
sahneye hiç ulaşmıyordu.

Ölçüldü: `(1,05; 1e4; 0,10)` ve `(1,30; 1e4; 0,40)` noktaları
**birebir aynı** `x, m, α₀, Y₀` üretiyordu.

Dolayısıyla depoda *"gözlenebilir iç yapıyı ayırt edemiyor"*
diye bir **bulgu yok**. Yalnız bozuk bir düzenek vardı.

## Tasarım

| | değer |
|---|---|
| nokta sayısı | `24` (LHS) |
| **tekrar** | aynı `24` nokta, **ikinci `root_seed`** ile |
| çözünürlük | kaba merdiven (`N ≈ 17 201`, ölçülen `5` dk/nokta) |
| `α_av` | **F kampanyasının kazananı** |
| `t_end` | `0,024 s` |

### Gürültü tabanı neden ikinci tohum

`root_seed` blok **yerleşimini** ve hasar tohumlamasını belirliyor.
Aynı `θ`, farklı tohum = **aynı fiziğin farklı gerçeklemesi**.

Bu, gözlenebilirin `θ` hakkında bilgi taşıyıp taşımadığını sormanın
doğru yolu: `θ`'lar arası değişim, **aynı `θ`'nın gerçeklemeleri
arası** değişimden büyük mü?

Üç noktalı Richardson `σ_num` A52 yüzünden yapılamıyor; **gerçekleme
gürültüsü** onun yerine geçmiyor ama kendi başına anlamlı ve
**ölçülebilir** bir taban.

## Ölçülen

Her nokta için `Δβ_hedef`, `M_ejekta`, `⟨v⟩`.

```
S_theta  = Var( ortalama_tohum(y | theta) )      # theta'lar arasi
S_gurultu = ortalama_theta( Var_tohum(y | theta) ) # gerceklemeler arasi
F = S_theta / S_gurultu
```

## Yargı — **şimdi kilitleniyor**

| gözlenen | sonuç |
|---|---|
| `F > 4` **ve** en az bir `θ` bileşeniyle Spearman `\|ρ\| > 0,5` (`p < 0,05`) | **AYIRT EDİYOR.** Gözlenebilir iç yapı hakkında bilgi taşıyor. Bilimsel sonuç budur. |
| `F > 4` ama hiçbir bileşenle anlamlı korelasyon yok | Bilgi **var** ama tek eksene inmiyor; bileşik parametre aranır. |
| `1 < F ≤ 4` | **Zayıf**. Bildirilir, ama çıkarım kurulmaz. |
| `F ≤ 1` | **AYIRT ETMİYOR.** Ve bu, düzeltilmiş düzenekle alınmış ilk geçerli ölçüm olur. |

### Ön koşullar — biri düşerse sonuç okunmaz

1. `n_kacan_hedef ≥ 1` olan nokta oranı `≥ %80`. Aksi hâlde
   gözlenebilir çoğu noktada **var olmuyor** demektir ve varyans
   oranı anlamsızdır.
2. Her noktada defter kapalı (`\|artık_bağıl\| < 1e-10`).
3. Her noktada şok yargısı `KISMI` veya `SOK_VAR` (ADR-0049).
4. Sahne gerçekten `M1`: her koşu `alpha0`'ında **üç** benzersiz
   değer taşımalı (mermi, matris, blok). İki tanesi varsa A46
   geri gelmiş demektir — **koşu geçersiz**.

## Maliyet

`48` koşu × `5` dk = `4` saat tek GPU; `6` GPU'da **`~40` dakika**.

## Bu sınav neyi kanıtlamaz

Yakınsamayı kanıtlamaz. Kaba çözünürlükte alınmış bir sonuçtur ve
`R` kampanyası o çözünürlükte gözlenebilirin üretim AV'sinde
**var olmadığını** gösterdi. Bu yüzden F kampanyasının kazanan
ayarı şart: gözlenebilir önce **var olmalı**.

Sonuç, *"düzeltilmiş düzenekte ve akışın var olduğu ayarda,
gözlenebilir `θ` hakkında bilgi taşıyor mu"* sorusunun yanıtıdır.
Daha fazlası değil — ve daha azı da değil.

---

## Ek: `β` var olmazsa — **krater derinliği** (2026-09-06, koşudan önce)

`Rb_R1` (`N = 17 201`, üretim AV'si) ölçtü: `n_kacan_hedef = 0`.
Yani `β` o çözünürlükte **var olmuyor**. Ön koşul 1 düşer ve G
okunamaz.

Krater derinliği ise aynı koşuda **`0,533 m`** ile **var**. Ve
Hera'nın doğrudan görüntüleyeceği nicelik odur.

### Kural

F kampanyası `F_kaba_av01` kolunda `n_kacan_hedef = 0` verirse
G, `--nicelik krater_derinlik` ile koşar. O hâlde:

- **`n_kacan` ön koşulu uygulanmaz** (rapor: `UYGULANMADI`);
  krater `β`'dan bağımsız bir gözlenebilirdir.
- Diğer üç ön koşul **aynen** geçerli (defter, şok, `M1` nöbetçisi).
- `F` ve Spearman eşikleri **değişmez** (`4`, `0,5`, `0,05`).

### Bu bir gevşetme değil

Gözlenebilir **değişiyor**, ölçüt değil. `β` üzerine bir iddia
kurulmuyor; kurulan iddia *"krater derinliği `θ` hakkında bilgi
taşıyor mu"* oluyor — ve o soru kendi başına anlamlı, çünkü Hera
krateri ölçecek.

`x_reference` **zorunlu** (R4): verilmezse `crater_profile` cismi
küre varsayar ve **şekli** krater diye ölçer. Verilmezse `nan`
döner — sessiz sayı üretilmiyor.
