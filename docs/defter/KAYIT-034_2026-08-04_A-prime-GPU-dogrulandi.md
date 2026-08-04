# KAYIT-034 — A′ GPU'da **doğrulandı** (2026-08-04)

**Kapsam:** FAZ 4.3 · **Durum:** ölçüldü — üç sınav da temiz
**Öncül:** [ADR-0041](../adr/ADR-0041-yerel-incelme-yaklasimi.md) (kilitli),
[KAYIT-033](KAYIT-033_2026-08-04_A-prime-3-ince-bolge-orani-belirleyici.md)

---

## 0. Neden ayrı bir hızlı sınav

A′'nın GPU tarafı `c7eebea`'te yazıldı ve commit mesajına şu yazıldı:

> "YERELDE GPU YOK — bu degisiklikler burada KOSULAMADI. S9'un dersi geregi
> 'atlanan test gecti degildir'."

Tam doğrulama ~1,5 saat. Ama A′'nın **çekirdek** iddiaları üç ölçümle
dakikalar içinde sınanabilir. Uzun koşuyu beklerken yanlış bir taban
üstüne inşa etmemek için önce bunlar koşuldu.

---

## 1. Üç sınav ve neden bunlar

| # | sınav | hangi kusuru yakalar | nereden biliyoruz |
|---|---|---|---|
| 1 | skaler `h` vs **tekdüze dizi** `h` **bit aynı** | `h_ij = ½(h+h)` yuvarlamayı değiştiriyorsa | ilk K21 düzeltmem `1e-14` fark üretmişti |
| 2 | değişken `h`'de `Σ mᵢaᵢ = 0` **tam** | bir çift büyüklüğü hâlâ **asimetrik** `h` kullanıyorsa | CPU'da yapay viskozitede yakalandı: net/ölçek **4,0e5** |
| 3 | değişken `h`'de **CPU = GPU** | portun sessiz sapması | K1'in kök nedeni tam bu boşluğun **yokluğuydu** |

---

## 2. Ölçüm (job 1451544, kolyoz-cuda, H100)

`N = 343`, `h₀ = 1,3·s`, Tillotson + mukavemet açık, `h` yayılımı
`[0,7891, 2,0725]`:

| # | sınav | sonuç |
|---|---|---|
| 1 | BİT UYUMU (skaler vs tekdüze dizi) | **True** — `P`, `cs`, `a`, `rho` dördü de `array_equal` |
| 2 | MOMENTUM (değişken `h`) | **8,608e-17** — TAM |
| 3 | CPU-GPU ÇAPRAZ (değişken `h`) | **True** — `P`, `cs`, `a` hepsi `< 1e-10` göreli |

> **Üçü de temiz.** ADR-0041 §5b'nin dört maddeli sözleşmesinden üçü
> (simetrik `h_ij`, CPU referansı + çapraz kontrol, skaler yolun bit
> korunması) GPU'da **ölçülerek** doğrulandı.

### Sınav 2 neden bu kadar keskin

Momentum kalıntısı `8,6e-17` — çift duyarlıklı toplamanın gürültü tabanı.
Bu bir "küçük" değil, **tam** sonuçtur: `f_ij = −f_ji` cebirsel olarak
sağlanıyor, dolayısıyla toplam yalnızca yuvarlama sırasından sapıyor.
Bir tek çift büyüklüğü asimetrik `h` kullansaydı CPU'daki gibi `1e5`
mertebesinde bir kalıntı çıkardı.

---

## 3. Tam takım (job 1451542, aynı commit)

| aşama | sonuç |
|---|---|
| katı/yoğunluk/hasar/zaman-adımı **CUDA çapraz kontrolü** | **15/15 geçti** |
| tam test takımı | koşuyor (bu kayıt yazılırken) |

CUDA çapraz kontrollerinin geçmesi, §2'deki sınav 3'ü bağımsız bir kod
yolundan **ikinci kez** doğruluyor: o testler skaler `h` ile koşuyor ve
dizi dönüşümünden sonra da bit uyumlu kalmışlar.

---

## 4. Ne doğrulanmadı

Dürüstlük gereği ayrı yazılıyor:

| madde | durum |
|---|---|
| `Ω` (grad-h) düzeltmesinin GPU'da uygulanması | **henüz yok** — ADR-0041 §5b madde 2 açık |
| mukavemet/porozite/hasar ile etkileşim | **ölçülmedi** — ADR-0041 §5 boşluk 3 |
| DART kurulumunda çözünürlük yakınsaması | FAZ 4.4 |

> Sınav 1–3, `h`'nin **taşınmasının** doğru olduğunu gösteriyor. `Ω`'nın
> **fiziğinin** doğru olduğunu göstermiyor — o ayrı bir ölçüm.

---

## 5. Sırada

| # | iş | neden |
|---|---|---|
| 4.3b | `Ω` (grad-h) GPU'da | ADR-0041 §5b madde 2 |
| 4.4 | DART kurulumunda çözünürlük yakınsaması | boşluk 3'ü de kapatır |

---

## 6. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| "atlanan test geçti değildir" (S9) | §0 — GPU'suz yerelde yazılan kod TRUBA'da koşuldu |
| uzun koşuyu beklerken **çekirdek iddia** ayrıca sınanır | §0, §1 |
| her sınav **bilinen bir kusura** bağlanır | §1 — üçü de gerçek olaylardan |
| doğrulanmayan **ayrıca** yazılır | §4 |
