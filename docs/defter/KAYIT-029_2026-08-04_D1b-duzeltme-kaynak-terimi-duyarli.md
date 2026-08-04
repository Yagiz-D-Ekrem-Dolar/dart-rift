# KAYIT-029 — DÜZELTME: kaynak terimi biriktirme yarıçapına **duyarlı** (2026-08-04)

**Kapsam:** FAZ 4.2 · **Durum:** [KAYIT-028](KAYIT-028_2026-08-04_D1-kaynak-terimi-model-form.md)
§3'ün yargısı **geçersiz**; ADR-0041'in gerekçesi zayıfladı
**Öncül:** KAYIT-028, ADR-0041 §5 boşluk 1 ve 2

---

## 0. Ne düzeltiliyor

KAYIT-028 §3 şunu yazmıştı:

> **İyi örneklenen aralıkta gözlenebilir, enerjinin biriktirildiği bölgenin
> yarıçapına neredeyse duyarsız.** Yarıçapı 2,4 kat değiştirmek şok
> yarıçapını yalnızca **1,2 puan** oynatıyor.

**Bu yargı geçersizdir.** Silinmiyor; nedeni yazılıyor.

KAYIT-028'in kendi §4'ü zaten uyarmıştı: *"taranan aralık 0,20–0,48; **DART
çalışma noktası 0,065–0,13**, yani **altında**."* ADR-0041 §5 bunu **boşluk
1** olarak kaydetti. Bu kayıt o boşluğu kapattı — ve yargıyı çevirdi.

---

## 1. D-1b: `n_side = 128`, DART bandına iniş (iş 1451183, 28 dk)

`n = 64`'te `r_dep/r_şok = 0,10`'a inmek enjeksiyon bölgesini **32
parçacığa** düşürüyordu. `n = 128`'de aynı oran **136 parçacıkla** elde
ediliyor — **altı noktanın hepsi iyi örneklenmiş**.

| `r_dep/r_şok` | `n_enj` | `r_ölçülen` | **işaretli hata** | adım |
|---|---|---|---|---|
| **0,1000** | 136 | 0,22389 | **−0,10405** | 2522 |
| 0,1200 | 208 | 0,22585 | −0,09621 | 2087 |
| 0,1601 | 552 | 0,23053 | −0,07750 | 1407 |
| 0,2001 | 1088 | 0,23499 | −0,05966 | 1010 |
| 0,2401 | 1904 | 0,23755 | −0,04940 | 783 |
| 0,3201 | 4632 | 0,24023 | −0,03868 | 526 |

```
BOSLUK KONTROLU tarama ayirt ediyor mu : True
enjeksiyon iyi orneklendi mi           : True  (en az 136)
iyi orneklenen nokta sayisi            : 6/6
iyi rejimde hata araligi               : %3,87 - %10,41   (yayilim 6,54 puan)
```

### Hata **monoton** ve **güçlü**

`n = 64`'te "düz" görünen şey, aralığın yeterince aşağı inmemesiydi.
`n = 128`'de biriktirme yarıçapı 3,2 kat küçülünce hata **2,7 kat** büyüyor.

### Tabanı ayır — geriye **model-form** kalır

ADR-0011 ölçtü ki `h/dx = 2` sabitken `n → ∞` tabanı **~%3,9**. D-1b'nin en
geniş noktası (`0,3201`) **%3,87** veriyor — **taban budur**. Fazlalık:

| `r_dep/r_şok` | toplam hata | **taban üstü fazlalık** |
|---|---|---|
| 0,3201 | %3,87 | **~0** |
| 0,2401 | %4,94 | %1,1 |
| 0,2001 | %5,97 | %2,1 |
| 0,1601 | %7,75 | %3,9 |
| 0,1200 | %9,62 | %5,7 |
| **0,1000** | %10,41 | **%6,5** |

> **DART bandında (`0,065 – 0,13`) biriktirme yarıçapının model-form hatası
> ~%5–7'dir** — KAYIT-028'in bulduğu `≤1,2` puan **değil**.

---

## 2. D-1c: ikinci gözlenebilir de duyarlı (iş 1451261, 69 s)

ADR-0041 §5 boşluk 2 için: Sedov'da β'nın en yakın karşılığı **kinetik enerji
kesridir**. Benzerlik çözümünde (nokta patlaması) `KE/E ≈ 0,28`.

| `r_dep/r_şok` | `n_enj` | `r_hata` | **`KE/E`** | 0,28'den fark |
|---|---|---|---|---|
| 0,1200 | 32 | −0,07112 | 0,12717 | **−%54,6** |
| 0,1601 | 56 | −0,09611 | 0,14459 | −%48,4 |
| 0,2001 | 136 | −0,04028 | 0,17027 | −%39,2 |
| 0,2401 | 208 | −0,04435 | 0,17760 | −%36,6 |
| 0,3201 | 552 | −0,04464 | 0,18168 | −%35,1 |
| 0,4802 | 1904 | −0,03255 | 0,21035 | −%24,9 |

**`KE/E` hiçbir noktada 0,28'e yaklaşmıyor** ve biriktirme yarıçapı
küçüldükçe **düşüyor**: `0,210 → 0,127`. İyi örneklenen rejimde bile göreli
yayılım **%23,5**.

Yani **enerjinin ne kadarının harekete gittiği**, biriktirme yarıçapına
belirgin biçimde bağlı. β momentum-türevi bir büyüklük olduğu için bu
doğrudan ilgilidir.

### Betiğin kendi yargısı yanıltıcıydı — ve düzeltildi

Betik *"kinetik/şok duyarlılık oranı 0,63× → kinetik de duyarsız"* dedi.
**Bu kıyas hatalıydı:** şok yarıçapının **göreli** yayılımı `n = 64`'te
%37,1 görünüyordu çünkü **tabanı küçüktü** (%3,26). `n = 128`'de aynı göreli
yayılım **%169**'a çıkıyor. İki büyüklüğün göreli yayılımlarını kıyaslamak,
tabanları farklıyken **anlamsızdır**.

Doğru okuma: **her iki gözlenebilir de duyarlı**, ve şok yarıçapı daha çok.

---

## 3. KAYIT-028 neden yanıldı — ve ne doğru kaldı

| KAYIT-028'in söylediği | durum |
|---|---|
| ham uydurmanın kirlenmiş olduğu (`n_enj < 100`) | **doğru** — D-1b bunu doğruladı (`n=128`'de hepsi ≥136) |
| eşiğin `20`'den `100`'e çıkarılması gerektiği | **doğru** |
| ~%4 tabanın `h`-sınırlı olduğu | **doğru** — D-1b'nin en geniş noktası %3,87 |
| **"hata biriktirme yarıçapına duyarsız"** | **YANLIŞ** — dar aralığın artefaktıydı |

**Kök neden:** iyi örneklenmiş nokta bulabilmek için aralığı **yukarı**
kaydırmıştım (`0,20–0,48`). O aralıkta hata gerçekten düz görünüyor — çünkü
orada zaten tabana yakın. Duyarlılık **aşağıda** ortaya çıkıyor.

> **Ders:** bir büyüklüğün "duyarsız" olduğunu, ilgilenilen **çalışma
> noktasını içermeyen** bir aralıkta ölçerek söyleyemezsin. KAYIT-028 bu
> sınırı **kendi §4'ünde yazmıştı** — ama yargıyı yine de kurmuştum.

---

## 4. ADR-0041'e etkisi

ADR-0041 **D**'yi önermişti. Gerekçesinin üçüncü maddesi şuydu:

> *"D'nin ölçülen model-form duyarlılığı düşük (§3.6) ve korunumu bozmuyor."*

**Bu madde artık geçerli değil.** Doğrusu:

> D'nin model-form hatası, DART bandında **~%5–7** (şok yarıçapı) ve kinetik
> enerji kesrinde **%24–55** sapma. Duyarlılık **düşük değil.**

Diğer iki madde **ayakta**:

1. **C hâlâ elenmeli** — momentumu sistematik olarak kaybediyor (KAYIT-027).
2. **D hâlâ ADR-0028'in kusurunu ortadan kaldırıyor** — mermi parçacığı yok,
   geri sıçrayacak bir şey de yok.

Ve yeni bir madde ekleniyor:

3. **D'nin biriktirme yarıçapı bir *serbest parametredir* ve sonucu %5–7
   düzeyinde belirler.** Kalibre edilmeden kullanılamaz.

### Öneri değişti mi?

**A′ ile D arasındaki denge D'nin aleyhine kaydı.** A′ momentumu korur ve
model-form hatası **yoktur** (mermiyi gerçekten çözer); bedeli mimaridir ve
arayüz gürültüsü şok geçişinde **ölçülemez** (KAYIT-026).

Ama D'nin kalibre edilebilir olması hâlâ mümkün: biriktirme yarıçapını
**çözülmüş bir referansla** eşleştirmek (küçük ölçekte) bir yol olabilir.
**Bu ölçülmedi.**

> **ADR-0041 zaten `ÖNERİLDİ` durumundaydı ve kilitlenmemişti.** Bu kayıt,
> kilitlememenin **neden doğru olduğunu** gösteriyor.

---

## 5. Sırada

| # | iş | neden |
|---|---|---|
| **D-2** | biriktirme yarıçapını çözülmüş referansla **kalibre et** | D'nin serbest parametresini bağlar |
| **A′-1** | A′'nın mimari iş yükü kestirimi | kararın diğer kefesi ölçülmedi |
| — | boşluk 3 (mukavemetli malzeme) | hâlâ açık |

---

## 6. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| yanlış çıkan yargı **silinmez, not düşülür** | §0, §3 |
| bir sınır **yazıldıysa** yargı ona uymalı | §3 — KAYIT-028 sınırı yazmış ama yargıyı kurmuştu |
| iki büyüklüğün **göreli** yayılımı, tabanları farklıyken kıyaslanmaz | §2 |
| tabanı ayır, **fazlalığı** raporla (K18) | §1 |
| kendi betiğinin yargısı da **denetlenir** | §2 |
