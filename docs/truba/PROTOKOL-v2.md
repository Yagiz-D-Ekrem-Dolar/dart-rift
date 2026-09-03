# Protokol v2 — neden değişti, ne değişti (2026-09-03)

**Öncül:** Protokol v1 = commit `44abe54`, etiket
`anlik/2026-09-01-yontem-donduruldu`

---

## Dondurma neden **asla değiştirme** demek değil

`L2`, v1'in şok kapısında bir eksik olduğunu **ölçümle** gösterdi.
İki seçenek vardı:

| seçenek | sonucu |
|---|---|
| eksik olduğu **bilinen** kapıyla `R1/R2/R3` koşmak | yanlışlığı bilinen ölçütle veri üretmek |
| **versiyonla + gerekçelendir + yeniden dondur** | **seçilen** |

> `dondurma ≠ asla değiştirme`
> `dondurma ⇒ değişiklik varsa versiyonla, gerekçelendir, yeniden dondur`

Sessizce değiştirmek `p`-hacking olurdu. Bu, tersi: değişiklik
**sonuçtan önce değil, sonuçla** geldi ve **gerekçesiyle** yazıldı.

## Değişen **tek** şey: şok kapısı iki taraflı

| | v1 | **v2** |
|---|---|---|
| **sert kapı** | `≥ %4,56` (bandın `1/10`'u) | **aynı — yalnız alt sınır** |
| üst sınır | yok | **tanı bayrağı** `> 1,2 × %74,3` |
| yargılar | `SOK_YOK` / `KISMI` / `SOK_VAR` | `+ SOK_ASIRI_ADAY` |

### Üst sınır neden **sert kapı değil**

İlk v2 taslağı onu sert kapı yapmıştı; **yanlıştı**. Bandın üst
kenarı `up = v/2`'den geliyor ve bu **aynı malzeme ve empedanstaki
simetrik düzlemsel** çarpma için doğru. DART'ta mermi alüminyum,
hedef gözenekli bazalt — arayüz parçacık hızı **empedans
eşleşmesiyle** belirlenir.

> Gerçek bir üst tavan ancak kullanılan EOS/Hugoniot ve çarpma
> empedans probleminden **türetilirse** sert kapıya dönüşür. O türetim
> yapılana kadar `SOK_ASIRI_ADAY` yalnızca **şüphe işaretidir** ve
> tek başına sonucu iptal etmez.

Aksi hâlde *"neden `1,2`?"* sorusunun savunulabilir bir cevabı olmaz.

### Neden üst sınır

`L2`'nin düşük AV kolu sıkışmayı `%75,65`'e çıkardı ve v1 kapısı
`SOK_VAR` dedi. Hugoniot'u aşmak şok yakalamanın **bozulduğunun**
işareti: yetersiz yapay viskoziteyle parçacık iç içe geçmesi ve şok
sonrası salınım.

### Neden pay `1,2` ve neden `1,0` değil

Bandın üst kenarı `up = v/2`'den geliyor ve bu **aynı malzeme ve
empedanstaki simetrik düzlemsel** çarpma için doğru. DART'ta mermi
alüminyum, hedef gözenekli bazalt — arayüz parçacık hızı **empedans
eşleşmesiyle** belirlenir.

> Yani `%74,3` kesin bir tavan **değil**, sezgisel bir üst kenar.
> Pay bu belirsizliği kapıya yazıyor.

**Sonucu:** düşük AV kolu (`%75,65`) v2 kapısını da **geçiyor**. O
kolun kanıt sayılmamasının sebebi kapı değil, **kütle bileşimi**
(A36) — kaçan `33` parçacığın **hepsi kaba seviyeden**.

## Değişmeyenler

`Δβ` ölçütü · üç nicelik (`Δβ`, `M_ejekta`, `P_ejekta,∥`) ·
`A1 < 0,20` / `A2 < 0,10` eşikleri · `σ_num` kuralı (monoton/zarf) ·
zamansal plato kapısı · `n_kaçan`'ın yalnızca tanı olması ·
`L2` karar ağacı.

## Kayıt değişikliği (**ölçüt değişikliği değil**)

`ileri_kosu_merdiven` artık `durum_dizini` alıp her nokta için `npz`
kaydediyor: `mermi_kesri` (provenance), `alpha0`, `x_referans`, `θ`.

`L1`'in `β`'ları kullanılamadı çünkü bu kayıt yoktu (A37): defter
post-hoc uygulanamadı, parçacık kimliği karşılaştırılamadı. Bu bir
**yargı kuralı** değişikliği değil; hiçbir eşiğe dokunmuyor.

## `L2` yorumu — v2 altında

| kol | kapı | okunur mu | not |
|---|---|---|---|
| taban | `KISMI` | evet | `n = 16`, hepsi `5,83 kg` |
| `u` tabanı | `KISMI` | evet | tabanla **bit düzeyinde aynı** |
| gözeneksiz | `SOK_YOK` | **hayır** | ADR-0049 |
| düşük AV | `SOK_VAR` | evet **ama** | ejekta **tamamen kaba** (A36) |

### Düşük AV kolunun **doğru** ifadesi

> Düşük AV kolundaki artmış kaçış sinyali, **çözülmüş ejekta kanıtı
> olarak reddedildi**; sinyal tamamen **kaba çözünürlük
> seviyesindeki** parçacıklardan geliyor.

Bu, düşük AV'nin dinamikleri **etkilemediği** anlamına gelmez —
tersine, başka bir **sayısal rejime** ittiğini gösterir.

### Dar ifadeler

- `u` hattı için: *"test edilen `u` pertürbasyonu, taban koşulunda
  ejekta davranışının baskın açıklaması olarak **desteklenmedi**"* —
  *"elendi"* değil; tek bir varyant bütün termodinamik başlatma
  olasılıklarını elemez.
- Gözeneksiz kol için: *"bu koşuda şok kurulmadı"* — *"gözeneklilik
  önemsiz"* **değil**.
- `L1` ejekta kütlesi için: *"ayrıklaştırmayla **nicemli** ve
  parametre taramasında toplam düzeyinde ayırt edilemiyor"* —
  *"aynı parçacıklar kaçıyor"* **değil**; parçacık kimliği
  karşılaştırılamadı.


---

## L1'in krater sonucu **kullanılabilir** — diff denetlendi

`3bbc722 -> HEAD` farkı yalnızca şunlara dokunuyor:

| dosya | ne |
|---|---|
| `anlik_al.py` | yeni araç |
| `faz4_zincir.sh` | `pipefail` |
| `faz5_ensemble_merdiven.py` | raporlama + `npz` + dilim |
| `forward.py` | **yalnızca ekleme** — `durum_dizini` ve `npz` bloğu |
| `momentum_defteri.py`, `sok.py` | gözlenebilir/kapı |

`warp_core/`, `setup/`, `crater_shape.py`, `cpu_reference/`,
`faz48_iki_asama.py` — **hiçbirine dokunulmadı**.

> İleri fizik, inceltme, parçacık durumu ve krater çıkarıcısı `L1`
> koşusuyla **birebir aynı**. Krater duyarlılığı (`0,08 – 0,79 m`)
> savunulabilir; `β`'lar (A37) yine de kullanılmıyor.

## Ejekta bileşimi artık **her ölçümde** raporlanıyor

Yeni kapı değil; mevcut ölçümün parçası (A36):

| alan | ne |
|---|---|
| `ejekta_seviyeleri` | her ayrıklaştırma seviyesinde `n`, kütle, `P_eksenel` |
| `m_ej_medyan`, `m_ej_max` | kaçan parçacık kütlesi dağılımı |
| `en_agir_1_pay`, `en_agir_5_pay` | momentumun **yoğunlaşması** |

`R1/R2/R3`'te `M_ejekta` tek başına değil, **seviye başına** da
görülecek. `β` yakınsarken momentumu bir-iki kaba parçacık taşıyorsa
gözlenebilir hâlâ kırılgandır — bu bir **tanı**, kapı değil.
