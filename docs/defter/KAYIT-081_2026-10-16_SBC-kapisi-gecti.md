# KAYIT-081 — SBC kapısı **GEÇTİ**: posterior yayımlanabilir

**Tarih:** 2026-10-16 · `n_sbc = 200`, tohum `20261016`, `n_grid = 60`
**Koşucu:** `scripts/up_sbc_kapisi.py` ·
**Çıktı:** [`docs/sonuclar/UP_sbc.json`](../sonuclar/UP_sbc.json)
**Öncül:** [PROTOKOL-HAVUZ](../truba/PROTOKOL-HAVUZ-URETIM.md) §6,
KAYIT-079, KAYIT-080


> ## ⚠ NOT — 2026-10-16 akşam
>
> Bu SBC koşumu hatalı `kos` sütunlu girdiyle yapıldı
> ([KAYIT-082](KAYIT-082_2026-10-16_kos-hatasi-ve-duzeltilmis-sonuclar.md)).
> Düzeltilmiş girdiyle **yeniden koşuldu** ve yargı **değişmedi**:
> üç eksen de `KALİBRE` (`p = 0,868 / 0,074 / 0,299`,
> kapsama `0,645 / 0,650 / 0,680`). Aşağıdaki sayılar eski koşuma
> aittir ve kayıt olarak durur.

---

## 1. Sonuç

| eksen | tanı | PIT ort. (se 0,0204) | KS `p` | kapsama68 |
|---|---|---:|---:|---:|
| `α_b` | **KALİBRE** | 0,5050 | 0,9714 | 0,675 |
| `Y₀` | **KALİBRE** | 0,4682 | 0,1794 | 0,675 |
| `f` | **KALİBRE** | 0,5394 | 0,0690 | 0,675 |

**GENEL: KALİBRE** → PROTOKOL-HAVUZ §6 tablosunun ilk satırı:
**posterior yayımlanır.**

Üç eksende de kapsama `0,675`, nominal `0,68`'in pratikte üstünde
değil altında değil. PLAN-90-GÜN'de `~%25` yazılı olan "SBC düşer"
riski **gerçekleşmedi**.

## 2. Ama iki eksen sınıra yakın — saklanmıyor

- **`f`: KS `p = 0,0690`**, eşik `0,05`. Geçti ama en zayıf eksen.
  `p` eşiğin `1,4` katı; `n_sbc`'yi büyütmek bu sayıyı ya
  sağlamlaştırır ya düşürür.
- **`Y₀`: PIT ortalaması `0,4682`**, beklenen `0,5`. Sapma `0,0318`,
  yanlılık eşiği `2·se = 0,0408`. Yani `1,56σ` — yanlı sayılmadı ama
  sıfırdan uzak.

İkisi de kuralın içinde kaldı ve kural değiştirilmedi. Yine de
`n_sbc` büyütülürse bu iki sayının nereye gittiği izlenmeli.

## 3. Bu geçiş neyi kanıtlar, neyi kanıtlamaz

**Kanıtlar:** çıkarım makinesi — vekil + ölçülmüş `R` + `σ` +
ızgara posterioru — kendi varsayımları altında **kalibre**. Yani
posterior "%68" dediğinde gerçekten %68 kapsıyor. Bu, P-v4b'de bir
kez düşmüş olan sınav (A82, aşırı güvenli GP); θ-gruplu ÇD + Bachoc
düzeltmesinden sonra ayakta.

**Kanıtlamaz:** modelin **doğru** olduğunu. SBC, veriyi çıkarımın
kendi modelinden üretir; sorduğu soru *"model doğruysa posterior
kalibre mi"*. Modelin gerçeğe uyup uymadığı ayrı bir soru ve onun
cevabı KAYIT-080'de: tarih eşlemesi `I_min = 0,504` ile **model
gözleme ulaşıyor**, ama posterior bağdaşır bölgeden 14,8 kat dar
(**POSTERIOR DAR**).

İkisi birlikte okunmalı: *posterior kendi içinde tutarlı ve kalibre,
ama taşıdığı Gauss/köşegen varsayımı onu olduğundan emin gösteriyor.*
Ana sonuç hâlâ eleme bölgesi; SBC'nin geçmesi posteriorun **yanında**
yayımlanabilmesini sağlıyor.

## 4. Yöntem notu — ızgaraya tutturma

`uret(x, rng)` gerçek `θ`'yı en yakın ızgara düğümüne tutturup veriyi
oradan üretiyor; PIT ise **gerçek** `x`'e karşı hesaplanıyor. Aradaki
alt-ızgara farkı (`n_grid = 60`, birim adım `≈ 0,017`) küçük bir
uyuşmazlık katıyor. Etkisi PIT'i hafifçe **genişletmek** yönünde,
yani muhafazakâr tarafta; kapsamaların `0,675` çıkması bunun maddi
olmadığını gösteriyor. Yine de kayda geçiyor.

## 5. Ne değişmedi

`n_sbc ≥ 200`, KS eşiği `0,05`, `2·se` yanlılık bandı, §6 karar
tablosu — dördü de önceden kilitliydi. **Paydaya dokunulmadı**
(A115 (c)3: paydayı büyütüp geçmek yasak).

## 6. Sıradaki

Posterior artık koşabilir ve yayımlanabilir. Etiketleri belli:

- başlık `n_yön = 1` parametreli (KAYIT-079)
- "olabilirlik varsayımına koşullu", ana sonuç eleme bölgesi (KAYIT-080)
- üç önselin tablosu zorunlu ek (KAYIT-080)
- SBC kalibre (bu kayıt)
