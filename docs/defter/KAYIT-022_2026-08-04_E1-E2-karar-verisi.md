# KAYIT-022 — E1 ve E2: FAZ 4.2 kararının verisi (2026-08-04)

**Kapsam:** FAZ 4.1-E1, 4.1-E2 · **Durum:** ikisi de ölçüldü
**Öncül:** [KAYIT-020](KAYIT-020_2026-08-04_arayuz-hatasi-nicel.md) §6

---

## 0. KAYIT-020'nin bıraktığı iki soru

| # | soru | neden karar için gerekli |
|---|---|---|
| **E1** | gerçek oturmuş yığın §5 tablosunun **hangi satırında**? | %2 ise arayüz 3,26× katıyor; %10 ise hiç katmıyor |
| **E2** | yapay kuvvet **birikiyor mu**? | `t = 0` anlıktır; sabit bir kuvvet hızı doğrusal büyütür |

İkisi de yanıtlandı. **E1 KAYIT-020 §5'in yargısını tersine çevirdi.**

---

## 1. E1 — gerçek yığın ne kadar düzensiz?

### Yöntem: vekil değil, **aynı sonda**

K14'ün dersi gereği düzensizlik bir **vekille** (ör. paketleme kesri)
ölçülmedi. Sarsıntılı kafeslere uygulanan **aynı sonda** gerçek yığına da
uygulandı; sonuç kalibrasyon eğrisine oturtuldu.

### K7'nin dördüncü tuzağı — sondada

Gerçek yığının kütleleri **yığın** yoğunluğuna (2400) göre üretilir, **katı**
yoğunluğuna (2700) göre değil. Sondanın skaler `rho0`'ı `m/ρ ≠ V_p` yapardı
ve ölçülen "düzensizlik" aslında **kütle tutarsızlığı** olurdu.

Sondaya `rho_base = m / V_p` eklendi. Doğrulandı:

```
rho_taban = m/V_p: [2400.0, 2400.0] kg/m3   (yigin hedefi 2400)
```

ADR-0030'un değişmezi gerçek yığında da **tam** tutuyor.

### İkinci vekil tuzağı — küresel `r`

Hedef bir **elipsoit** (88×87×74 m). `|x|` yüzeye uzaklığın vekilidir ve kısa
eksende **yanılır**. İç maske mesh'in **işaretli mesafesinden** türetildi:

```python
pay = 2.0 * h + 0.5 * spacing                      # cekirdek destegi + guvenlik
maske = signed_distance(mesh, x) < -pay
```

Sonuç: `798 / 3324` parçacık (pay = 31,0 m).

### Kalibrasyon eğrisi

| sarsıntı | a_rms | a/ölçek |
|---|---|---|
| 0,00 | 7,2548e-12 | 0,0000 |
| 0,01 | 2,0430e+02 | 0,0484 |
| 0,02 | 4,1779e+02 | 0,0952 |
| 0,03 | 5,9803e+02 | 0,1580 |
| 0,05 | 1,0799e+03 | 0,2598 |
| 0,07 | 1,4556e+03 | 0,4098 |
| 0,10 | 2,1065e+03 | 0,5252 |
| 0,15 | 2,9500e+03 | 0,7509 |
| 0,20 | 3,7867e+03 | 1,0910 |
| 0,30 | 5,1506e+03 | 1,2100 |

**Boşluk kontrolü:** mükemmel kafeste `7,255e-12` — sıfır. ✔
**Kalibrasyon:** en bozukta `5,151e+03` — sonda gerçekten **ayırt ediyor**. ✔

### Gerçek yığın

```
uretildi        : N = 3324, aralik = 10,0 m
OTURMADAN once  : a_rms  2,2069e-11    a/olcek 0,0000
oturtuldu       : adim 100, KE 0,000e+00 -> 1,940e-05  (esik 1,545e+04)
OTURDUKTAN sonra: a_rms  3,2749e-06    a/olcek 0,0000
```

### Bağımsız ikinci ölçü — aynı yanıt

Tek bir ölçüye güvenmemek için en yakın komşu mesafesinin **saçılımı** da
alındı ve **aynı** kalibrasyon kafeslerine uygulandı:

| | saçılım |
|---|---|
| kalibrasyon, sarsıntı 0,00 | 2,88e-16 |
| kalibrasyon, sarsıntı 0,02 | 0,0163 |
| kalibrasyon, sarsıntı 0,05 | 0,0419 |
| kalibrasyon, sarsıntı 0,10 | 0,0827 |
| kalibrasyon, sarsıntı 0,20 | 0,1469 |
| **gerçek yığın, ham** | **0,0** |
| **gerçek yığın, oturmuş** | **9,58e-12** |

İki bağımsız ölçü aynı yere işaret ediyor:

> **Bu modeldeki hedef, oturduktan sonra da neredeyse kusursuz bir FCC
> kafesidir. Eşdeğer sarsıntı ~0.**

### Neden — ve bu bir kusur değil

Oturma **hiçbir şey yapmadı**, yapamazdı da. Öz-yerçekimi Dimorphos
ölçeğinde çok zayıftır; ses hızına bağlı CFL adımıyla bir **serbest düşme
süresine** ulaşmak ~10⁷ adım ister. `settling.py` bunu **zaten** biliyor ve
`steps_per_free_fall` ile `simulated_fraction_of_free_fall` alanlarını
raporluyor (ADR-0024); kırmızı takım da `converged`'in **sabit True
olamayacağını** ayrıca sınıyor.

Yani burada yeni bir kusur yok — **var olan dürüstlük** doğru okundu.

---

## 2. E1'in sonucu: KAYIT-020 §5'in yargısı geçerli değil

KAYIT-020 §5 şunu ölçmüştü:

| sarsıntı | 1:1 a_rms | 8:1 a_rms | artış |
|---|---|---|---|
| **0,00** | 6,81e-12 | 1,32e+03 | **∞** |
| 0,02 | 4,04e+02 | 1,32e+03 | 3,26× |
| 0,05 | 1,01e+03 | 1,43e+03 | 1,42× |
| 0,10 | 1,99e+03 | 1,80e+03 | 0,90× |

Ve şu yargıya varmıştı: *"gerçekçi düzensizlik varken arayüz ikinci
mertebeye düşer."*

**E1 diyor ki bu proje modelinin bulunduğu satır en üsttekidir.**

> Arayüz hatası **maskelenmiyor**. Bu modelde **tek başına baskın**
> ayrıklaştırma hatasıdır: taban `1e-15`, arayüz `0,13–0,29`.

KAYIT-020 §5 silinmiyor — ölçüm doğruydu, **koşulu** yanlış varsaymıştım.
Doğru okuma: *"arayüz katkısı, ancak ~%5 konum düzensizliği varsa ikinci
mertebeye düşer — ve bu modelde o düzensizlik **yok**."*

### Yan sonuç: kayalar kütle oranı getirmiyor

Model sınıfı M1/M2'de kayalar farklı `α₀` taşır, yani farklı kütle. Ama:

```
kaya   : ρ = 2700/1,05  = 2571
matris : ρ = 2700/1,160 = 2328        (bulk 2400, f_kaya = 0,30'dan çözülür)
oran   : 2571/2328      = 1,10
```

**%10.** 2:1'in bile çok altında — ihmal edilebilir.

---

## 3. E2 — yapay kuvvet birikiyor mu?

### Düzenek ve nedensel pencere

Düzgün basınçlı küre, serbest yüzeyinden içeri bir **seyrelme dalgası**
gönderir. Dalga varana kadar arayüz halkası **tam durgun** kalmalıdır.

Pencere artık **ölçülen bölgenin kendi dış kenarından** türetiliyor (S5):

```
bolgenin dis kenari r = 34,9 m
NEDENSEL PENCERE (70 − 34,9)/10150 = 3,461 ms = 16 adim
kosulan                             3,279 ms = 16 adim      ICERIDE ✔
```

Her adımda `ρ ≤ 0` sayacı **0**, durum **sonlu** (K21 kontrolü).

### Ölçüm

| adım | t (ms) | 1:1 v_rms | 8:1 v_rms |
|---|---|---|---|
| 1 | 0,2049 | 3,2326e-09 | 2,6919e-01 |
| 2 | 0,4099 | 6,4490e-05 | 5,3369e-01 |
| 4 | 0,8197 | 9,4128e-04 | 1,0348e+00 |
| 8 | 1,6395 | 1,1786e-02 | 1,8684e+00 |
| 12 | 2,4592 | 5,9522e-02 | 2,4078e+00 |
| 16 | 3,2789 | 2,0561e-01 | **2,6261e+00** |

### Birikim yasası

Sabit bir yapay kuvvet `v ~ t¹` verir.

| | üs (tümü) | üs (ilk iki nokta atılınca) | son `v/c` |
|---|---|---|---|
| 1:1 | 5,315 | 3,841 | 2,026e-05 |
| **8:1** | **0,825** | **0,722** | 2,587e-04 |

### Okuma — iki ayrı şey

**(a) 8:1'de hata BİRİKMİYOR, DOYUYOR.** Üs **1'in altında** ve düşüyor.
Sabit kuvvet öngörüsü `a·t = 1316 × 3,28e-3 = 4,32 m/s`; ölçülen **2,63** —
%61'i, ve oran düşüyor. Adım başına artış: `0,269 → 0,265 → … → 0,035`.
Hız ~2,7 m/s'ye doğru **asimptot yapıyor**.

> Parçacıklar çok az yeniden düzenleniyor ve hata **kendini kısmen
> götürüyor**. Bu, arayüzü zamanla dağıtan bir kuvvet **değil**.

**(b) 1:1'de yuvarlama gürültüsünden büyüyen bir kip var.** `3,2e-09`'dan
`0,206`'ya; üs ~4. Sonda mutlak olarak hâlâ **13 kat küçük**, ama **yönü
yukarı**. Pencere bunu ekstrapole etmek için **çok kısa**.

### Söylenemeyecek olan

3,28 ms'lik bir pencereden çarpma süresine (~10²–10³ ms) **ekstrapolasyon
yapılamaz.** Ölçülen şudur ve yalnızca budur:

- 8:1'de yapay hız, pencere içinde **doyar** ve `v/c ≈ 2,6e-4`'te kalır.
- 1:1'de yuvarlamadan büyüyen bir kip vardır ve pencere sonunda hâlâ 13 kat
  küçüktür.

Daha uzun bir ölçüm **serbest yüzeysiz** bir düzenek ister (E2c).

---

## 4. FAZ 4.2 için elde ne var

| bulgu | kaynak | karara etkisi |
|---|---|---|
| arayüz hatası `a/ölçek = 0,13–0,29`, 2:1'den itibaren | KAYIT-020 §3b | A'nın **bedeli** |
| hata **gürültü**, yönlü kuvvet değil (%86–99,5 yönsüz) | KAYIT-020 §2 | arayüzü **itmiyor** |
| hata **mutlak basınçla** ölçekleniyor → `0,21·L/h` | KAYIT-020 §3 | **düzgün** alanlarda göreli olarak kötü |
| model **kusursuz kafes**, eşdeğer sarsıntı ~0 | **E1** | hata **maskelenmiyor**: baskın kaynak |
| kayalar yalnızca **1,10** kütle oranı getiriyor | **E1** | mevcut modelde sorun değil |
| 8:1'de yapay hız **doyuyor** (`t^0,72`) | **E2** | zamanla **dağıtmıyor** |
| momentum korunumu kütle oranından etkilenmiyor (1e-16) | KAYIT-020 §1 | defter bozulmuyor |

### Şu an okunan tablo

A yaklaşımı (ani kütle sıçraması) **bu modelde baskın ayrıklaştırma
hatasını getirir** — ama getirdiği hata **sınırlı** ve **birikmiyor**:
büyüklüğü ~%5 konum düzensizliğinin eşdeğeri, ve zamanla doyuyor.

**Karar hâlâ verilmedi.** Eksik: **E3 — arayüzden şok geçişi.** Buraya
kadarki her ölçüm **yumuşak** bir alanda yapıldı; çarpma probleminin asıl
sorusu arayüzden geçen şoktur ve yansıma/iletim ayrı bir ölçüm ister.

---

## 5. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| vekil kullanma, **aynı sondayı** uygula | §1 — düzensizlik kalibrasyon eğrisine oturtuldu |
| küresel `r` düzensiz cisimde **vekildir** (K14) | §1 — işaretli mesafe |
| aynı büyüklük iki yerde yazılırsa türet (K7) | §1 — `rho_base = m/V_p` |
| tek ölçüye güvenme | §1 — komşu saçılımı **bağımsız** ikinci ölçü |
| boşluk kontrolü + araç kalibrasyonu | §1 — sonda 0'da sıfır, 0,30'da ayırt ediyor |
| ölçümün **geçerlilik penceresini** ölçülen bölgeden türet (S5) | §3 |
| ekstrapolasyon yapma, ölçüleni söyle | §3 "söylenemeyecek olan" |
| yanlış çıkan yargıyı **not düşerek** düzelt, silme | §2 |
