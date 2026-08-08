# KAYIT-039 — Dokuz turluk hata ayıklama: **testlerin kör olduğu** kusurlar (2026-08-08)

**Kapsam:** FAZ 4.4–4.7 kodu · **Durum:** dokuz tur, **dokuz kusur**
**Öncül:** [KAYIT-038](KAYIT-038_2026-08-08_kota-dolunca-kod-yazildi.md)

---

## 0. Neden bu tur gerekliydi

KAYIT-038'de FAZ 4.4–4.7'nin kodu yazıldı ve 136 test geçti. Ama
*"testler geçiyor"* bir güvence değil — 1. turun dersi tam olarak bu:

> Testler *parçaların doğruluğunu* sınıyordu, *bütünün davranışını* değil.

Bu turda yazdığım kodu **testlerden bağımsız** denetledim. Dokuz kusur
çıktı ve **üçü testleri geçiyordu** — yani testler onlara kördü.

---

## 1. Bulunan kusurlar

| # | kusur | testler yakaladı mı | nasıl bulundu |
|---|---|---|---|
| 1 | `prior_width()` **yanlış payda** | **hayır** | bilgisiz posterior ölçüldü |
| 2 | B3 **sözlük sırasına** bağlı | **hayır** | yorum ile kod karşılaştırıldı |
| 3 | kenara çakılma "bilgilendirici" sayılıyordu | **hayır** | uç durum ölçüldü |
| 4 | `judge` doygun cephede **çöküyordu** | hayır (yol sınanmamıştı) | elle senaryo koşuldu |
| 5 | aynı çökme `faz44_bosluk3`'te de vardı | hayır | tüketici taraması |
| 6 | JSON serileştirme sınanmıyordu | — | risk taraması |
| 7 | beş koşucuda **sabit TRUBA yolu** | hayır | tutarlılık taraması |
| 8 | `ileri_kosu` patlamayı **koşu sonunda** anlıyordu | — | GPU maliyeti düşünüldü |
| 9 | UTF-8 koruması **dört koşucuda yoktu** | hayır | gerçekten çöktü |

---

## 2. En öğretici üçü

### 2.1 `prior_width` — hatanın **yönü** önemliydi

`prior_width()` `1,0` döndürüyordu: *"birim küpte önsel bir birim
geniştir."* Ama C2 posteriorun **`%68` aralığını** ölçüyor; onu önselin
**tam genişliğiyle** kıyaslamak elmayla armut kıyaslamak.

Ölçtüm — bilgisiz posterior (`predict ≡ 0`, `n_grid = 200`):

```
width_u        = [0.68342 0.68342 0.68342]
prior_width()  = [1.0     1.0     1.0    ]
```

Düzgün dağılımın `16–84` yüzdelikleri arası **tam `0,68`**'dir.

> **Hatanın yönü:** eski payda C2'yi **belgede yazandan zayıf**
> yapıyordu. Bilgisiz bir posterior `0,683` ile eşiğe (`0,50`) `%37`
> yaklaşıyordu; oysa `%100` uzak olmalıydı.

Düzeltildikten sonra kuru kipte C2 `0,142 → 0,208` **sıkılaştı** ve hâlâ
geçiyor. Yani düzeltme ölçütü güçlendirdi, sonucu bozmadı.

### 2.2 Kenara çakılma — KAYIT-030'un hata sınıfı

Gerçek değer önsel aralığın **dışındaysa** posterior sınıra dayanır ve
**çok dar** bir bant üretir — yani *"son derece bilgilendirici"* görünür.
Doğru okuma tam tersi: **parametre aralığı yanlış seçilmiş**.

Ölçtüm (`n_grid = 100`, `σ = 0,02`):

| gerçek `u` | mod bini | kenarda mı | `%68` genişlik |
|---|---|---|---|
| 0,50 | 49 | hayır | 0,03955 |
| 0,90 | 89 | hayır | 0,04059 |
| 0,98 | 97 | hayır | 0,03545 |
| **1,00** | **99** | **evet** | 0,02624 |
| **1,50** | **99** | **evet** | **0,00687** |
| **−0,30** | **0** | **evet** | **0,00000** |

> **Genişliğin dışarı çıkıldıkça daralması** sahte kesinliğin imzasıdır.

Ayrım keskin ve **parametresiz**: mod en dış kutuda mı? Çakılı eksen
artık C2'yi geçiremiyor ve C3'ün eksen seçiminden de dışlanıyor. Pozitif
kontrol de var: korumanın **meşru** dar bantları engellemediği ayrıca
sınanıyor.

### 2.3 Sözleşme değişti, tüketiciler denetlenmedi

Cephe ölçümünü ölümcül olmaktan çıkarırken (doygunsa `None` dönsün diye)
`judge`'ı güncellemeyi unuttum:

```
TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'
```

Üstelik **tam da düzeltmenin hedeflediği durumda**: gözenekli kolda cephe
kutu kenarına varıyor, `_kos` `None` yazıyor ve `judge` çöküyordu. Yani
*"None döndürelim ki koşu devam etsin"* düzeltmesi, koşunun bir sonraki
adımında patlamasına yol açıyordu.

> **Ders:** bir fonksiyonun dönüş **sözleşmesi** değiştiğinde, o dönüşü
> **tüketen her yer** denetlenmeli.

Bu dersi hemen uyguladım ve sistematik tarama yaptım — aynı kök neden
`scripts/faz44_bosluk3.py`'de **iki yerde daha** vardı.

---

## 3. Kota, hata ayıklamanın **yönünü** belirledi

TRUBA kotası dolu (`7.200.096 / 7.200.000 cpu-dk`; iş **1460742**
kuyrukta). GPU zamanı en kıt kaynak olduğu için iki düzeltme doğrudan
**israfı** hedefledi:

- **Erken iptal**: `ileri_kosu` patlamayı koşu **sonunda** anlıyordu.
  3000 adımın 100.'sünde patlarsa 2900 adım boşa gidiyordu. Artık
  `steps/30`'da bir sınanıyor.
- **Sabit yollar**: iş nihayet koştuğunda bir yol hatasıyla düşmesi
  12 saatlik pencereyi yakar. Beş koşucudaki sabit TRUBA yolu
  `__file__`'dan türetmeye çevrildi.
- **JSON**: 12 saatlik bir koşunun **sonunda** serileştirme patlarsa her
  şey kaybolur. Dört test eklendi.

---

## 4. Zayıf testleri **zayıf** diye işaretledim

Erken iptal ve tasarım-tamamen-düştü korumaları GPU gerektirdiği için
**koşulamıyor**. Testleri kaynak metni sınıyor:

```python
assert "ERKEN IPTAL" in kaynak
```

Bu zayıf bir testtir ve docstring'inde öyle yazılı. Hiç olmamasından iyi
— niyeti kayda geçiriyor — ama **doğrulama değildir**.

---

## 5. Sayılar

| büyüklük | değer |
|---|---|
| tur sayısı | 9 |
| bulunan kusur | 9 (+3 tutarlılık) |
| **testlerin kör olduğu kusur** | **3** |
| eklenen gerileme testi | 24 |
| yerel test takımı | **912 geçti, 96 atlandı** (öncesi 898) |

---

## 6. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| *"testler geçiyor"* bir güvence **değildir** | §0 |
| bir hatanın **yönü** ayrıca yazılır | §2.1 |
| ölçütün **gücü** varsa **zayıflığı** da ölçülür | §2.1, §2.2 |
| dönüş sözleşmesi değiştiyse **tüketiciler taranır** | §2.3 |
| bir koruma **meşru** durumu engellememeli — pozitif kontrol | §2.2 |
| zayıf test **zayıf** diye işaretlenir | §4 |
| kıt kaynak, hata ayıklamanın **yönünü** belirler | §3 |
