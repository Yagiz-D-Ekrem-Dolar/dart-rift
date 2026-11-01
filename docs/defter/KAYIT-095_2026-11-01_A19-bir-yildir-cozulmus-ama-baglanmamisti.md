# KAYIT-095 — A19 **bir yıldır çözülmüştü** ve kimse bağlamamıştı

**Tarih:** 2026-11-01 · **Sıfır GPU** · **Sıfır TRUBA**
**Öncül:** [KAYIT-094](KAYIT-094_2026-11-01_kesisim-sayisi-olculdu-ADR-0062-tek-yanli-cikti.md)
**Karar:** [ADR-0065](../adr/ADR-0065-krater-derinlik-ureticisi-yan-yana-baglanir.md)
**Kusurlar:** A19 (2026-08-21'den beri açık), A116 1. satır

---

## 1. Tek cümle

A19'un `xfail(strict=True)` sınavları *"düzeltildiği gün düşerler"*
diye yazılmıştı ve bir yıl düşmediler. Sebebi ölçüldü: çare
(`krater_yuzey`) **depoda, sınavlı, ve üretime bağlı değildi**.

## 2. Ölçüm

A19'un iki senaryosu, iki çıkarıcıyla, aynı fikstürle
(`0` GPU, sentetik):

| A19 sınavı | gereken | `crater_profile` (**üretimde bağlı**) | `krater_yuzey` |
|---|---|---|---|
| pürüzlü yüzey, **çarpma yok** | `0` | **`+0,2598`** ✗ | **`+0,0000`** ✓ |
| gerçek `12 m` çukur (`508` kazılmış) | `> 6` | **`−0,0262`** ✗ | **`+6,3170`** ✓ |

`krater_yuzey` ölçümü `h/aralık = 1,5`'te (`h = 4,60`, aralık
`3,068` m). Daha kaba `h`'de derinlik **düşüyor** (`6,20 → +5,71`,
`7,70 → +5,20`) — çekirdek desteği `12 m` çukuru yayıyor. Bu bir kusur
değil, **çözünürlük sınırının kendisi**, ve sınavda üst sınır olarak
yazılı (`d < 12`: ölçülen derinlik gerçek çukurdan derin olamaz).

### 2.1 İlk ölçümüm YANLIŞTI — işareti ters verdim

İlk denememde üç tanım da `+0.0000` verdi ve "demek `krater_yuzey` de
çukuru görmüyor" diye okumaya hazırdım. Tam sıfır olması şüphe
uyandırdı. Fikstür çukuru **`−z`** tarafına açıyor ve testin kendi
yorumu şöyle: *"Mermi `+z` yönünde gidiyor → çarpma cismin `−z`
tarafında."* Ben `impact_direction`'ı `−z` vermiştim, yani operatör
cismin **karşı** tarafına bakıyordu.

> Doğru işaretle `+6,3170` çıktı. Tam `0,0000`'ın üç tanımda da
> tekrarlanması, "ölçüm" değil "yanlış yere bakıyorum" işaretiydi.

## 3. Niçin bir yıl sürdü — A116'nın en pahalı örneği

A116 (2026-10-09) deseni adlandırmıştı: *"yazılmış ama bağlanmamış
modül"*, tablosunun **birinci satırı** `krater_yerdegistirme` →
*"A19'un çaresi"*. Ama A19 kapanmadı, çünkü:

- `xfail`'ler `crater_profile`'ı sınıyordu ve **o çıkarıcı hiç
  değişmedi** — dolayısıyla `xfail`'ler doğru kaldı ve hiçbir alarm
  çalmadı.
- Çare başka bir ada (`krater_yuzey` / `krater_yerdegistirme`) yazıldı
  ve A19'un sınav dosyasına yalnız **tanı** olarak girdi.
- `forward.py:390` hiç dokunulmadı: `crater_profile` → `y[1]`.

> **Ders.** `xfail(strict=True)`, *"düzeltildiği gün düşer"* güvencesi
> verir — ama yalnız **sınadığı çağrı** düzeltilirse. Çare başka bir
> fonksiyona yazılırsa `xfail` sonsuza kadar sessiz kalır ve kusur
> "sabitlenmiş" görünür. `xfail` bir **çivi**dir, alarm değil.

## 4. Yapılan — yan yana bağlama

[ADR-0065](../adr/ADR-0065-krater-derinlik-ureticisi-yan-yana-baglanir.md)
**koddan önce** yazıldı. `gozlenebilirleri_cikar`'a `krater_uretici`
alanı eklendi:

| değer | üretici | durum |
|---|---|---|
| `"profil"` | `crater_profile` | **VARSAYILAN**, bit-aynı, A19'lu |
| `"yuzey"` | `krater_yuzey` | A19'un iki sınavını geçer |

- **Varsayılan bit-aynı:** `43` mevcut ileri-model sınavı geçti
  (ADR-0065 §5 geri alma koşulu).
- **`"yuzey"` yolu `h` ister** ve yoksa **neyin eksik olduğunu
  söyleyerek** reddediyor; `h` yalnız katı çözücünün durumunda var
  (`solver_solid.state_numpy`). Sessiz `KeyError` yerine gerekçeli red.
- **Varsayılan artık sessiz değil:** hangi çıkarıcının kullanıldığı
  `KRATER_URETICI_KUTUGU`'na A19 uyarısıyla yazılıyor. A19'un asıl
  zararı sayının yanlış olması değil, **hangi çıkarıcıdan geldiğinin
  görünmemesi**ydi — KAYIT-088 tam bu yüzden iki ayrı çıkarıcıyı
  karıştırdı.
- **A114'ün kanalı kirletilmedi:** üretici kütüğü ayrı tutuldu, çünkü
  `test_a114_istege_bagli_gozlemli` o kanalda **tam bir** girdi
  bekliyor. Bunu bir sınav olarak çiviledim.

### 4.1 Sınavım bir kez daha yanlış öncülle yazıldı

`test_A114_kanali_KIRLETILMEDI`'yi ilk hâlinde *"A114 kanalı boş
olmalı"* diye yazdım ve **düştü**: bu sentetik sahnede
`crater_profile` haklı olarak reddediyor (*"hiçbir kutuda 5 parçacık
yok"*) ve o `nan` gerekçesi kanalın **asıl işi**. Kod doğruydu, sınav
yanlıştı. Değişmez şu hâle getirildi: *üretici satırı o kanala
sızmasın.*

## 5. A19 niçin **hâlâ açık**

Varsayılan `"profil"` kaldı. Bu bir tercih değil, **kural 6**:
`krater_derinlik` yayımlanmış `y` vektörlerine girdi (`havuz_96.csv`,
`30/96` `nan`); üreticisini sessizce değiştirmek, yayımlanmış bir
gözlenebilirin **tanımını sonradan değiştirmek** olur. Varsayılanın
değişmesi **koşudan önce yazılmış bir protokol** ve **yeni etiket**
ister. A19 o gün kapanır, bugün değil.

## 6. Canlı zararın sınırı — ölçülü

- `krater_derinlik` ADR-0055 ile **isteğe bağlı** ve **posteriora
  girmiyor**; `n_yön = 1` (KAYIT-079) yalnız `β`'ya dayanıyor.
- Mühürlü krater ön kaydı `uretim66`, `havuz_krater_tarama_96.csv`'yi
  yani **`krater_yuzey`'i** kullandı — `crater_profile`'ı **değil**
  (kaydın `krater_olcumu` alanı bunu yazıyor).
- `crater_profile`'ın çıktısı yalnız `havuz_96.csv`'nin
  `krater_derinlik` kolonunda duruyor ve `docs/sonuclar/README.md` §13
  zaten *"bu sütun `havuz_96.csv`'deki `krater_derinlik` DEĞİL"*
  uyarısını taşıyor.

## 7. Kilitli yargılara etkisi — YOK

`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), mühürlü spin ön kaydı (KAYIT-084),
mühürlü krater ön kaydı (KAYIT-092) **etkilenmez**. Hiçbir mühre
dokunulmadı.
