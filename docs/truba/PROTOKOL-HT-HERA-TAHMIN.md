# Protokol HT — kilitli Hera krater tahmini (ön kayıt)

**Yazıldı:** 2026-09-14, **tahmin üretilmeden ÖNCE**. Kural
`scripts/hera_tahmin.py`'de; sınavı `tests/test_hera_tahmin.py`.

## 1. Amaç (Faz 6)

Şartname Faz 6: *kilitli Hera tahmini, ön kayıt*. Hera DART kraterini
görüntülemeden önce, modelin krater öngörüsü değiştirilemez biçimde
kaydedilir; Hera verisi geldiğinde öngörü **kayda dokunmadan** sınanır.

## 2. Ağırlıklar

Protokol D ile aynı `β` gözlemi, vekil ve kapsama kuralı:

- **ÖNSEL İÇİNDE** → posterior ağırlık; kayıt `POSTERIOR`.
- **ÖNSEL DIŞI** → düzgün önsel; kayıt **`KOSULSUZ`** ve kapsama yargısı
  kaydın içinde. Bu durumda tahmin iç yapı çıkarımına **dayanmaz**.

## 3. Öngörü

Gözlenebilirler: `R_krater` (m), `V_krater` (m³), `M_ejekta` (kg), P'nin
dönüşümleriyle. Her biri için ikinci derece vekil, θ-gruplu 4-kat artık
sapması ve (varsa) Mt çözünürlük terimi. `20 000` örnek, tohum `20260914`;
kantiller `q05`–`q95` (5/16/50/84/95) doğal birimde.

## 4. Kayıt

`ONKAYIT_HERA_<etiket>.json`: tahmin + meta (koşul, kapsama, gözlem, havuz
deseni, koşu sayısı, `t_end`, çözünürlük terimleri, git commit, UTC zaman)
ve içeriğin **SHA-256**'sı. Aynı adla ikinci kayıt **üzerine yazılmaz**
(hata). Kayıt depoya commit'lenir; commit tarihi zaman damgasının ikinci
kanıtıdır.

## 5. Uyarı — kaydın parçası

Model krateri `t_end` (0,1 s ya da 24 ms) anındaki krater; Hera'nın
ölçeceği **son krater değil**: düşük yerçekiminde krater oluşumu çok daha
uzun sürer ve model yerçekimsiz. Bu kayıt bir **mekanizma ön kaydıdır**;
Hera karşılaştırması ancak uzun zaman/yerçekimli bir ileri modelle bilimsel
anlam kazanır ve bu sınırlama karşılaştırma raporuna aynen taşınır.

## 6. Üretilecek kayıtlar

| etiket | havuz | koşul |
|---|---|---|
| `Qo` | Q3 orta 0,1 s + Mt orta çözünürlük terimi | Q §4 esas olabilir |
| `i72` | ince-72, 24 ms | betimleyici |

## 7. Hera geldiğinde (kilitli)

Ölçülen değerin öngörü dağılımındaki kantili yazılır; `q05`–`q95`
dışında → **TUTARSIZ**, içinde → **TUTARLI**. §5 uyarısı yargının yanında
yazılır.
