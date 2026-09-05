# İki günlük plan — bilimsel sonuca giden en kısa yol

**Yazıldı:** 2026-09-06 · **Hedef:** ölçülmüş, savunulabilir pozitif sonuç

---

## Neden bu plan

Uzman incelemesi beş kablolama kusuru ortaya çıkardı (A46 – A50) ve
en önemlisi şu: **çıkarımın üç ekseninden ikisi sahneye hiç
ulaşmıyordu.** Yani depoda *"gözlenebilir iç yapıyı ayırt edemiyor"*
diye bir bulgu **yok** — yalnız bozuk bir düzenek vardı.

Ve A53 ölçtü: kazı akışı kodun içinde **var**; üretim yapay
viskozitesinde sönümleniyor.

| kol | `M_kaçan` | `⟨v⟩` |
|---|---:|---:|
| `α_av = 1,0` (üretim) | `93 kg` | `−1264 m/s` ← jet |
| `α_av = 0,1` | `12 303 kg` | `−0,397 m/s` ← **kazı akışı** |

Bu ikisi birlikte, kapanmış sanılan iki kapıyı yeniden açıyor.

## Yapmadığım şey — ve nedeni

**A52'yi çözmeye kalkışmıyorum.** Komşu arama yarıçapı her parçacık
için `2·h_max`; kök sebep `h_ij = (h_i+h_j)/2` — ince parçacık kaba
komşusunu `14 m` öteden aramak zorunda. Bu bir veri yapısı değil,
**çekirdek tasarımı** sorunu (uzmanın 12. maddesi de oraya işaret
ediyor). İki günde bit-eşitliği ve determinizm korunarak çözülmez.

Bedeli kabul ediliyor ve **kayıtlı**: üç noktalı Richardson bu turda
yok, `E3i` (ince AV kolu) kurulamıyor.

---

## Zincir

```
E (mekanizma)  ->  F (AV x cozunurluk)  ->  G (ayirt edilebilirlik)
   3-4 saat            ~1,5 saat              ~40 dakika
```

### E — hangi kuvvet kazıyı durduruyor

| kol | sınadığı | protokol |
|---|---|---|
| `E1a` / `E1b` | şok gerçekten oluşuyor mu (`--alpha-donuk`) | `PROTOKOL-E1-ERKEN.md` v2 |
| `E2a` / `E2b` | matris çekmesi (`--matris-cekme-yok`) | `PROTOKOL-E2-CEKME.md` |
| `E3` / `E3o` | yapay viskozite taraması | `PROTOKOL-E2-CEKME.md` eki |

E1'in gerekçesi A45: şok mermiyi `6,0e-5 s`'te geçiyor (`≈ 11` adım),
iz aralığı `2 000` adımdı — **depodaki hiçbir ölçüm canlı şoku
görmedi.**

E2'nin gerekçesi A51: `Y₀` sekiz mertebe değişirken EOS çekme basıncı
`−1,518635e+07 Pa`'da **yedi haneye kadar aynı**.

### F — AV etkisi çözünürlükte yaşıyor mu

`3` AV değeri × `2` çözünürlük. A53'ün açık sorusu tek: kaçan `33`
parçacığın hepsi kaba seviyedendi, bu artefakt mı?

Doğru sınav bir kademe ince merdivendi; A52 yüzünden `107` saat
sürerdi. Bunun yerine **mevcut iki ölçekte** tekrarlanıyor. Mekanizma
ikisinde de duruyorsa çözünürlük-dirençli bir iddia olur — tam
yakınsama değil, ama boş da değil.

### G — **asıl hedef**

Aynı `24` nokta, **iki sahne gerçeklemesi**, kaba merdiven, F'nin
kazanan AV'si.

```
F = Var(theta'lar arasi) / ortalama(gerceklemeler arasi)
```

Yargı `F > 4` **ve** en az bir `θ` bileşeniyle `|ρ| > 0,5`
(`p < 0,05`). Eşikler `scripts/ayirt_raporu.py`'de **kilitli** ve
`test_ayirt_raporu.py` onları protokolle karşılaştırıyor.

**Ön işaret iyi:** üretim ölçeğinde ölçüldü —

| | blok parçacığı | matris `α₀` |
|---|---:|---:|
| `θ = (1,05 ; 0,10)` | `1 109` | `1,5896` |
| `θ = (1,30 ; 0,40)` | `3 448` | `1,6430` |
| aynı `θ`, tohum `999` | `1 055` | `1,5844` |

`θ` etkisi gerçekleme gürültüsünden **~44 kat** büyük. Gözlenebilir
sahne yapısına *herhangi* bir duyarlılık gösteriyorsa `F` büyük çıkar.

---

## Risk ve karşılığı

| risk | karşılık |
|---|---|
| Kaba ölçekte gözlenebilir hiç var olmuyor (`Rb_R1`: `n_kaçan = 0`) | F'nin `F_kaba_av01` kolu tam bunu sınıyor. Var olmazsa G, `β` yerine **krater derinliği** üzerinden koşar — o `R1`'de `0,53 m` ile mevcut ve Hera'nın doğrudan ölçeceği nicelik. |
| E'nin üç adayı da düşer | Elde ölçülmüş bir **eleme** kalır; dördüncü aday `h_ij` (uzmanın 12. maddesi). |
| F "eşikli" der (artefakt) | AV aday olmaktan çıkar, G üretim AV'siyle ve krater derinliğiyle koşar. |

## Bu planın kanıtlamadığı

Uzamsal yakınsamayı kanıtlamıyor — `R` kampanyası düştü
(`docs/SONUC-R-YAKINSAMA.md`) ve A52 çözülmeden düzelmiyor. G'nin
sonucu *"düzeltilmiş düzenekte ve akışın var olduğu ayarda,
gözlenebilir `θ` hakkında bilgi taşıyor mu"* sorusunun yanıtıdır.

Daha fazlası değil — ve daha azı da değil.
