# KAYIT-040 — A′, FAZ 5 ensemble'ını **mümkün kılan** şey (2026-08-08)

**Kapsam:** FAZ 4 → 5 geçişi · **Durum:** hesaplandı (ölçülen girdilerle)
**Öncül:** [FIZIBILITE.md](../FIZIBILITE.md) §1 ve §2b,
[KAYIT-038](KAYIT-038_2026-08-08_kota-dolunca-kod-yazildi.md)

---

## 0. Neden yeniden hesaplandı

`FIZIBILITE.md` §1 şöyle bitiyordu:

> *"1 saniyelik koşularla ensemble fizibil. 10 saniyelik koşularla
> sınırda."*

O hesap **tekdüze** bir sahnede yapıldı. Sonra iki şey oldu:

1. **ADR-0026** ölçtü ki tekdüze kaba sahnede **mermi çözülmüyor** —
   yani o hesabın dayandığı kurulum **kullanılamaz**.
2. **A′** (ADR-0041) ölçüldü ve DART geometrisinde `6,87×` parçacık
   tasarrufu veriyor (KAYIT-038).

> Maliyet parçacık sayısıyla neredeyse doğrusal olduğu için **hesap
> değişti.** Ve değişen yön belirleyici.

---

## 1. Hesap — girdilerin hepsi **ölçülmüş**

| büyüklük | değer | kaynak |
|---|---|---|
| adım maliyeti (**tam fizik**) | `8 658 µs/1000 parçacık` | FIZIBILITE §2b, iş 1429628 |
| A′ parçacık sayısı | `11 164` | KAYIT-038 |
| tekdüze ince | `76 722` | aynı |
| tekdüze kaba | `10 347` | aynı |
| `dt` (kaba) | `6,9e-5 s` | FIZIBILITE §1 |

### `dt` cezası **hesaba katıldı**

CFL `h`'ye bağlı; A′'nın ince bölgesinde `h` yarıya iniyor ⇒ `dt` de
yarıya. Bu tasarrufun bir kısmını **geri alır**.

> Atlanırsa A′ olduğundan **ucuz** görünürdü. Ayrı bir test bunu
> sınıyor ve bedelin büyük kısmının `dt`'den geldiğini gösteriyor.

---

## 2. Sonuç (300 koşu, GPU-günü)

| `t_sim` | tekdüze kaba | **A′** | tekdüze ince | kazanç |
|---|---|---|---|---|
| 0,1 s | 0,45 | **0,97** | 6,69 | 6,87× |
| **1,0 s** | 4,51 | **9,73** | **66,85** | 6,87× |
| 5,0 s | 22,54 | **48,64** | 334,27 | 6,87× |
| 10,0 s | 45,08 | **97,28** | 668,54 | 6,87× |

### Bütçeyle **en fazla** kaç saniye

| bütçe | tekdüze kaba | **A′** | tekdüze ince |
|---|---|---|---|
| 30 GPU-günü | 6,65 s | **3,08 s** | 0,45 s |
| 100 GPU-günü | 22,18 s | **10,28 s** | 1,50 s |
| 300 GPU-günü | 66,55 s | **30,84 s** | 4,49 s |

---

## 3. Belirleyici satır

`1 s` simüle için:

| kurulum | maliyet | `~30 GPU-günü` bütçeye sığıyor mu | kullanılabilir mi |
|---|---|---|---|
| tekdüze kaba | 4,51 gün | evet | **hayır** — mermi çözülmemiş (ADR-0026) |
| **A′** | **9,73 gün** | **evet** | **evet** |
| tekdüze ince | 66,85 gün | **hayır** | evet |

> **A′, çözülmüş mermili bir ensemble'ı mümkün kılan tek seçenek.**
> Onsuz: ya mermi çözülmez (kaba), ya bütçe iki kat aşılır (ince).

Bu, ADR-0041'in seçilme gerekçesine **yeni bir kefe** ekliyor. Karar
verilirken gerekçe *"model-form hatası yok"* ve *"DART rejiminde 19,6×
ucuz"*du (KAYIT-033). Şimdi üçüncüsü var: **ensemble bütçesi**.

---

## 4. Bu hesabın **söylemediği** şeyler

Dürüstlük gereği ayrı yazılıyor.

### 4.1 Gereken simüle süre **bilinmiyor**

FAZ 4.5'in işi ve TRUBA kotası yüzünden ölçülmedi. Bu yüzden çıktı bir
**tek sayı değil**, bir **sınır**. Bir sayı uydurmaktansa sınırı vermek
doğrudur.

### 4.2 FIZIBILITE'nin sayılarıyla **doğrudan kıyaslanamaz**

`FIZIBILITE` §1 `N ≈ 2 000 000`'lik bir sahne varsayıyor; bu hesap
`N ≈ 11 000`'lik DART sahnesinde (`s = 7 m`). İki mutlak sayı **aynı şeyi
ölçmüyor**.

Ayrıca §1'in adım maliyeti **gözeneklilik ve öz-yerçekimi kapalı**
ölçülmüştü; §2b bunu düzeltti ve tam fizikte parçacık başına maliyet
çok daha yüksek çıktı. Burada §2b kullanıldı.

> **Kıyaslanabilir olan tek şey ORAN** (`6,87×`) ve o sahne ölçeğinden
> bağımsız — çünkü iki senaryo da aynı `µs/1000` ile çarpılıyor.

### 4.3 Doğrusal ölçekleme bir **varsayım**

FIZIBILITE'nin iki noktası bunu tam desteklemiyor: `N` üç kat artarken
parçacık başına maliyet `15 520 → 8 658 µs/1000`'e **düşüyor** (komşu
arama sabit maliyetinin amortismanı).

> Yani tahmin **muhafazakâr**: küçük `N`'de gerçek maliyet daha yüksek
> olabilir. Yön yazıldı.

### 4.4 `s = 7 m` çözünürlüğü **yeterli mi bilinmiyor**

Bu hesap tek bir kaba aralıkta yapıldı. G4-B1 (çözünürlük yakınsaması)
koşulmadan `s = 7 m`'nin yeterliliği bilinmiyor. Yetersizse `N` büyür ve
**bütün tablo ölçeklenir**.

---

## 5. Sırada

| # | iş | engel |
|---|---|---|
| 4.5 | gereken simüle süre → tablodan **tek satır** seçilir | kota |
| 4.4 | `s = 7 m` yeterli mi | kota |
| — | ADR-0041'e üçüncü kefe (ensemble bütçesi) işlenmesi | — |

---

## 6. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| bilinmeyen bir parametre **taranır**, uydurulmaz | §4.1 |
| iki sayı aynı şeyi ölçmüyorsa **kıyaslanmaz** | §4.2 |
| bir varsayımın **yönü** yazılır | §4.3 |
| bedel (`dt` cezası) **hesaba katılır**, gizlenmez | §1 |
| eski bir sonuç değiştiyse **nedeni** yazılır | §0 |
