# KAYIT-050 — `boulder_Y0` hiçbir taramada değişmedi; iki kuşkum çürüdü (2026-08-21)

**Kapsam:** A17 · sahne malzemesi · depo tutarlılığı
**Öncül:** [KAYIT-049](KAYIT-049_2026-08-18_CI-yesil-A3-kapandi.md)
**Koşular:** yok — **yerel CPU**, sahne kurulumu (kanıt koşusu değil)

---

## 1. Rapor kendi özetiyle çelişiyordu

Başlık `Açık: 4 — A3, A11, A12, A17` diyordu; oysa A3'ün gövdesi
`2026-08-17`'de *"Bu yarısı da KAPANDI (iş `1506785`)"* yazıyor ve
KAYIT-049 de A3'ü kapanmış sayıyordu.

`test_KAPANAN_ve_ACIK_sayilari_TABLOLARLA_tutuyor` bunu yakalayamaz,
çünkü sayıyı **başlıklarla** karşılaştırıyor ve iki taraf da A3'ü açık
sayıyordu. Etiket düzeltildi (sayaç `4 -> 3`), gerekçe yerinde kaldı ve
değişiklik raporun kendi içinde **not olarak** yazıldı.

---

## 2. Soru: taranan `Y0` çarpmanın gördüğü `Y0` muydu?

A17'nin bütün elemeleri `β = 1,411216`'yı **bit düzeyinde**
bırakmıştı — `Y0` altı mertebe, yerçekimi, koşu süresi `3000×`. Bu
kadar farklı kolun aynı sayıyı vermesi, taranan şeyin çalışma
noktasına ulaşmadığını da düşündürür.

Koda bakıldı:

```
faz48_iki_asama.py:156   return {**kw, "matrix_Y0": float(Y0)}
inference/forward.py:99  kw.update(boulder_alpha0=a0, matrix_Y0=y0, ...)
inference/forward.py:103 kw.update(matrix_alpha0=a0, matrix_Y0=y0, ...)
```

Üçü de **yalnızca matrisi** eziyor. `build_scene`'in `boulder_Y0`
varsayılanı `1,0e7 Pa`; `SAHNE` onu hiç vermiyor. Yani FAZ 4 boyunca —
eleme koşuları ve çıkarım uzayının `Y0` ekseni dahil — blokların
mukavemeti **hiç değişmedi**. Bloklar hedefin kütlece `%36,3`'ü.

---

## 3. Ölçüm yerel, ölçüt önden

`scripts/a17_carpma_bolgesi_malzemesi.py` sahneyi CPU'da kuruyor
(analitik ikosfer, PDS verisi gerekmiyor) ve çarpma noktası çevresinde
malzemeyi sayıyor. İki ölçüt betiğin kendi belgesinde, **veriye
bakılmadan** yazıldı.

### İki kuşkum da çürüdü

| kuşku | ölçüt | ölçülen | yargı |
|---|---|---|---|
| çarpma bir bloğun içine düşüyor | blok kütle payı `>= %50` | `r <= 8 m`: **`0,0000`** | **çürüdü** |
| ejekta ayrıklaştırma tabanının altında | krater içinde `< 20` parçacık | üretim inceltmesinde **`223`** | **çürüdü** |

Krater bölgesinin kütlesi `%92,6` matris, ve gereken ejekta
`10 m/s`'de `13,8` parçacık eder — kaba ama engel değil.

### Ayakta kalan: ortalamayı blok belirliyor

`r <= 15 m`'de blok kütle payı `%7,4` ama kütle ağırlıklı `Y0`
**`7,47e5 Pa`** — matrisin `75` katı. Sonuç aritmetik:

| `matrix_Y0` | bölgenin `<Y0>`'ı |
|---|---|
| `1 Pa` | `7,3779e5` |
| `100 Pa` | `7,3788e5` |
| `2,15e6 Pa` | `2,7292e6` |

> İş `1506779`'un üç kolu (`1 / 10 / 100 Pa`) bölgenin kütle ağırlıklı
> mukavemetini **`1,0001` kat** oynatıyor. *"Üçü de aynı çıktı"*
> bulgusu, taranan şey bölgede neredeyse hiç değişmediği için
> `Y0`'ın etkisizliğini **göstermiyor olabilir**.

Bunu bir kanıt gibi okumamak gerek: kütle ağırlıklı ortalama bir
**vekil**, matris `%92,6` ile sürekli faz ve kazıyı o yönetiyor
olabilir. Karar bir koşuya bağlı.

### Çarpma noktasının malzemesi bir kura

Sekiz tohumda `r <= 15 m` blok kütle payı: üretim tohumunda `0,0738`,
bir tohumda `0,4373`, **altısında `0,0000`**. Bütün A17 koşuları tek
tohumla yapıldı. Bu, ensemble'ın istatistiksel yakınsaması için de
ayrı bir uyarı.

---

## 4. Bunu kapatacak koşu — ölçüt önden yazıldı

İki ucuz kol (`t_end = 0,2 s`, tek nokta):

| kol | değişen |
|---|---|
| **B1** | üretim tohumu, `boulder_Y0` `1e7 -> 1e2 Pa` |
| **B2** | tohum `20260803` (saf matris), `matrix_Y0` `1e4 -> 1 Pa` |

- herhangi bir kolda `β` farkı `> %10` -> *"`Y0` da değil"* yargısı
  **geri alınır**.
- ikisinde de `< %1` -> mukavemet, öncekinden **daha sağlam** bir
  zeminde elenir.
- arası -> kısmi.

---

## 5. Engel: TRUBA çalışma alanına erişilemiyor

MCP bağlantısı `arf` ve `cuda` hedeflerinin ikisinde de
`egitimg16u1` olarak açılıyor. `/arf/scratch/egitimg16/driftclaude`
**yok**, `/arf/scratch/egitimg16u4` `Permission denied`. Kuyrukta iş
yok, `kolyoz-cuda` ayakta (`57` alloc, `palamut` drain).

Bu bir kod sorunu değil **erişim** sorunu ve etrafından
dolaşılmadı: B1/B2 gönderilmedi, gönderilmiş gibi de yazılmadı.

---

## 6. Bu turda ne **yapılmadı**

- Hiçbir kanıt koşusu koşulmadı; bu kayıttaki her sayı sahne
  kurulumundan geliyor.
- A17 kapanmadı, A11 ve A12'ye dokunulmadı.
- ADR-0046'nın kapsam kararı hâlâ kullanıcıda.
