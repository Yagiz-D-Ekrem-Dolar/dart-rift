# KAYIT-023 — Çözülen ölçeği `h` belirliyor: A yaklaşımı elenir (2026-08-04)

**Kapsam:** FAZ 4.1-E3 önkoşulu · **Durum:** ölçüldü, **A yaklaşımı elendi**
**Öncül:** [KAYIT-022](KAYIT-022_2026-08-04_E1-E2-karar-verisi.md), ADR-0011, ADR-0013, ADR-0026

---

## 0. Bu ölçüm neden yapıldı

E3'ü (arayüzden şok geçişi) kurarken bir **mimari olgu** fark ettim.
Kod tabanının tamamında `h` **skalerdir**:

```
warp_core/solver.py:179        self.h = float(h)
warp_core/solver_solid.py:299  self.h = float(h)
cpu_reference/solid_ref.py:46  h: float
```

Yani A yaklaşımı (değişken kütle bölgeleri) bu kodda ancak **tek global `h`**
ile uygulanabilir. KAYIT-020 ve KAYIT-022'de ölçtüğüm şey tam olarak budur —
ve bunu o kayıtlarda **açıkça yazmamıştım**. Önemli bir kısıttır.

Buradan doğrudan bir soru çıkıyor:

> SPH'de çözülen ölçek `h` ise, bir bölgeye 8 kat parçacık koyup `h`'yi kaba
> tutmak **çözünürlüğü artırır mı?**

Artırmıyorsa A, ADR-0026'nın sorununu (DART mermisini çapı boyunca 6
parçacıkla çözmek) **çözemez** ve karar A'nın dışına çıkmak zorundadır.

**Bu önemli bir iddiadır ve ölçülmeden yazılmaz.**

---

## 1. İlk tasarımım yanlıştı — ve neden yanlış olduğunu betiğin kendisi söyledi

Sınavı şöyle kurdum: *"olağan yakınsamada hata **küçülmeli** (boşluk
kontrolü), sabit `h`'de **düzleşmeli**."*

ADR-0011'i okumadan yazdım. **ADR-0011 bunu zaten ölçmüştü:** bu kurulumda şok
yarıçapı hatası **%3,9'luk bir tabana** oturur, sıfıra gitmez. Sebebi
ayrıklaştırma değil **model-form** — enerji noktasal değil, şok yarıçapının
~%32'si kadar bir bölgeye konuyor; analitik çözüm ise nokta patlaması varsayar.

Yani boşluk kontrolüm **küçülmeyeceği bilinen** bir şeyin küçülmesini
bekliyordu. İş 1450756:

```
  BOSLUK KONTROLU  olagan kol kuculuyor mu : False  (0.01153 -> 0.04464)
  -> SINAV AYIRT ETMIYOR: sonuc yorumlanamaz
```

**Betik doğru davrandı.** Boşluk kontrolü düştüğü için *"h belirliyor"*
sonucunu **vermedi**, `inconclusive` dedi. ADR-0040'ın kuralı beni kendi
hatamdan korudu.

Ölçülen değerler ADR-0011'in tablosuyla **birebir aynı** (0,2528 / 0,2434 /
0,2387) — gerileme yok, yalnızca tasarım yanlıştı. Kayıt: **S7**.

---

## 2. Doğru ölçüt: hata değil, **platonun yeri**

Hata sıfıra gitmiyor. Ama yarıçap bir değere **oturuyor**. Doğru soru:

> Her kol **hangi** değere oturuyor?

Ve kesin kanıt için üçüncü bir kol: **başka bir sabit `h`** başka bir platoya
oturmalıdır. Oturuyorsa platonun yerini `h` belirliyor demektir.

---

## 3. Ölçüm (TRUBA H200, iş 1450829, commit `6c0a96d`)

Sedov, `t_end = 0,0288`. Nokta patlaması için tam yarıçap `0,249897`
(hiçbir kol buna oturmaz — ADR-0011).

### Kol A — `h/dx = 2` sabit, yani `h → 0`

| n | N | dx | h | h/dx | r_ölçülen | adım |
|---|---|---|---|---|---|---|
| 48 | 110 592 | 0,02083 | 0,04167 | 2,00 | 0,24336 | 221 |
| 64 | 262 144 | 0,01562 | 0,03125 | 2,00 | 0,23874 | 287 |
| 80 | 512 000 | 0,01250 | 0,02500 | 2,00 | 0,23983 | 345 |
| 96 | 884 736 | 0,01042 | 0,02083 | 2,00 | 0,24004 | 407 |
| 112 | 1 404 928 | 0,00893 | 0,01786 | 2,00 | 0,24011 | 464 |

**PLATO = 0,24008** — son değişim %0,032, **oturdu**.

### Kol B — `h = 0,06250` **sabit**, yalnızca `dx` küçülüyor

| n | dx | h/dx | r_ölçülen |
|---|---|---|---|
| 32 | 0,03125 | 2,00 | 0,25278 |
| 40 | 0,02500 | 2,50 | 0,25530 |
| 48 | 0,02083 | 3,00 | 0,25590 |
| 56 | 0,01786 | 3,50 | 0,25667 |
| 64 | 0,01562 | 4,00 | 0,25633 |

**PLATO = 0,25650** — son değişim %0,132, **oturdu**.

### Kol C — `h = 0,03125` **sabit** (B'nin yarısı)

| n | dx | h/dx | r_ölçülen |
|---|---|---|---|
| 64 | 0,01562 | 2,00 | 0,23874 |
| 72 | 0,01389 | 2,25 | 0,24068 |
| 80 | 0,01250 | 2,50 | 0,24196 |
| 88 | 0,01136 | 2,75 | 0,24280 |
| 96 | 0,01042 | 3,00 | 0,24325 |

**PLATO = 0,24303** — son değişim %0,184, **oturdu**.

---

## 4. Yargı

```
BOSLUK KONTROLU  uc kol da oturdu mu   : True
kaba sabit-h platosu limitten uzakligi : %6,84
ince sabit-h platosu limitten uzakligi : %1,23
plato h ile KAYIYOR mu                 : %5,25
h kuculunce limite YAKLASIYOR mu       : True

YARGI: h_sets_resolution
```

### İki etkinin temiz ayrışması

| değişen | etkisi |
|---|---|
| **`h/dx`** (komşu sayısı) | **quadrature** hatası → platoya **yaklaştırır** |
| **`h`** | **platonun yeri** → fiziksel çözünürlük |

Kol B'de `h/dx` 2,00'den 4,00'e çıkıyor (komşu sayısı ~8 kat) ve sonuç
`0,25278 → 0,25650`'ye **oturuyor** — ama `0,24008`'e **gitmiyor**.
`h` yarıya inince (kol C) plato `0,24303`'e taşınıyor: limite uzaklık
**%6,84 → %1,23**, yani **5,6 kat** iyileşme.

> **Sabit `h`'de ne kadar parçacık eklenirse eklensin, `h → 0` limitinin
> oturduğu yere ulaşılamıyor. Çözülen ölçeği `h` belirliyor.**

---

## 5. Bunun FAZ 4.2 kararına etkisi — A elenir

ADR-0026: DART mermisini çapı boyunca 6 parçacıkla çözmek **1,72e9** parçacık
ister; fizibil sınır **1,12e7**; oran **153×**.

A yaklaşımı (tek global `h` + değişken kütle) bu koda uygulandığında **iki
yoldan biri** seçilmek zorundadır ve **ikisi de kapalıdır**:

### Yol 1 — `h`'yi **kaba** bölgeye göre seç

Bu ölçümün tam olarak sınadığı durum. Çarpma bölgesine 8 kat, 64 kat parçacık
konabilir; çözülen ölçek **değişmez**. Mermi hâlâ çözülmez.

**Ölçüldü: plato limitten %6,84 uzakta ve parçacık eklemekle kapanmıyor.**

### Yol 2 — `h`'yi **ince** bölgeye göre seç

O zaman kaba bölgede `h/dx < 1` olur. **ADR-0013 bunu zaten ölçmüş:**

| h/dx | komşu | şok yarıçapı hatası |
|---|---|---|
| 1,25 | 65 | **%15,8** |
| 1,60 | 137 | %6,5 |
| 2,00 | 268 | %2,6 |

`λ = 2` (8:1 kütle oranı) için kaba bölgede `h/dx = 1,0` → 34 komşu →
ADR-0013'ün en kötü noktasından **daha kötü**. Uzak alan kullanılamaz hâle
gelir.

### Sonuç

> **A yaklaşımı, `h`'nin skaler olduğu bir kodda ADR-0026'nın sorununu
> çözemez.** Bu bir ayar değil, bir **mimari** olgudur.

---

## 6. Karar uzayı yeniden çizildi

| # | yaklaşım | bu koda uygunluğu |
|---|---|---|
| ~~A~~ | ~~değişken kütle, tek global `h`~~ | **ELENDİ** — çözünürlük artmıyor (§5) |
| **A′** | değişken kütle **+ parçacık başına `h`** | çekirdek/hash-grid/CFL **mimari değişikliği** ister |
| **B** | parçacık bölme | bölme `dx`'i küçültür; **`h` skaler kaldıkça faydasız** → A′'yı gerektirir |
| **C** | iki alan eşlemesi | **mevcut mimariyle uyumlu**: her alanın kendi skaler `h`'si olur |
| **D** | kaynak terimi (mermiyi hiç çözme) | `h` kaba kalır; çözünürlük sorunu **ortadan kalkar**, model-form hatası girer |

**Yeni bilgi:** B, bağımsız bir seçenek değil — A′'nın bir alt kümesi.
Ve **C, mevcut skaler-`h` mimarisiyle çalışabilecek tek "mermiyi çöz"
seçeneğidir.**

Bu, KAYIT-019'da yazdığım dört seçenekli tablonun **ölçümle daraltılmış**
hâlidir. ADR-0041 bu tablo üzerinden yazılacak.

---

## 7. Hâlâ eksik

| # | eksik | neden gerekli |
|---|---|---|
| E3 | arayüzden **şok** geçişi | C seçeneğinin arayüzü de şok geçirecek; yansıma/iletim ölçülmeli |
| — | A′'nın **maliyeti** | parçacık başına `h` çekirdeği, hash-grid ve CFL'i değiştirir; iş yükü kestirimi yapılmadı |
| — | D'nin **model-form hatası** | çözülmüş bir referansla kıyas gerekir (ama referans 1,72e9 parçacık ister — dolaylı kıyas tasarlanmalı) |

**Karar hâlâ verilmedi.** Ama karar uzayı ölçümle **dörtten üçe** indi ve
kalanlar arasındaki fark artık *tercih* değil, *mimari maliyet*.

---

## 8. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| önemli iddia **ölçülmeden yazılmaz** | §0 |
| ölçüm tasarlamadan önce **ilgili ADR okunur** | §1 (S7 — okumadım, düştüm) |
| kriter **düşebilmeli**; düşerse sonuç **verilmez** | §1 — betik `inconclusive` dedi |
| yakınsamayan bir büyüklükte **öz-yakınsama** ölçülür | §2 |
| tek bir kol yetmez: **üçüncü kol** açıklamayı sınar | §3 kol C |
| var olan ölçümler yeniden **kullanılır** | §5 Yol 2 — ADR-0013 |
