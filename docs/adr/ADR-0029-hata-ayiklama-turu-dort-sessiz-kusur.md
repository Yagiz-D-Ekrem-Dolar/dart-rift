# ADR-0029 — Hata ayıklama turu: dört sessiz kusur ve ortak kök nedeni

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-02
- **Bağlam:** FAZ 3 "0 hata" iddiası reddedildi; aktif hata ayıklama istendi
- **İlgili:** ADR-0025 (makineler arası determinizm), ADR-0027 (Grady-Kipp hasar),
  `docs/EKSIKLER.md`, RT9, RT10, G3 C5

## Neden bu ADR var

FAZ 3 "tamamlandı, 0 hata" diye sunulmuştu: 627 test geçiyordu, G3 kapısı 7/7,
14 kırmızı-takım maddesi temizdi. Bu sunum reddedildi ve **aktif hata ayıklama**
istendi. Tur dört kusur buldu; ikisi bilimsel sonucu birinci mertebede
bozuyordu.

Kayıt bu ADR'de duruyor çünkü asıl mesele tek tek kusurlar değil, **hepsinin
aynı kör noktadan gelmesi**: testler *parçaların doğruluğunu* sınıyordu,
*bütünün davranışını* değil.

## Kusur 1 — Hasar, durum değişkenini bozuyordu (ŞİDDETLİ)

`apply_damage_k` gerilmeyi **yerinde** çarpıyordu:

```
S[i] = f * S[i]          # f = 1 - D
```

`S` bir **durum** değişkenidir: `kick_S_3d` ile integre edilir, hiçbir yerde
yeniden hesaplanmaz. `_eval()` ise KDK adımı başına **iki kez** çağrılır.
Sonuç: her adımda `S <- (1-D)^2 S`, birikimli.

Ölçüldü (TRUBA iş 1446269, H100; `D = 0.5` sabit tutuldu, hiçbir fiziksel
evrim yok):

| | S[0,0,1] |
|---|---|
| başlangıç | 1,000000e+07 |
| 1./2./3./4. `_eval()` | 5,0e+06 / 2,5e+06 / 1,25e+06 / 6,25e+05 |
| 5 adım sonra | **4,88e+03** (olması gereken 5,0e+06) |

**1000 kat sapma.** Deviatorik gerilme, hasar büyümesinden bağımsız olarak üstel
sönümleniyordu. `P` kurtuluyordu çünkü EOS onu her `_eval()`'de yeniden
hesaplıyor; `S` hesaplamıyor.

### Neden hiçbir test görmedi

Hasarın bütün testleri şunu soruyordu: *"hasar sonucu değiştiriyor mu?"*
Değiştiriyordu — ama yanlış nedenle. Formül testlerinin (asal gerilme, kusur
sayımı, hız, uygulama) hepsi doğruydu; **hiçbir formül yanlış değildi**.

### Karar

Hasar **ayrı** `P_eff`/`S_eff` dizilerine yazar; durumu okur, yazmaz.
Kuvvetler taşınan gerilmeyi görür, `kick_S_3d` ham `S`'yi evrimler. Hasar
kapalıyken ek dizi yok, ek maliyet yok.

Düzeltme sonrası ölçüm (aynı kurulum): S **1,000000e+07 sabit**, `S_eff`
her `_eval()`'de tam **5,000000e+06**.

### Yapısal önlem (kusurun sınıfını kapatır)

`tests/test_solver_idempotence.py`: **alan değerlendirmesi saf bir
fonksiyondur.** İki ardışık `_eval()` sonrası bütün durum dizileri bit
düzeyinde aynı kalmalı. Bu, hasara özgü değil; aynı sınıftan gelecek her
kusuru yakalar.

`cpu_reference/solid_ref.py` içinde artık hasar **döngüsü** de var
(`seed_solid_damage`, `_accumulate_damage`, `P_eff`/`S_eff`), ve
`TestDamageCross` GPU ile CPU'yu 10 adım boyunca karşılaştırıyor. Projedeki
her fizik modülünün bir CPU referans adımı vardı; **hasarın yoktu** — kusurun
tam olarak yaşadığı boşluk buydu.

## Kusur 2 — Krater çıkarıcı cismi küre sanıyordu (ŞİDDETLİ)

Modülün kendi belgesi şöyle diyordu:

> "theta > theta_dış olan yüzey parçacıklarıyla bir REFERANS yarıçap profili
> R_ref(theta) uydurulur"

Kod ise referansı **tek bir sayı** alıyordu: `prof_ref = np.full(n_bins,
r_ref_global)`. Yani cismi küre kabul ediyordu. **Dimorphos küre değil:
88 × 87 × 65 m, eksenler arası %26 fark.**

Ölçüldü — **kratersiz** bir Dimorphos elipsoidinde (doğru cevap 0 m):

| çarpma ekseni | derinlik | çap |
|---|---|---|
| kısa (z) | **9,04 m** | 66,76 m |
| uzun (x) | 1,46 m | 0,00 m |

Cismin yarıçapı zaten kendiliğinden ~11,5 m oynuyor; "krater" oradan
geliyordu. Bilinen 8 m'lik çukur kazılınca da **17,43 m** raporlanıyordu —
iki kat şişirme. Bu, DART'ın gerçek krater ölçüsüyle **aynı mertebede** bir
hata.

### Karar

Referans, cismin **kendi çarpma öncesi şeklidir**. `x_reference` verilirse
`R_0(theta)` aynı kutulama ve aynı eksenle ölçülür; çarpma dışı bölgede
ölçülen küresel ölçek kayması referansa eklenir (böylece global büzüşme
kraterden düşer — modülün asıl amacı). Verilmezse eski davranış sürer ama
`reference_is_spherical` tanısı **açıkça** `True` döner.

Düzeltme sonrası: kratersiz elipsoit **9,04 → 0,000 m**; bilinen 8 m'lik
çukur **17,43 → 8,66-9,04 m**.

Kalan %8-13 fazlalık yeni bir kusur değil: `surface_particles`in bilinen
örneklem yanlılığı (yüzey = kutudaki en uzak parçacık, gerçek yüzeyin biraz
içinde; krater tabanında kutu başına örnek referans bölgesinden az). Aynı
etki küre testinde de türetilmişti (20 m → 21,1 m, +%5,5).

### Neden hiçbir test görmedi

Krater çıkarıcının **bütün** sınavları küre üzerindeydi: bilinen kalot,
küresel büzüşme (RT9), az örneklenen kutular. RT9'un adı "küresel deformasyon
krater sayılıyor mu" ama izotropik büzüşme referansa zaten girer; asıl tehlike
cismin kendi şekliydi ve o hiç sınanmamıştı.

## Kusur 3 — Duyarlılık taramasının hız ekseni tamamen ölüydü

P3-VR-03 beta'yı kontrol yüzeyi **ve** hız eşiği üzerinde tarar. Eksen başına
ölçülünce:

```
beta_spread_radius_axis = 0,2189
beta_spread_speed_axis  = 0,0000     <-- TAM SIFIR
```

Sebep: o senaryoda kaçış hızı 0,0803 m/s, en yavaş ejekta 0,2 m/s; en yüksek
eşik (2×) 0,161 m/s bile hiçbir parçacığı eleyemiyor. **Toplam yayılım pozitif
olduğu için G3 C5 ve RT10 geçiyordu** — hız eşiği kod yolu hiç koşulmadan.
RT12 ile aynı sınıf: doğru sonuç, yanlış sebep.

### Karar

`beta_sensitivity` artık **eksen başına** yayılım ve `*_axis_active` raporlar.
`run_speed_threshold_selftest` hızları kaçış hızının etrafına yayar; ölçüldü:
hız ekseni yayılımı 0,3209, beta eşikle **monoton** azalıyor
1,735 → 1,633 → 1,414, ejekta sayısı 2265 → 1535 → 748. G3 C5 ve RT10 artık
her iki eksenin de iş gördüğünü ayrı ayrı şart koşuyor.

## Kusur 4 — Varsayılan hedef yarıçapı %21 küçüktü

`momentum_transfer` içinde `median(dist)` doğrudan yarıçap sayılıyordu. Düzgün
**dolu** bir kürede medyan uzaklık R değil `R/2^(1/3) = 0,794 R`'dir.
Ölçüldü (300k parçacık, R = 100 m):

```
median(dist) = 79,294 m       (kuramsal 79,370)
v_kaçış      = %12,3 BÜYÜK    (v ~ 1/sqrt(R))
r_kontrol    = 1,59 R         (2,00 R sanılıyordu)
```

Üçü de ejekta ölçütünü sıkılaştırır ve beta'yı sessizce kaydırır. Kusur
görünmez kalmıştı çünkü **gerçek çağıranların hepsi `target_radius` veriyor**;
varsayılan yol hiç koşulmuyordu — kod bir tuzak olarak bekliyordu.

### Karar

`estimate_target_radius()` (medyan × 2^(1/3)), varsayımı açık, aykırı ejektaya
dayanıklı (RMS yarıçap değil — birkaç uzak parçacık onu şişirir).
`target_radius_estimated` tanısı eklendi.

## Ölçülüp DEĞİŞTİRİLMEYENLER

Bunlar da tur sırasında sınandı; kayıt, yeniden tartışılmaması için.

| konu | ölçüm | karar |
|---|---|---|
| Uslu yasa uydurmasının yanlılığı | N=200: −%3,3; N=2000: −%0,67; N=20000: +%0,11 (kapı toleransı %10) | değiştirilmedi; kuyruk kırpmak N=2000'de −%0,19 veriyor ama gerekmiyor |
| `momentum_transfer` toplamları `np.sum` (fsum değil) | sıralar arası bağıl fark ~1e-15; `beta_recovery_rel_err` toleransı 1e-6 | değiştirilmedi — mertebe farkı 9 basamak |
| Krater kenarı: "en dış" vs "bitişik" kural | kürede %3 yüzey pürüzlülüğüyle bile ayrışmadı | yine de bitişiklik şartı eklendi (düzensiz cisimde ayrışabilir) |

## Ortak kök neden

Dördü de aynı boşluktan geldi: **testler parçaların doğruluğunu sınıyordu,
bütünün davranışını değil.**

- Hasarın formülleri doğruydu; **döngüsü** sınanmamıştı.
- Krater çıkarıcı kürede doğruydu; **hedefin gerçek şekli** sınanmamıştı.
- Tarama iki eksenli görünüyordu; **eksenlerin iş görüp görmediği** sınanmamıştı.
- Yarıçap kestirimi vardı; **varsayılan yol** hiç koşulmamıştı.

Bunun genellenebilir dersi: *bir kriter geçtiğinde, geçme SEBEBİNİN
ölçülmüş olması gerekir.* "Sonuç değişti", "yayılım pozitif", "derinlik
makul" — hepsi doğru sebeple de yanlış sebeple de sağlanabilir.

Bu yüzden bu turda eklenen her kriter, **neyin iş gördüğünü** ayrı ayrı
raporluyor: `radius_axis_active`, `speed_axis_active`,
`reference_is_spherical`, `target_radius_estimated`, ve `_eval()` saflık
değişmezi.

## Sonuç

"0 hata" iddiası yanlıştı ve **not düşülerek düzeltildi, silinmedi**
(RULES.txt). FAZ 3 kod tabanı bu dört düzeltmeden sonra yeniden kapıya
sokuldu.
