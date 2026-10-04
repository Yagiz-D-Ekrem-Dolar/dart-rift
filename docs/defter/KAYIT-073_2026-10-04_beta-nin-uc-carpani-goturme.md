# KAYIT-073 — `β`'nın `Y₀`'ya duyarsızlığı bir **götürme**: üç güçlü etki birbirini siliyor (2026-10-04)

**Kapsam:** mevcut koşulardan ölçüm, **0 GPU-saat** ·
**Durum:** `β`'nın üç çarpanı ayrıştırıldı, toplam kuralı **tutuyor**,
çıkarım tasarımına doğrudan sonucu var ·
**Kaynak:** `W2_Y{1,10,50}_g1p0` durum `npz`'leri (KAYIT-067 koşuları),
`observables/ejekta_ayrismasi.py` ·
**Öncül:** [KAYIT-072](KAYIT-072_2026-10-04_DY2-model-gozleme-ulasiyor.md),
[ADR-0053](../adr/ADR-0053-y0-onseli-ve-tanimlayici-gozlemli.md) §3,
ADR-0051 §2c (`rank(F) ≤ gözlemli sayısı`)

---

## 1. Soru

ADR-0053 ölçtü: `β`, `Y₀`'ya çok zayıf bağlı (`b = β − 1 ∝ Y₀^(−0,076)`;
`1σ` için `Y₀`'da `×12,4` belirsizlik), ama `M_ejekta` **4,2 kat** daha dik
(`−0,321`). **Neden?** Aynı fiziğin iki ölçüsü, biri neden kör?

## 2. Ayrıştırma

Kaçan ejektanın çarpma ekseni boyunca taşıdığı momentum, tanım gereği üç
çarpanın ürünüdür:

    p_ejekta = M_kaçan · v_ort · kos_ort
    β − 1 = K · p_ejekta / p_mermi

- `M_kaçan`: kaçış hızını geçen hedef maddesinin kütlesi
- `v_ort`: o maddenin **kütle ağırlıklı** ortalama hızı
- `kos_ort`: hız yönünün eksenle kosinüsü, **momentum ağırlıklı**
- `K`: momentum defterinin `R` yüzeyi tanımı + bağlı kalıp hareket eden madde

Ölçülen (W2 kıyas sahnesi, `t_geçiş = 1,0 s`, `600 s`, **yalnız `Y₀`
değişiyor**):

| `Y₀` | `M_kaçan` | `v_ort` | `kos_ort` | `M·v·kos/p` | `β − 1` | oran |
|---|---|---|---|---|---|---|
| `1 Pa` | `5,373e7` | `0,3064` | `0,6152` | `2,8441` | `3,3889` | `0,8393` |
| `10 Pa` | `2,603e7` | `0,4831` | `0,7192` | `2,5401` | `3,0699` | `0,8274` |
| `50 Pa` | `1,521e7` | `0,6338` | `0,7714` | `2,0880` | `2,4938` | `0,8373` |

**Önçarpan sabit:** `K⁻¹ = 0,8347 ± 0,0052`; `Y₀` `1,7` dekad boyunca yalnız
`%1,4` değişiyor. Yani ayrıştırma bir yaklaştırma değil, neredeyse kimlik.

## 3. Sonuç: üsler toplanıyor

| büyüklük | `Y₀` üssü | yön |
|---|---|---|
| `M_kaçan` | **`−0,3221`** | dayanım artınca **çok daha az** madde kaçıyor |
| `v_ort` | **`+0,1866`** | ama kaçan **daha hızlı** |
| `kos_ort` | **`+0,0585`** | ve **daha toplu** |
| **toplam** | **`−0,0769`** | |
| `β − 1`'in kendi ölçülen üssü | **`−0,0760`** | |

Toplam, `β`'nın bağımsız ölçülmüş üssünü **`%1,3`** içinde veriyor.

> **`β`, `Y₀`'ya duyarsız değildir — üç GÜÇLÜ etkinin birbirini
> götürmesinden duyarsız GÖRÜNÜR.** Kütle `%32`/dekad düşerken hız `%19`
> ve toplanma `%6` artıyor; `β` geriye `%8`/dekad bırakıyor.

## 4. Fizik okuması

Daha güçlü matris, kazı akışını **daha erken** durduruyor: yavaş, geniş
açıyla saçılan malzeme artık kaçamıyor; kaçanlar yalnız çarpma noktasının
yakınındaki, **hızlı ve eksene yakın** fırlatılanlar oluyor. Yani dayanım
ejekta dağılımının **düşük hız / geniş açı** kuyruğunu kesiyor.

Bu, KAYIT-072 §3'ün şekil bulgusuyla aynı yöne bakıyor: `β` yerel ve
toplamsal bir **oran**; ejektanın *nasıl* dağıldığını bilgisini taşımıyor.
Orada şekil, burada dayanım — ikisinde de ayırt edici olan `β` değil,
ejektanın kendisi.

## 5. Çıkarıma sonucu (en önemli kısım)

ADR-0051 §2c'nin kuralı: **`k` gözlemliyle en çok `k` yön öğrenilir.** Bu
kayıt o kuralın *niçin* ısırdığını gösteriyor:

1. **`β` tek gözlemli olarak kullanmak, üç bağımsız bilgiyi ÇARPIP birini
   tutmaktır.** Üç çarpanın `Y₀` üsleri `−0,32 / +0,19 / +0,06`; `β`
   onların **toplamını** (`−0,077`) görüyor. Bilgi kaybı tasarımdan.
2. **`M_ejekta`'yı ikinci gözlemli yapmak çarpımı açmanın ilk adımı** ve
   ölçülmüş kazancı `6,3` kat (ADR-0053 §3). Bu kayıt sebebini veriyor:
   `M_kaçan` götürmeye katılmayan, en dik çarpan.
3. **Üçüncü gözlemli ejektanın YÖNELİMİ olmalı** (`kos_ort` ya da koni).
   `v_ort` ile `kos_ort` ayrı yön taşıyor ama `β` ve `M_ejekta`
   verildiğinde ikisinin **çarpımı** belirlenmiş olur: `v·kos = b·p/(K·M)`.
   Yani `(β, M_ejekta)` çifti üç çarpandan ikisini sabitliyor, üçüncüsü
   serbest kalıyor — ve o serbest yön **`A95` yüzünden** gözlemle
   karşılaştırılamıyor.

> **`A95` kozmetik bir tanı sorunu değil: çıkarımın üçüncü yönünü
> kapatıyor.** Koni açısı LICIACube anında (`~170 s`) **konumdan**
> ölçülüp gözlemle kıyaslanabilir hale gelmedikçe, `θ`'nın üç
> ekseninden en az biri önsel-baskın kalır. Ölçülen `kos_ort` `Y₀` ile
> `0,615 → 0,771` (`%25`) değişiyor; yani orada **gerçek bilgi var**,
> yalnız gözlem tarafı eksik.

## 6. Ne yapılmadı (dürüstlük)

- **`kos_ort` bir gözlemli olarak eklenmedi.** Model tarafı ölçülü ve
  temiz; ama DART karşılığı (LICIACube koni açısı) A95 yüzünden
  kıyaslanabilir değil. Gözlem tarafı olmadan posteriora sokmak
  "model-model kıyasını gözlem yerine koymak" olurdu.
- **Ayrıştırma yalnız `Y₀` ekseninde ölçüldü.** `α_b` ve `f` eksenlerinde
  üç çarpanın nasıl davrandığı **ölçülmedi** — götürmenin orada da olup
  olmadığı bilinmiyor. Havuz bunu verecek: `ejekta_bilesenleri` her
  koşuda hesaplanabilir (ek maliyet yok, son durumdan okunuyor).
- **Üç nokta ve kavis:** üsler `1–50 Pa` aralığından, log-log doğrusal
  uydurmayla. `%10` eşiğiyle kural tutuyor ama `p` küçük olduğu için
  `β`'nın üssü en gürültülü olan. PROTOKOL-DO'nun iki noktası (`500`,
  `5000 Pa`) bu ayrıştırmayı da **2,7 dekada** yayacak.
