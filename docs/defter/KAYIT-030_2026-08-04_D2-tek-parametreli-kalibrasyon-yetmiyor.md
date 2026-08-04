# KAYIT-030 — D-2: tek parametreli kalibrasyon **yetmiyor** (2026-08-04)

**Kapsam:** FAZ 4.2 son ölçüm · **Durum:** ölçüldü — **D'nin serbest
parametresi bağlanamadı**
**Öncül:** [KAYIT-029](KAYIT-029_2026-08-04_D1b-duzeltme-kaynak-terimi-duyarli.md),
ADR-0041 §5

---

## 0. Soru

KAYIT-029 ölçtü: D'nin model-form hatası DART bandında **%5–7** ve
biriktirme yarıçapı **serbest bir parametredir**. Serbest bir parametre
**kalibre edilebiliyorsa** kusur olmaktan çıkar.

> Gerçek mermiyi temsil eden `r_dep` **hesaplanabilir** mi?

---

## 1. Düzenek — piston

Gerçek mermi enerjisini **toplu hareket** olarak taşır ve şokta ısıya
çevirir; kaynak terimi ise doğrudan **ısı** olarak koyar. Küresel simetriyi
bozmadan bunu kuran düzenek:

```
piston(R)       :  KE = E_INJECT (homolog, v = c·x),  u = arka plan
biriktirme(r_d) :  u  = E_INJECT,                     v = 0
```

**Aynı enerji, farklı biçim.** Her `R` için `r_p(R) = r_b(r_d)` sağlayan
`r_d` aranır. `r_d/R` sabitse kalibrasyon **taşınabilirdir**.

KAYIT-029'un dersi uygulandı: `n_side = 128`, tüm pistonlar `n ≥ 136`.

---

## 2. Ölçüm (TRUBA, iş 1451309, 2147 s)

### Piston kolu

| `R` | `n_piston` | `KE` | `r_şok` | `KE/E` (son) | adım |
|---|---|---|---|---|---|
| 0,0250 | 136 | 1,000000 | 0,23247 | 0,17313 | 796 |
| 0,0350 | 360 | 1,000000 | 0,23559 | 0,18814 | 593 |
| 0,0500 | 1088 | 1,000000 | 0,24354 | 0,20930 | 378 |
| 0,0700 | 3016 | 1,000000 | 0,25088 | 0,21813 | 298 |

Enerji dördünde de **tam** `1,000000` — iki kol aynı enerjiyi taşıyor.

### Biriktirme kolu

| `r_dep` | `n_enj` | `r_şok` | `KE/E` (son) | adım |
|---|---|---|---|---|
| 0,0250 | 136 | 0,22389 | 0,13175 | 2522 |
| 0,0300 | 208 | 0,22585 | 0,13606 | 2087 |
| 0,0400 | 552 | 0,23053 | 0,14684 | 1407 |
| 0,0500 | 1088 | 0,23499 | 0,15688 | 1010 |
| 0,0600 | 1904 | 0,23755 | 0,16755 | 783 |
| 0,0800 | 4632 | 0,24023 | 0,18908 | 526 |

---

## 3. Betiğin ilk yargısı **yanıltıcıydı** — ve iki kusuru vardı

Betik şunu yazdı:

```
oran r_d/R ortalama : 1.6349
oran YAYILIMI       : %17.0
TASINABILIR MI      : True
-> Kalibrasyon TASINABILIR: r_dep ~ 1.635 * R_mermi
```

**Raporlanmadan önce iki kusur bulundu.**

### Kusur 1 — `np.interp` aralık dışında **kelepçeliyor**

| `R` | `r_şok(piston)` | `r_dep eşdeğer` | oran | aralıkta |
|---|---|---|---|---|
| 0,0250 | 0,23247 | 0,04435 | 1,7741 | ✔ |
| 0,0350 | 0,23559 | 0,05235 | 1,4957 | ✔ |
| 0,0500 | 0,24354 | **0,08000** | 1,6000 | **✘** |
| 0,0700 | 0,25088 | **0,08000** | 1,1429 | **✘** |

Son iki pistonun şok yarıçapı (`0,24354`, `0,25088`) biriktirme kolunun
üst sınırını (`0,24023`) **aşıyor**. `np.interp` onları **uç değere
kelepçeliyor** ve ikisi de `0,0800` çıkıyor — sonra `0,0800/R` bölmesi
`1,60` ve `1,14` gibi **uydurma** oranlar üretiyor.

Bunlar ölçüm değil, **kelepçe artefaktı**. Artık aralık dışında oran `NaN`.

### Kusur 2 — iki nokta bir **sabitlik** iddiasını taşıyamaz

Geriye kalan **iki** nokta (`1,7741`, `1,4957`). İki noktayla "yayılım"
zaten **tek bir farktır**; sabitlik kanıtı değildir. Eşik `≥ 3` yapıldı.

> Betiğin eşiği (`≥ 2`) ölçümden **önce** yazılmıştı — yani post-hoc değil.
> Ama yine de yetersizdi.

---

## 4. Asıl bulgu: **ikinci gözlenebilir eşleşmiyor**

Şok yarıçapı eşlendiğinde kinetik enerji kesri ne oluyor?

| `R` | `r_dep` eşdeğer | `KE/E` piston | `KE/E` biriktirme | **uyuşmazlık** |
|---|---|---|---|---|
| 0,0250 | 0,04435 | 0,17313 | 0,15121 | **%14,5** |
| 0,0350 | 0,05235 | 0,18814 | 0,15939 | **%18,0** |

> **Şok yarıçapı eşleşirken kinetik enerji kesri %14,5–18,0 ayrışıyor.**
> Tek parametreli kalibrasyon **iki gözlenebiliri aynı anda eşlemiyor**.

### Bu bir ayar sorunu değil

Piston enerjiyi **hareket** olarak taşır ve şok üzerinden ısıya çevirir;
biriktirme onu **baştan ısı** olarak koyar. Geç zamandaki kinetik/termal
bölüşüm bu yüzden farklı kalıyor. Bir tek sayı (`r_dep`) iki bağımsız
büyüklüğü aynı anda ayarlayamaz.

Piston kolunun `KE/E`'si (0,173–0,218) biriktirme kolununkinden
(0,132–0,189) **sistematik olarak yüksek** — yani fark yönlü ve
yapısaldır.

---

## 5. Düzeltilmiş yargı

```
aralikta 2/4      yeterli nokta: False
ikinci gozlenebilir esliyor mu: False (maks uyusmazlik %18,0)
TASINABILIR: False
```

> **D'nin serbest parametresi bağlanamadı.** Biriktirme yarıçapı, şok
> yarıçapını eşleyecek biçimde seçilebilir — ama o seçim kinetik enerji
> kesrini **%18'e kadar** yanlış bırakır.

β momentum-türevi bir büyüklüktür ve kinetik/termal bölüşüme **doğrudan**
bağlıdır. Yani bu uyuşmazlık D'nin ana ürününü etkiler.

---

## 6. ADR-0041'e etkisi

ADR-0041'in §5 gerekçesi zaten KAYIT-029 ile zayıflamıştı:

> D korunumu bozmuyor, ama **model-form duyarlılığı düşük değil** ve
> biriktirme yarıçapı **kalibre edilmesi gereken serbest bir parametredir**.

Bu kayıt bir adım daha atıyor:

> **O kalibrasyon tek parametreyle yapılamıyor.** İki gözlenebilir aynı
> anda eşlenemiyor; `r_dep` seçimi hangi gözlenebilirin doğru olacağını
> **seçmek** demektir.

### Denge artık nerede

| | A′ | D |
|---|---|---|
| mermiyi çözer | **evet** | hayır |
| model-form hatası | **yok** | %5–7, **kalibre edilemiyor** |
| momentum | `1e-16` ✔ | ✔ |
| arayüz | 3,2–6,5 kat gürültü | yok |
| mimari bedel | çekirdek + grid + CFL + Ω | ılımlı |

**A′ öne geçti.** Model-form hatası **yoktur** çünkü mermiyi gerçekten
çözer; bedeli yalnızca mimaridir ve arayüz gürültüsü şok geçişinde
**ölçülemez** (KAYIT-026: taşma %0,000).

D hâlâ tümüyle elenmiş değil — ama artık *"ucuz ve yeterince doğru"*
diye savunulamaz.

---

## 7. Sırada

| # | iş | neden |
|---|---|---|
| **A′-1** | A′'nın mimari iş yükü kestirimi | kararın diğer kefesi hâlâ **ölçülmedi** |
| D-3 | **iki parametreli** kaynak terimi (yarıçap + kinetik/termal bölüşüm) | tek parametre yetmiyorsa iki deneyebilir |
| — | ADR-0041 §5 boşluk 3 (mukavemetli malzeme) | hâlâ açık |

---

## 8. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| kendi betiğinin yargısı **denetlenir** | §3 — `TASINABILIR: True` yanlıştı |
| ara değerleme **kelepçelerse** o sayı ölçüm değildir | §3 kusur 1 |
| iki nokta **sabitlik** iddiasını taşımaz | §3 kusur 2 |
| bir eşleme **tek** gözlenebilirle doğrulanmaz | §4 |
| eşik ölçümden **önce** yazılmış olsa da yetersiz olabilir | §3 |
| yanlış çıkan yargı **silinmez**, düzeltilir | §3, §5 |
