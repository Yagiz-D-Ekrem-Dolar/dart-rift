# KAYIT-087 — `n_yön = 1` çözünürlük yanlılığına **dayanıklı**

**Tarih:** 2026-10-22 · **Sıfır GPU** · **KEŞİF, yargı değil**
**Betik:** `scripts/yanlilik_n_yon_duyarliligi.py`
**Öncül:** KAYIT-079 (`n_yön = 1`), KAYIT-085 (yanlılık), KAYIT-086

---

## 1. Soru

KAYIT-085 iç içe koşunun 7 noktasında `b_ince/b_kaba` oranının 7/7
aynı yönde olduğunu ölçtü (ortanca `%+23,3`). Bu kayma `n_yön = 1`
sonucunu bozar mı?

Soru ikiye ayrılır:

1. **Kayma sabit mi, `θ`'ya bağlı mı?** Sabitse Jakobyen satırı sabit
   bir çarpanla ölçeklenir: gradyan **yönleri değişmez**. `θ`'ya
   bağlıysa gradyanlar **döner**.
2. **Dönme yargıyı eşiğin üstüne taşır mı?**

## 2. Cevap 1: kayma pratikte **sabit**

`log r = a_0 + a\cdot u` modeli (7 nokta, 4 katsayı):

| katsayı | değer | se | `t` |
|---|---:|---:|---:|
| `a₀` (sabit) | +0,1137 | 0,1854 | +0,61 |
| `a₁` ($\alpha_b$) | +0,0093 | 0,1534 | **+0,06** |
| `a₂` ($\log Y_0$) | +0,0941 | 0,1922 | **+0,49** |
| `a₃` ($f$) | +0,1512 | 0,1801 | **+0,84** |

Artık sd `0,1311`. **Hiçbir eğim `|t| > 2` değil** — en büyüğü 0,84.
Yani 7 noktayla `θ`-bağımlılığına dair kanıt yok; kayma pratikte
çarpansal bir sabit.

> **Küçük örneklem uyarısı.** `|t| < 2` olması "eğim yok" demek değil,
> "7 noktayla ayırt edilemiyor" demektir. Standart hatalar
> katsayıların kendisinden büyük; bu model zayıftır ve öyle
> raporlanmaktadır.

## 3. Cevap 2: `n_yön` **değişmiyor**

Düzeltme bütün 96 noktaya uygulanıp Fisher yeniden hesaplandı. Kovaryans
**iki kolda da aynı** ve üretim tarifinden (gözlem hatası + ölçülmüş
model bütçesi).

| kol | `n_yön` (5 `θ` noktası) | ikinci öz değerler |
|---|---|---|
| kaba (üretim) | `1, 1, 1, 1, 1` | 0,57 · 8,64 · 0,65 · 0,62 · 0,78 |
| yanlılık düzeltilmiş | `1, 1, 1, 1, 1` | 3,69 · 10,54 · 3,84 · 4,87 · 0,18 |

Eşik **36**. Düzeltme ikinci öz değeri en çok `0,57 → 4,87`'ye
çıkarıyor; eşiğin hâlâ **7 kat** altında.

**`n_yön = 1` ayakta.**

## 4. Betikte düzeltilen kusur

İlk koşumda Fisher kovaryansı veri saçılmasından (`b.std()`)
kurulmuştu. İki hatası vardı:

- mutlak `n_yön` anlamsız çıkıyordu (kilitli ölçüm `1` iken `0`),
  çünkü veri saçılması gerçek ölçüm belirsizliğinden çok büyük;
- `b` iki kolda farklı olduğu için kovaryans da farklıydı — yani
  karşılaştırma elma-armut oluyordu.

Düzeltildikten sonra kaba kolun `n_yön`'ü kilitli ölçümle (`1`)
örtüşüyor; bu, betiğin kendi doğrulamasıdır.

## 5. Ne iddia edilmiyor

- **Bu bir düzeltme değil.** ADR-0059 kapısı 1. maddeden düştü
  (12 nokta istiyordu, 7 var); düzeltilmiş `b` yayımlanabilir bir
  sonuç değildir, yalnız dayanıklılık sınavının aracıdır.
- **`Y₀`'ın mutlak değeri hâlâ belirlenemiyor.** Bu kayıt yalnız
  *kaç yön* sorusunun cevabının dayanıklı olduğunu gösterir; *o yönün
  nerede olduğu* sorusunun cevabı KAYIT-085'teki gibi açıktır.
- **7 nokta azdır.** Kalan 5 nokta koşulursa bu sınav yinelenmeli.
