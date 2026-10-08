# Protokol SI — kaydedilmiş durumlardan **son işleme** ölçümleri (KİLİTLİ)

**Yazıldı:** 2026-10-08, **ölçümler yapılmadan ÖNCE.** TRUBA erişimi o an
kapalıydı, yani hiçbir sayı görülmedi.
**Öncül:** [PLAN-90-GUN](../PLAN-90-GUN.md) §1, KAYIT-076 (DO/DC/DN),
ADR-0054 (hedef `β`), literatür taraması (2026-10-08).
**Girdi:** `*.durumlar/nokta_*.npz` (`x, v, m, u, rho, x_referans, alpha,
P, S, D, h, cs, strain, mermi_kesri`) + `fizik_tani`.
**Maliyet:** **sıfır GPU.**

---

## 1. Niçin

Her koşunun tam durumu kaydediliyor. Buradan çıkarılabilecek her ölçüm
**GPU istemiyor** ve TRUBA kapalıyken de hazırlanabiliyor. Bu protokol altı
ölçümün yargı kurallarını, **sayılar görülmeden** kilitler.

Üçü (§5 spin, §6 yoğunluk, §7 şekil) **Hera'nın sınayacağı öngörü**
olabilir; mühürleme PROTOKOL-HT'nin işi, bu protokol yalnız **ölçümü**
tanımlar.

### Ortak geçerlilik

Bir kol için `gecerli = True`, `t = 600 s`, `kutle_tutarliligi` tutarlı.
Değilse o kolun **bütün** SI ölçümleri **OKUNMAZ**.

### Ortak künye — doğrulanacak sabitler

Aşağıdaki sayılar **birincil kaynaktan teyit edilmeden** hiçbir ölçüm
koşulmaz (teyit edilince bu tabloya kaynak yazılır):

| sabit | kullanılan | kaynak |
|---|---|---|
| Didymos kütlesi | **teyit bekliyor** | Daly 2023 / Naidu 2024 |
| yörünge yarı ekseni `a` | `~1206 m` **teyit bekliyor** | aynı |
| yörünge periyodu `T` | `11,92 sa` (çarpma öncesi) **teyit bekliyor** | aynı |
| Dimorphos kütlesi | `4,3e9 kg` | `GOZLEM_KUTLESI` (A108) |

> **Kural:** teyit edilmemiş sabitle koşulan ölçüm **OKUNMAZ** sayılır.
> Hatırladığım sayıyla hesap yapmak, ölçülmemiş bir kesinlik iddiasıdır.

---

## 2. İki kaçış ölçütüyle `β` ve geri düşme payı

### Neden

Modelin kaçış eşiği Dimorphos'un **kendi** kaçış hızı
(`escape_speed(M, R) = 0,0805 m/s`). Ama Dimorphos, Didymos'un
`~1,2 km` yakınında: **sistemden** kaçış `~0,24 m/s`. Literatür iki `β`'yı
ayrı veriyor ve aradaki fark `%6` mertebesinde.

### Ölçüm

`b = β − 1`. Aynı son durumdan, **yalnız eşik değişerek**:

- `b_Dimorphos` : `v_esc` = `escape_speed(M_D, R_etkin)` (koşunun kendi
  değeri, `kacis_hizi_kalibre` ile geri çözülür)
- `b_sistem` : `v_esc` = `sqrt(2 G M_Didymos / a)`

**`σ_kacis = |b_Dimorphos − b_sistem| / b_Dimorphos`**

### Kilitli yargı

| yargı | koşul | sonucu |
|---|---|---|
| **KACIS OLCUTU ONEMSIZ** | `σ_kacis ≤ 0,03` | terim bütçeye yazılır, `β` tanımı değişmez |
| **LITERATURLE UYUMLU** | `0,03 < σ_kacis ≤ 0,12` | aynı; literatürün `%6`'sı doğrulanmış sayılır |
| **KACIS OLCUTU BASAT** | `σ_kacis > 0,12` | `β`'nın hangi ölçütle raporlandığı **başlıkta** yazılır ve ikisi yan yana verilir |

**Hangi `β` hedefle karşılaştırılır:** Cheng'in `β`'sı Dimorphos'un
**yörünge periyodu** değişiminden türüyor; Dimorphos'tan ayrılan madde o
bütçeden çıkmış sayılır. Dolayısıyla **kilitli karşılaştırma
`b_Dimorphos` ile** yapılır. `b_sistem` **yan yana** raporlanır ve
heliyosentrik sapmayla ilgilenen okuyucuya aittir. Bu seçim koşudan önce
yapıldı.

---

## 3. `β`'nın yörünge hızı yönüne projeksiyonu

### Neden

Literatür: `β`, **yörünge hızı yönünde** ölçülür; yana giden ejekta
momentumu yörünge periyodunu doğrudan değiştirmiyor. Bizim `beta_hedef`
**mermi momentumu** yönünde projekte ediliyor. DART yörünge hızına
yaklaşık ters çarptı ama `17°` eğik → iki tanım `cos 17° = 0,956` kadar
ayrılabilir.

### Ölçüm

`ê_mermi` = mermi momentumu birim vektörü (koşunun kullandığı).
`ê_yörünge` = Dimorphos'un çarpma anındaki yörünge hızı birim vektörü
(künyeden; **teyit bekliyor**).

    b_mermi   = K · Σ m (−v·ê_mermi)   / p        (mevcut tanım)
    b_yörünge = K · Σ m (−v·ê_yörünge) / p

**`σ_yon = |b_mermi − b_yörünge| / b_mermi`**

### Kilitli yargı

| yargı | koşul |
|---|---|
| **YON FARKI ONEMSIZ** | `σ_yon ≤ 0,02` |
| **GEOMETRIK BEKLENTIYLE UYUMLU** | `0,02 < σ_yon ≤ 0,08` (≈ `1 − cos 17°` mertebesi) |
| **YON FARKI BASAT** | `σ_yon > 0,08` → hangi tanımla raporlandığı başlıkta yazılır |

**Kilitli karşılaştırma `b_yörünge` ile olur** — çünkü gözlenen `β`
periyot değişiminden türüyor ve o, yörünge yönündeki momentumu ölçüyor.
`b_mermi` yan yana kalır ve geçmiş bütün yargılar (DY2 dahil) onunla
hesaplandığı için **olduğu gibi** durur.

---

## 4. Balistik son işleme — Didymos çekimi ve geri düşme

### Neden

Geri düşme `10–11 saat` sürüyor; koşu `600 s`'de bitiyor. Literatür bir
hafta sonra ejektanın `~%9`'unun Dimorphos'a geri biriktiğini bildiriyor.
Yani "kaçtı" saydığımız maddenin bir kısmı dönüyor → `β` **yukarı yanlı**.

`600 s`'de kaçan madde artık **balistik**: temas kuvveti ve dayanım yok.
Dolayısıyla SPH'yi uzatmak gerekmiyor; test parçacığı entegrasyonu yeter.
Bu, alanın **standart** yöntemi (çarpma kodu + N-cisim evresi).

### Yöntem

1. Kaçan parçacıklar (`v > v_esc,Dimorphos`) test parçacığı alınır.
2. Çekim: Dimorphos (nokta kütle + **elipsoit** çarpışma sınaması) +
   Didymos (nokta kütle, `a` uzaklıkta) + dönen çerçeve (`T`).
3. `t_son = 12 saat`. Her parçacık üç sonuçtan birine düşer:
   **geri düştü** (elipsoide değdi) / **sistemde bağlı** / **sistemden kaçtı**.
4. `b_balistik` = yalnız **sistemden kaçan** maddeden yeniden hesaplanır.

İhmal edilenler (yazılı): parçacık-parçacık çarpışmaları, ejekta öz
çekimi, güneş radyasyon basıncı, Didymos'un şekli.

### **Entegratör kapısı** — geçmezse sonuç OKUNMAZ

| sınav | eşik |
|---|---|
| `t = 0`'da `b_balistik` mevcut `b`'yi yeniden üretiyor | bağıl fark `< 1e-6` |
| Çekim kapalıyken momentum korunuyor | bağıl artık `< 1e-10` |
| Tek parçacık + tek nokta kütlede analitik Kepler yörüngesi | enerji sapması `< 1e-6` |

### Kilitli yargı

**`σ_geri = |b_600s − b_balistik| / b_600s`**

| yargı | koşul |
|---|---|
| **GERI DUSME ONEMSIZ** | `σ_geri ≤ 0,05` |
| **LITERATURLE UYUMLU** | `0,05 < σ_geri ≤ 0,20` (bir haftada `%9` birikme) |
| **GERI DUSME BASAT** | `σ_geri > 0,20` → `t_end` kararı (A110) yeniden açılır |

`σ_geri` **bütçeye ölçülmüş terim** olarak girer (`plato_olculen_DART`
yanına, onu **değiştirmeden**).

---

## 5. Spin / açısal momentum değişimi — **Hera sınayacak**

### Neden

DART çarpması Dimorphos'un dönme durumunu değiştirdi; literatürde takla
atma tartışılıyor. **Hera dönme durumunu doğrudan ölçecek.**

### Ölçüm

Bağlı malzemeden (`v ≤ v_esc`), kütle merkezi çerçevesinde:

    L = Σ m (r − r_km) × (v − v_km)

`L_0` aynı büyüklük `x_referans` ve çarpma öncesi hız alanından (sıfır).
Raporlanan: `|L|`, yönü, ve eylemsizlik tensöründen **dönme periyodu
değişimi** kestirimi.

### Kilitli yargı

| yargı | koşul |
|---|---|
| **SPIN DEGISIMI OLCULEBILIR** | kestirilen periyot değişimi `> %1` |
| **SPIN DEGISIMI KUCUK** | `≤ %1` |
| **OKUNMAZ** | bağlı parçacık `< 1000` (kütle merkezi ve tensör gürültülü) |

**Mühürlenecek sayı:** `|L|` ve periyot değişimi kestirimi, belirsizlikle.
Belirsizlik gerçeklem saçılmasından (iki tohum, DY2/DT) **ölçülür**.

---

## 6. Yoğunluk / sıkışma değişimi — **Hera sınayacak**

### Neden

Hera kütleyi radyo bilimle, şekli görüntüyle ölçüp **yığın yoğunluğunu**
verecek. Çarpma cismi sıkıştırdıysa ya da gevşettiyse öngörülebilir.

### Ölçüm

`alpha` (gözenek genişleme) alanından, bağlı malzemede kütle ağırlıklı:

    α_son / α_0 − 1        (negatif = sıkışma)
    ρ_yığın,son = M_bağlı / V_bağlı      (p99,5 kabuğundan hacim)

### Kilitli yargı

| yargı | koşul |
|---|---|
| **SIKISMA OLCULEBILIR** | `|Δρ/ρ| > %1` |
| **SIKISMA KUCUK** | `≤ %1` |

Dikkat: `V_bağlı` kabuk yüzdeliğine duyarlı. **İki yüzdelikle
(`p99` ve `p99,5`) hesaplanır ve ikisi yan yana raporlanır**; fark
belirsizliğe girer.

---

## 7. Şekil değişimi — **Hera sınayacak**

### Ölçüm

`yari_eksenler` alanı zaten kaydediliyor (`p99,5`). Çarpma öncesi
(`88,5 / 87 / 58 m`) ile karşılaştırılır:

    Δa/a, Δb/b, Δc/c        ve        basıklık değişimi

### Kilitli yargı

| yargı | koşul |
|---|---|
| **SEKIL DEGISIMI OLCULEBILIR** | en büyük `|Δ/eksen| > %1` |
| **SEKIL DEGISIMI KUCUK** | `≤ %1` |

Belirsizlik: gerçeklem çifti (DY2/DT) + iki kabuk yüzdeliği.

---

## 8. Bu protokolün yapmadığı şey

- **Mühürlemiyor.** §5/§6/§7'nin sayıları PROTOKOL-HT'de, posteriordan
  örneklenmiş `θ`'larda ve ön kayıtlı biçimde mühürlenir.
- **Geçmiş yargıları değiştirmiyor.** DY2'nin `MODEL GÖZLEME ULAŞIYOR`'u
  `b_mermi` ve `v_esc,Dimorphos` ile hesaplandı ve **öyle kalır**
  (kural 6). Yeni ölçümler **yan yana** girer.
- **Önsel/hedef seçimine dokunmuyor** (KAYIT-075'in beş kararı yerinde).
