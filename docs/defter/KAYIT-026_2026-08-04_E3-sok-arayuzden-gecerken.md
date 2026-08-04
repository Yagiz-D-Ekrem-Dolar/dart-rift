# KAYIT-026 — E3: şok arayüzden geçerken ne oluyor? (2026-08-04)

**Kapsam:** FAZ 4.1-E3 · **Durum:** ölçüldü — **arayüz zararsız**
**Öncül:** [KAYIT-020](KAYIT-020_2026-08-04_arayuz-hatasi-nicel.md),
[KAYIT-022](KAYIT-022_2026-08-04_E1-E2-karar-verisi.md) §6

---

## 0. Neden bu ölçüm son sırada bekliyordu

KAYIT-020, 022, 024'teki **her** ölçüm **yumuşak** bir basınç alanında
yapıldı. Çarpma probleminin asıl sorusu ise arayüzden geçen **şoktur** ve
yumuşak alandan ona geçiş **çıkarım değil, varsayım** olurdu.

---

## 1. Tasarım — üç kol, **aynı** global `h`

KAYIT-023 ölçtü ki sabit `h`'de sonuç bir platoya oturur ve platoyu `h`
belirler. Öyleyse `h`'yi **sabit** tutup yalnızca **parçacık dağılımını**
değiştirirsek, arayüz zararsızsa üç kol da aynı cevabı vermelidir:

| kol | dağılım |
|---|---|
| **a** | tek popülasyon, **kaba** |
| **b** | **iki bölgeli** (`r < 0,15` ince, dışı kaba; kütle oranı **8:1**) |
| **c** | tek popülasyon, **ince** |

Ölçülen büyüklük Sedov şok yarıçapıdır. **Tam çözümle kıyaslanmaz** —
ADR-0011 ölçtü ki bu kurulumda %3,9'luk bir **model-form tabanı** vardır.
Kollar **birbirleriyle** kıyaslanır.

### Üç ön koşul, hepsi denetleniyor

Biri bile sağlanmazsa yargı `inconclusive` döner — sessizce sonuç verilmez:

1. **Kollar ayırt edilebilir mi?** (`a` ile `c` farklı olmalı; aynılarsa
   `b`'nin "aralarında" olması **boş bir doğrudur**)
2. **Enjekte enerji üç kolda aynı mı?** (farklıysa **farklı problem**
   çözülmüş olur — ADR-0011'in tam olarak yakaladığı hata)
3. **Kütle uyuşmazlığı ihmal edilebilir mi?** (küre sınırı iki kafesle
   döşenemez; `r ~ (E/ρ)^{1/5}` olduğu için etkisi beşte biridir)

---

## 2. Ölçüm (TRUBA H200, iş 1450842, `n_kaba = 48`, `λ = 2`, `r_iç = 0,15`)

| kol | N | toplam kütle | E_enjekte | **r_ölçülen** | adım |
|---|---|---|---|---|---|
| tek / kaba | 110 592 | 1,000000 | 1,000000 | **0,24336** | 221 |
| **iki bölgeli** | 121 592 | 1,000027 | 1,000000 | **0,24732** | 258 |
| tek / ince | 884 736 | 1,000000 | 1,000000 | **0,24701** | 258 |

```
aralik [0,24336 ; 0,24701]   genislik %1,503

ON KOSULLAR
  kollar ayirt edilebilir : True
  enerji uc kolda ayni    : True   (1,000000 / 1,000000 / 1,000000)
  kutle ihmal edilebilir  : True   (%0,0027 -> yaricapa %0,0005)

iki bolgeli aralikta mi   : True     tasma %0,125

YARGI: interface_harmless
```

---

## 3. Okuma

### (a) Şok, arayüzü **bedelsiz** geçiyor

İki bölgeli kol `0,24732`; tek popülasyonlu **ince** kol `0,24701`. Fark
**%0,125** — ölçüm aralığının (%1,503) **on ikide biri**.

> **8:1 kütle oranlı bir arayüzden geçen şok, tümüyle ince çözülmüş bir
> koşuyla aynı yarıçapa varıyor.**

### (b) İki bölgeli kol, **ince** kolun tarafında

Ve bu beklenendir: patlama **ince bölgede** başlar. Şokun erken evrimi —
yörüngesini belirleyen kısım — orada geçer; arayüze vardığında zaten
kendine-benzer rejime girmiştir.

Adım sayısı da bunu doğruluyor: iki bölgeli **258**, ince kol **258**, kaba
kol **221**. İki bölgeli koşu, zaman adımı açısından ince koşu gibi
davranıyor.

### (c) Statik ölçümle çelişmiyor — **tamamlıyor**

KAYIT-020 arayüzde `a/ölçek ≈ 0,21` yapay ivme ölçtü. KAYIT-022 o ivmenin
**doyduğunu** gösterdi (`v ~ t^0,72`). E3 üçüncü halkayı ekliyor:

> Yapay ivme bir **gürültü tabakasıdır**; doyar; ve **şokun yayılımına
> ölçülebilir bir katkı yapmaz.**

Üç ölçüm aynı resmi veriyor.

---

## 4. Bunun karar için anlamı — **A'yı geri getirmez**

Bu sonuç arayüzün **zararsız** olduğunu söylüyor. Ama A'nın elenme sebebi
arayüz **değildi**:

> A elendi çünkü tek global `h` ile ince bölgeye parçacık eklemek
> **çözünürlüğü artırmıyor** (KAYIT-023: plato `h → 0` limitinden %6,84
> uzakta ve kapanmıyor).

E3, bu koşunun kendisinde de görülüyor: iki bölgeli kol ince kolla **aynı**
sonucu veriyor — yani ince parçacıklar **fizik** eklemiyor, yalnızca aynı
`h`'nin içini daha sık örnekliyor. Zaten KAYIT-023'ün söylediği buydu.

**Ama başka bir şey söylüyor:** kütle oranı arayüzü, **A′ ya da C hangisi
seçilirse seçilsin**, şok geçişi açısından bir engel değil. Yani 4.2 kararı
arayüz kalitesine değil, **çözünürlük** ve **korunum** eksenlerine
odaklanabilir.

---

## 5. Karar tablosu — dördüncü güncelleme

| # | yaklaşım | mermiyi çözer | yapay kuvvet | **şok geçişi** | mimari bedel |
|---|---|---|---|---|---|
| ~~A~~ | global `h` | **hayır** | 0,168 | **zararsız** ✔ | yok |
| **A′** | parçacık başına `h` | evet | 0,55–1,10 | ölçülmedi (A'da zararsız) | çekirdek+grid+CFL+Ω |
| **B** | bölme | A′ ile | = A′ | = A′ | = A′ |
| **C** | iki alan eşlemesi | evet | **yok** | ölçülmedi | iki çözücü + örtüşme + MLS |
| **D** | kaynak terimi | **atlar** | yok | — | ılımlı |

**Kalan tek belirleyici ölçüm: C-2** (eşlenmiş sistemde korunum kayması) ve
**D-1** (kaynak teriminin model-form hatası).

---

## 6. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| yumuşak alandan şoka **çıkarım yapılmaz**, ölçülür | §0 |
| tam çözüme değil, **kollara** kıyasla (ADR-0011 tabanı) | §1 |
| **üç** ön koşul, biri düşerse `inconclusive` | §1, §2 |
| kollar ayırt edilemiyorsa sonuç **boş bir doğrudur** | §1 (1. ön koşul) |
| kütle uyuşmazlığı **susulmaz**, sınırlanır | §2 (%0,0005) |
| olumlu sonuç, **elenmiş** bir seçeneği geri getirmez | §4 |
