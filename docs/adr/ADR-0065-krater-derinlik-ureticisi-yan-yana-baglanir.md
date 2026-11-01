# ADR-0065 — `krater_derinlik`'in üreticisi **yan yana** bağlanır; varsayılan bit-aynı

**Tarih:** 2026-11-01 · **Durum:** kabul (yan yana alan; varsayılan **bit-aynı**)
**Kapattığı kusurlar:** [A19](../FAZ4-SIKINTI-RAPORU.md) (2026-08-21'den beri açık),
[A116](../FAZ4-SIKINTI-RAPORU.md) 1. satır
**Öncül:** [ADR-0055](ADR-0055-gozlemli-vektoru-ve-krater-kutusu.md),
[ADR-0061](ADR-0061-krater-penceresi-durum-basina-kurulur.md),
[ADR-0062](ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md),
[ADR-0063](ADR-0063-yuzey-icten-disa-taranir.md),
[ADR-0064](ADR-0064-yuzey-referansa-en-yakin-kesisimdir.md)
**Kayıt:** [KAYIT-095](../defter/KAYIT-095_2026-11-01_A19-cozulmus-ama-baglanmamisti.md)

---

## 1. Bağlam — çare bir yıl önce yazıldı, **bağlanmadı**

A19 (2026-08-21) şunu ölçmüştü: krater çıkarıcısı **yokken var, varken
yok** diyor. İki sınav `xfail(strict=True)` ile çivilenmişti ve
*"düzeltildiği gün düşerler"* diye yazılmıştı. Bir yıl düşmediler.

A116 (2026-10-09) aynı şeyi desen olarak adlandırdı: *"yazılmış ama
bağlanmamış modül"*, ve tablosunun **birinci satırı**
`krater_yerdegistirme` → *"A19'un çaresi"*.

Bugün ölçüldü (`2026-11-01`, sentetik, `0` GPU): çare **zaten
üretimde değil ama depoda** — A73'ün yüzey operatörü `krater_yuzey`
A19'un **iki** sınavını da geçiyor.

| A19 sınavı | olması gereken | `crater_profile` (**üretimde bağlı olan**) | `krater_yuzey` |
|---|---|---|---|
| pürüzlü yüzey, **çarpma yok** | `0` | **`+0,2598`** ✗ | **`+0,0000`** ✓ |
| gerçek `12 m` çukur (`508` kazılmış parçacık) | `> 6` | **`−0,0262`** ✗ | **`+6,3170`** ✓ |

`krater_yuzey` ölçümü `h/aralık = 1,5`'te yapıldı (`h = 4,60`,
aralık `3,068 m`). Daha kaba `h`'de derinlik düşüyor
(`6,20 → +5,71`, `7,70 → +5,20`) — çekirdek desteği `12 m` çukuru
yayıyor, **beklenen** çözünürlük davranışı.

**Üretimde bağlı olan hangisi:** `inference/forward.py:390`
`crater_profile`'ı çağırıyor ve sonucu `y[1] = krater_derinlik` olarak
gözlenebilir vektörüne koyuyor (`:423`). Yani **A19'lu çıkarıcı
üretimdeki gözlenebiliri üretiyor.**

## 2. Ne kadar zarar verdi — sınırı yazılı

- `krater_derinlik` **ADR-0055 ile isteğe bağlı** ve **posteriora
  girmiyor**; `n_yön = 1` yargısı (KAYIT-079) yalnız `β`'ya dayanıyor.
- Mühürlü krater ön kaydı `uretim66` **`havuz_krater_tarama_96.csv`**'yi
  kullandı, yani `krater_yuzey`'i — `crater_profile`'ı **değil**.
  (`ONKAYIT_HERA_KRATER_uretim66.json`, `krater_olcumu` alanı.)
- `crater_profile`'ın çıktısı yalnız `havuz_96.csv`'nin
  `krater_derinlik` kolonunda duruyor (`30/96` `nan`) ve
  `docs/sonuclar/README.md` §13 zaten *"bu sütun `havuz_96.csv`'deki
  `krater_derinlik` DEĞİL"* uyarısını taşıyor.

Yani canlı zarar **sınırlı ve sınırı ölçülü**. Ama gözlenebilir vektörü
yayımlanmış bir çıktıdır ve üreticisi kanıtlanmış biçimde bozuktur.

## 3. Karar

### 3.1 `krater_uretici` alanı — yan yana, varsayılan bit-aynı

`gozlem_vektoru` yeni bir alan alır:

| değer | üretici | durum |
|---|---|---|
| `"profil"` | `crater_profile` | **VARSAYILAN**, bit-aynı, A19'lu |
| `"yuzey"` | `krater_yuzey` (ADR-0061/62/63/64) | A19'un iki sınavını geçer |

**Varsayılan `"profil"` kalır.** Sebebi bir tercih değil, kural 6:
`krater_derinlik` yayımlanmış `y` vektörlerine girdi; üreticisini
sessizce değiştirmek, yayımlanmış bir gözlenebilirin tanımını sonradan
değiştirmek olur. Değişiklik ancak **koşudan önce yazılmış bir
protokolle** ve **yeni etiketle** yapılır.

### 3.2 Ama varsayılan artık **sessiz değil**

`"profil"` seçildiğinde `fizik_tani["krater_uretici"]` alanına
üreticinin adı **ve** A19 uyarısı yazılır. Bir sonraki okuyan, sayının
hangi çıkarıcıdan geldiğini kütükten görür. A19'un asıl zararı sayının
yanlış olması değil, **hangi çıkarıcıdan geldiğinin görünmemesi**ydi
(KAYIT-088'in iki çıkarıcıyı karıştırması bunun kanıtı).

### 3.3 A19'un `xfail`'leri **kalır**

İki `xfail(strict=True)` `crater_profile`'ı sınıyor ve o çıkarıcı
**değişmedi** — hâlâ düşüyor, dolayısıyla `xfail` hâlâ doğru. Silinmez
(kural 5). Yanına, aynı iki senaryonun `krater_yuzey` ile **geçtiğini**
gösteren sınavlar eklenir. İki çıkarıcının farkı böylece **sınavlı**
olur.

## 4. Reddedilen seçenekler

| seçenek | niçin reddedildi |
|---|---|
| Varsayılanı `"yuzey"` yapmak | yayımlanmış `y` vektörünün tanımını sessizce değiştirir; kural 6 |
| `crater_profile`'ı silmek | "hiçbir satır silinmez" (kural 5); ayrıca `scene_checks` ve altı betik onu çağırıyor |
| A19'un `xfail`'lerini kaldırmak | `crater_profile` düzelmedi; kaldırmak kusuru gizlemek olur |
| `krater_yerdegistirme`'yi bağlamak | A116'nın işaret ettiği çare o, ama `krater_yuzey` A19'un **iki** sınavını da geçiyor ve zaten ADR-0061/62/63/64 zincirinin sınavlı ucu |
| `havuz_96.csv`'yi yeniden üretmek | kural 6; gerekirse yeni etiket |

## 5. Geri alma koşulu

`krater_uretici="profil"` ile üretilen `y` vektörü, bu ADR'den önceki
koda göre **bit-aynı** olmalıdır. Olmazsa alan geri alınır ve sebep
KAYIT'a yazılır.

## 6. Etkilenmeyen yargılar

`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), mühürlü spin ön kaydı (KAYIT-084),
mühürlü krater ön kaydı (`uretim66`, KAYIT-092) **etkilenmez**.
