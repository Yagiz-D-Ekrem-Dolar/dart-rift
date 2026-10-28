# PROTOKOL-HT EK-1 — krater ön kaydının **uygulanabilir** hâli

**Yazıldı:** 2026-10-28, **öngörü hesaplanmadan ÖNCE.**
**Ana protokol:** [PROTOKOL-HT](PROTOKOL-HT-HERA-TAHMIN.md) (2026-09-14) —
**değiştirilmedi, hiçbir satırı silinmedi.** Bu ek, ana protokolün
istediklerinden hangilerinin bugünkü ölçümlerle **karşılanabildiğini**,
hangilerinin **karşılanamadığını** ve niçin, önceden kaydeder.

**Betik:** `scripts/hera_krater_onkayit.py`
**Öncül ölçümler:** [KAYIT-090](../defter/KAYIT-090_2026-10-28_havuzda-krater-yeniden-okundu-ve-geri-alma-kapisi.md),
[KAYIT-091](../defter/KAYIT-091_2026-10-28_icten-disa-tarama-olculdu-66-nokta-capraz-dogrulandi.md),
[ADR-0062](../adr/ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md),
[ADR-0063](../adr/ADR-0063-yuzey-icten-disa-taranir.md)

---

## 1. Niçin bir ek gerekiyor

PROTOKOL-HT 2026-09-14'te, üretim havuzu koşmadan ve krater operatörünün
havuzdaki davranışı ölçülmeden yazıldı. O tarihten sonra üç şey ölçüldü:

1. Krater, havuzun bir bölümünde **okunamıyor** (KAYIT-090): `t = 600 s`'te
   zayıf matris rejiminde kaçmamış ejekta krateri örtüyor.
2. Okunabilir nokta sayısı ADR-0063 ile **46 → 66** çıktı ve bu 66'nın
   hepsi **iki bağımsız tanımla** doğrulandı (KAYIT-091).
3. `R_krater` 96 noktanın **2**'sinde sonlu.

Bu ek, bunların ön kayda nasıl yansıdığını **öngörüyü görmeden** yazar.
Veriyi gördükten sonra kapsamı daraltmak ön kayıt olmaz; sıranın kanıtı
bu belgenin commit tarihidir.

## 2. Hangi gözlenebilir mühürleniyor

PROTOKOL-HT §3: *"`R_krater` (m), `V_krater` (m³), `M_ejekta` (kg)"*.

| HT §3'ün istediği | karar | gerekçe (ölçülmüş) |
|---|---|---|
| `V_krater` | **MÜHÜRLENİR** | 66/96 noktada çapraz doğrulanmış |
| `R_krater` | **MÜHÜRLENMEZ** | 96 noktanın **2**'sinde sonlu (`4,0` ve `3,8` m). A11'in "gözlenemez" yargısı ayakta. Sayı yerine bu sayım kayda girer. |
| `M_ejekta` | **MÜHÜRLENMEZ** | İki sebep: (a) Hera'nın ölçeceği bir nicelik değil; (b) posteriorun **koşullandığı veri** (`M_EJEKTA_GOZ = 1,6e7 kg`). Kendi verisini öngörü diye mühürlemek döngüseldir. |
| **`d_merkez`** (ek) | **MÜHÜRLENİR** | HT §3'te yok; eklenir çünkü krater derinliği `V_krater`'den bağımsız bir yanlışlanabilir sayıdır ve aynı 66 noktada ölçülü. Ek olduğu kayda yazılır. |

> Kapsam **genişliyor değil daralıyor**: HT'nin üç isteğinden biri
> karşılanıyor, ikisi gerekçesiyle karşılanmıyor, bir tane ekleniyor.
> Hiçbiri "iyi çıkan"a göre seçilmedi — seçim ölçüm **sayılarına** göre
> ve öngörü hesaplanmadan yapıldı.

## 3. Hangi noktalar kullanılıyor

**Yalnız ADR-0063'ün çapraz doğruladığı 66 nokta.**
`docs/sonuclar/havuz_krater_tarama_96.csv`'de `capraz_dogrulandi`
sütunu `EVET_distan_ile` (46) ya da `EVET_60m_ile` (20) olanlar.

Dışarıda kalan 30 nokta ve sebepleri **kayda girer**:

- `HAYIR_tek_tani` (13): yalnız bir tanım ölçüyor; o tanım gövde
  içindeki boşluğa takılabiliyor (KAYIT-091 §7, idx 87'de `+36,49 m`).
- `olculmedi` (17): iki tanım da reddediyor (örtülü krater).

Bu, **seçilim yanlılığı taşır** ve bu da kayda yazılır: dışarıda kalan
30 noktanın `Y₀`'ı düşük tarafa yığılıyor. Vekil bu yüzden `Y₀`'ın
zayıf ucunda **ekstrapole** ediyor; öngörünün genişliği bunu yansıtmalı,
dar çıkması başarı değil **hata işareti**dir.

## 4. Vekil — GP, ikinci derece değil

HT §3 *"ikinci derece vekil"* diyor. Kullanılacak olan **GP**'dir
(ADR-0058'in kilitli tarifi: GP + ARD + θ-gruplu 4-kat + Bachoc
varyans kalibrasyonu). Gerekçe:

- ADR-0058 (2026-10-05) HT'den **sonra** yazıldı ve üretim zincirinin
  vekilini kilitledi.
- `β` ve `M_ejekta` GP ile, krater ikinci derece ile kurulsaydı iki
  öngörü **aynı ailede olmazdı** ve örnekleme tutarsız olurdu.

Sapma burada, öngörü hesaplanmadan yazıldı.

## 5. Ağırlık

HT §2: *"ÖNSEL İÇİNDE → posterior ağırlık"*. Koşul ölçüldü ve
**sağlanıyor**: tarih eşlemesinde model gözleme ulaşıyor
(`I_min = 0,325`, bağdaşır hacim `%34,04`; KAYIT-080). Dolayısıyla
kayıt **`POSTERIOR`** koşuluyla üretilir.

Posterior, `grid_posterior_hetero` ile ADR-0058 tarifinden; örnekler
posterior ağırlığıyla izgara düğümlerinden çekilir.

> **Not — HS'den bilerek farklı.** Spin ön kaydı (PROTOKOL-HS §4.2)
> eleme bölgesinden **düzgün** örnekledi, çünkü HS §6 posteriorun daha
> dar olduğunu söylüyordu ve dar olanı seçmek öngörüyü sahte biçimde
> keskinleştirirdi. HT §2 ise açıkça posterior ağırlığı istiyor. İki
> protokol farklı; **her biri kendi kuralıyla** koşuluyor. Farkın
> kendisi kayda yazılır ki karşılaştırmada karıştırılmasın.

## 6. Örnekleme

HT §3: `20 000` örnek, tohum **`20260914`**, kantiller
`q05, q16, q50, q84, q95` doğal birimde. **Aynen uygulanır.**

## 7. Koşullu eşleme (HS'deki gibi)

Mühürlü sayının yanına, Hera bir `V_krater` ölçerse `Y₀`'ın ne olacağı
tablosu da konur. Krater `Y₀`'a en duyarlı gözlenebilir (S7: `F = 1006`,
`ρ = −0,94`), dolayısıyla eşleme oradan kurulur.

## 8. Kaydın taşıması zorunlu uyarılar

1. **PROTOKOL-HT §5 aynen geçerli ve artık SAYILI.** Model krateri
   `t_end = 600 s`'deki **geçici** kraterdir; Hera **son** krateri
   (ejekta düştükten sonra) ölçecek. 2026-10-28 ölçümü: eksende kaçmamış
   ejekta `6,50 – 47,99` m yükseklikte, ortanca `30,89` m (KAYIT-090).
   Bu bir **mekanizma ön kaydıdır**, son krater öngörüsü değil.
2. **Seçilim yanlılığı** (§3): 30 nokta dışarıda ve `Y₀` düşük tarafa
   yığılı.
3. **`n_yön = 1`** (KAYIT-079): `α_b` ve `f` önselden ayırt edilemiyor;
   öngörü genişliğinin bir kısmı önselin genişliğidir.
4. **Çözünürlük yanlılığı** (KAYIT-085): ince koşu kaba koşudan 7/7
   noktada aynı yöne sapıyor, `Y₀`'da `×3,22`. Krater bundan muaf
   değildir ve bu kayıt yeniden üretilecekse **yeni etiketle** üretilir.
5. **Tek sabit sahne**; öngörü o sahneye koşulludur.

## 9. Mühür

`ONKAYIT_HERA_KRATER_<etiket>.json`: öngörü + meta (koşul, kapsam,
kullanılan/dışlanan nokta listesi, tohum, `t_end`, git commit, UTC) ve
gövdenin **SHA-256**'sı. Aynı adla ikinci kayıt **üzerine yazılmaz**.
Commit okunamazsa betik **durur** (künyesiz ön kayıt mühür sayılmaz).

## 10. Hera geldiğinde (kilitli)

HT §7 aynen: ölçülen değerin öngörü dağılımındaki kantili yazılır;
`q05`–`q95` dışında → **TUTARSIZ**, içinde → **TUTARLI**. §8'in
uyarıları yargının yanında yazılır.
