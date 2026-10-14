# ADR-0060 — `β` hangi doğrultuya izdüşürülür: gözlemle **aynı** gelenek

**Tarih:** 2026-10-14 · **Durum:** ÖNERİ → karar kullanıcıya
**Öncül:** KAYIT-078 §6, PROTOKOL-SI §3, ADR-0054 (gözlem hedefi)

---

## 1. Sorun

Benzetimimiz `β`'yı **çarpıcı momentumu** doğrultusuna izdüşürüyor:

    b_bizim = Σ m (−v⃗ · ê_U) / p,      p = m_mermi · v_mermi

Gözlenen değer ise öyle tanımlanmamış. **Cheng ve ark. (2023)**,
[arXiv:2303.03464](https://arxiv.org/abs/2303.03464), Denklem (1):

    M Δv⃗ = m U⃗ + m (β − 1) (Ê · U⃗) Ê

ve makalenin kendi ifadesi: *"β, aktarılan momentumun çarpıcı
momentumuna oranıdır, **net fırlatı momentumu doğrultusunda**."* Ayrıca
açıkça seçim gerekçesi veriliyor: *"önceki çalışmalar yüzey normali
doğrultusunu kullanmıştı; biz bunun yerine fırlatı doğrultusunu
seçtik ki sonuç yüzey topografyasından bağımsız olsun."*

**Along-track yön `ê_T` `β`'nın tanımı değildir.** `Δv⃗`'nin tamamı
ölçülemediği için Denklem (1), ölçülebilen bileşeni veren `ê_T` ile
skaler çarpılır; Denklem (2) bunun sonucudur. Referans yön hâlâ `Ê`.

Zincir doğrulandı: Cheng `β = 3,61 (+0,19 / −0,25)` veriyor (nominal
yoğunluk `2400 kg/m³`); ADR-0054'ün `β_göz = 3,5418 (+0,188 / −0,247)`
değeri bunun sahne kütlesine göre düzeltilmişidir — belirsizlikler
birebir örtüşüyor. Yani **karşılaştırdığımız sayı `Ê` geleneğinde.**

Üç gelenek:

| gelenek | referans | kim |
|---|---|---|
| yüzey normali | yüzey normali | eski çalışmalar |
| **fırlatı doğrultusu `Ê`** | net fırlatı momentumu | **Cheng 2023 → `β_göz`** |
| çarpıcı doğrultusu `ê_U` | mermi momentumu | **bizim koşularımız** |

## 2. Fark ne kadar — ÖLÇÜLDÜ

`P⃗ = Σ m v⃗` (kaçan hedef maddesi), `Ê = P⃗/|P⃗|`, `θ = ∠(Ê, ê_U)`:

    b_bizim = |P⃗| |cos θ| / p
    b_Cheng = |P⃗| / (p |cos θ|)
    ⟹  b_Cheng = b_bizim / cos²θ

88 koşuda sayıyla doğrulandı, azami sapma `4,0×10⁻¹⁵`.

| büyüklük | değer (88 nokta) |
|---|---|
| `θ` | `14,1° .. 27,7°` |
| `b_Cheng / b_bizim` | ortanca **`1,166`**, aralık `1,063 .. 1,275` |

Bu `0,166`'lık bağıl fark, `σ_model`'in (`0,065`) **iki katından fazla**
ve gözlemin kendi `1σ`'sından (`0,074–0,097`) büyük.

## 3. Karar (öneri)

**Posterior karşılaştırması `Ê` geleneğinde yapılır.** Vekile giren
model değeri, her koşu için kendi fırlatı alanından hesaplanan
`b_Cheng = b_bizim / cos²θ` olur.

`b_bizim` **silinmez**: yan yana raporlanır ve geçmiş bütün yargılar
(DY2, DO, DC, DN, KAYIT-076 dâhil) onunla hesaplandığı için **olduğu
gibi durur** (kural 5/6).

## 4. Bu neden eşik ayarlamak DEĞİL

Projenin tek maddelik sözü, kuralı sonuca göre ayarlamamaktır. Bu karar
onu bozmuyor, çünkü:

1. **Eşik getirmiyor.** `cos²θ` seçilen bir sayı değil; her koşunun
   kendi verisinden hesaplanıyor. Ayarlanacak serbestlik yok.
2. **Tanımsal bir düzeltme.** İki *farklı büyüklüğü* karşılaştırıyorduk;
   bu bir birim dönüşümü gibidir. Düzeltmemek, hatayı bilerek bırakmak
   olurdu.
3. **Yönü önceden belli.** `|cos θ| < 1` olduğundan düzeltme `b`'yi
   **daima büyütür**; sonucu "istediğimiz yere" çekme imkânı yok.

> ### ⚠ Tam ifşa
>
> Bu kararı yazmadan **önce** farkın büyüklüğünü ölçtüm (`1,166`).
> Yani karar tam anlamıyla kör değildir. Saklamak yerine yazıyorum:
> kararın gerekçesi büyüklük değil, **tanım uyuşmazlığıdır**; aynı
> uyuşmazlık `1,001` çıksaydı da düzeltme yine doğru olurdu, sadece
> önemsiz olurdu.

## 5. Neyi ÇÖZMÜYOR

* `Ê`'nin **yönü** bizim sahnemizin `600 s`'deki fırlatı alanından
  geliyor; Cheng'inki Hubble/LICIACube'dan kestirilmiş. Burada
  düzeltilen yalnız **gelenek** farkıdır, yön doğruluğu değil. Yön
  hatası ayrı bir terimdir ve ölçülmemiştir.
* PROTOKOL-SI §3'ün `σ_yon` eşikleri `ê_yörünge` için yazılmıştı ve
  **farklı bir büyüklüğe** aittir; bu ADR onlara dokunmaz.
* Geçmiş kilitli yargılar yeniden hesaplanmaz.

## 6. Reddedilen seçenekler

* **Düzeltmemek.** İki farklı büyüklüğü karşılaştırmak demek; `%17`
  sistematik, bütçenin en büyük üçüncü terimi olurdu ve `σ_model`'e
  gizlenemez (o bir saçılma, bu bir kayma).
* **`β_göz`'ü bizim geleneğe çevirmek.** Matematiksel olarak denk ama
  `Ê`'yi gözlemden değil modelden alırdı; gözlem hedefini modele
  bağımlı kılmak yanlış yöndür.
* **Yeni bir `σ` terimi eklemek.** Kayma varyansla soğurulmaz —
  ADR-0059'un kaba→orta `%−13` kayması için verdiği gerekçenin aynısı.
