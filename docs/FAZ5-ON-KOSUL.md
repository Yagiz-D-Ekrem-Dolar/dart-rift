# FAZ 5 ön koşulu — model gözlemi **üretebiliyor mu?**

> Bu belge FAZ 5'e geçmeden **önce** yazıldı ve ölçütü veriye
> bakılmadan sabitliyor.

---

## 1. Sorun: gözlem modelin aralığının **dışında**

Deponun kendi kaydından (`period_interface.py`, Cheng ve diğerleri 2023):

| | |
|---|---|
| ölçülen periyot değişimi | `−33,0 ± 1,0` dakika |
| ondan türetilen `β` | **`3,2225`** |
| yayımlanan `β` | `3,6` |

FAZ 4.12 ensemble'ı (40 nokta, tüm önsel kutusu):

| | |
|---|---|
| model `β` aralığı | **`1,410 – 1,438`** |

**Gözlem, modelin ürettiği her şeyin `2,2`–`2,5` katı.** Hiçbir parametre
birleşimi veriyi üretmiyor.

> Bu hâliyle FAZ 5'in posterior'u **kutunun kenarına çakılır** ve
> raporlayacağı "kısıt" verinin değil **kutunun** özelliği olur.
> 300 noktalık ensemble koşturmak bunu değiştirmez.

---

## 2. Eksik olan **ne kadar** — sayıyla

`β = 1 + |p_ejekta · ê| / p_mermi`:

| | `p_ejekta` |
|---|---|
| gözlem (`3,2225`) | `7,913e6 kg m/s` |
| model (`1,4112`) | `1,464e6` |
| **eksik** | **`6,449e6`** = merminin **`1,81` katı** |

Bunu taşıyacak hedef kütlesi:

| ejekta hızı | gereken kütle | hedefin kesri |
|---|---|---|
| 0,5 m/s | `1,29e7 kg` | `%0,31` |
| **1 m/s** | **`6,45e6 kg`** | **`%0,15`** |
| 3 m/s | `2,15e6 kg` | `%0,05` |

---

## 3. Fizik **orada** — sayamıyoruz

`t = 20 s` koşusunda:

| | |
|---|---|
| kaçmış sayılan kütle | `579,4 kg` = **merminin kendisi** |
| hedef ejektası | `0 – 91,3 kg` (dokuz köşe) |
| **bekleyen** madde (içeride, dışarı, `v_r > v_kaçış`) | `2786` parçacık `≈ %26` |
| bekleyenin kaba momentumu | `4,2e8` = **gerekenin `65` katı** |

> Model **bol bol** dışarı giden madde üretiyor. Sorun sayma
> ölçütünde: madde yüzeyi geçmeden ejekta sayılmıyor ve geçiş süresi
> medyan **`57–75 s`**. `20 s`'lik koşu bunu göremez.

Bekleyeni doğrudan saymak **savunulamaz**: `bekleyen_profili` ölçtü ki
o madde çarpma noktasında **seyrek**, uzakta **yoğun** — yani kazı
değil cismin **çınlaması** (rapor A16 sonrası ölçüm).

---

## 4. Ön koşul koşusu — `t_end = 200 s`

Tek nokta, nominal parametreler, geçiş süresinin **~3 katı**
(iş `1494664`).

### Ölçüt — **veriye bakılmadan** yazıldı

| gözlenen | sonuç |
|---|---|
| `β > 2,5` | model gözlemi **üretebiliyor** → FAZ 5 bir **maliyet** sorusu |
| `β < 1,8` **ve** durulmuş | **model-form** sorunu → FAZ 5'in iddiası değişmeli |
| arası | belirsiz → daha uzun koşu |

Yan şart: `n_hedef_ejekta` `32`'yi **belirgin biçimde** aşmalı. Aşmıyorsa
sorun süre değildir ve yukarıdaki ölçüt uygulanmaz.

### Maliyet — ölçüldü, tahmin değil

H100'de `t = 20 s` `≈ 25 dk` sürdü, yani `t = 200 s ≈ 4 saat`.

| senaryo | süre |
|---|---|
| `t_end = 0,2 s`, 300 nokta | **2,75 saat** |
| `t_end = 200 s`, 300 nokta | **~50 GPU-günü** |

ADR-0004 *"300 koşu × 10 s → 300 GPU-günü"* diyordu; ölçülen değer
`t = 200 s` için `~50` gün. Fark H100 ve iki aşamalı şemadan geliyor.

> Yani FAZ 5'in maliyeti **ön koşul koşusunun sonucuna** bağlı:
> `β` çıkıyorsa uzun koşu **zorunlu** ve fatura `~50` gün; çıkmıyorsa
> uzun koşmak da işe yaramaz ve iddia değişmeli.

---

## 5. Bu belge neden şimdi yazıldı

Ölçütü sonuçtan **sonra** yazmak, hangi cevap gelirse gelsin onu
"beklenen" göstermeye izin verir. `β = 2,0` çıkarsa bu belge
*"belirsiz"* der ve daha uzun koşu ister — sonradan yazsaydım
`2,0`'ı "yaklaşıyor" diye okumak çok kolay olurdu.
