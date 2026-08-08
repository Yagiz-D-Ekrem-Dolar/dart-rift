# KAYIT-037 — Boşluk 3 **kapandı**; A′ kazancın `%67`'sini veriyor (2026-08-08)

**Kapsam:** FAZ 4.4b · **Durum:** ölçüldü — **boşluk 3 kapandı**
**Öncül:** [KAYIT-036](KAYIT-036_2026-08-08_bosluk3-mukavemette-olculdu.md)
(gözenekli kol ölçülememişti),
[ADR-0041](../adr/ADR-0041-yerel-incelme-yaklasimi.md) §5 boşluk 3

---

## 0. KAYIT-036'nın bıraktığı yerden

KAYIT-036 mukavemeti ölçtü (taşma `%0,0000`) ama gözenekli kolu
**ölçemedi**: cephe yarıçapı doygunlaşıyordu ve kutu *"arayüzü geç"* ile
*"kenara varma"* şartlarını aynı anda sağlayamıyordu.

### Denenen ve **atılan** yol

İlk düşüncem arayüzü küçültmekti (`r_iç: 0,15 → 0,06`). **Yanlıştı** ve
koşulmadan önce görüldü: enjeksiyon yarıçapı `h_inj = 3·dx = 0,094`, yani
arayüzden **büyük** olurdu — enerji ince bölgenin **dışına** konurdu.
Kaba kafesin kaynağı çözmesi `h_inj ≳ 3·dx` gerektiriyor, o da
`r_iç ≥ 0,15` demek. **Kısıt gerçek; kaçamak yok.** Betik silindi.

### Seçilen yol: gözlenebiliri değiştir

Kutuyu büyütmek yerine (pahalı) **ölçülen şey** değiştirildi:

```
p_iletilen = Σ_{r > 0,30}  m_i · max(v_i · r̂_i , 0)
```

`r = 0,30`'dan geçen toplam **dışarı doğru** radyal momentum.

| | cephe yarıçapı | iletilen momentum |
|---|---|---|
| tür | **eşik** | **integral** |
| tavanı var mı | **var** (kutu köşesi `0,866`) | **yok** |
| gözenekli malzemede | doygunlaşıyor | çalışıyor |
| sorulan şey mi | dolaylı | **doğrudan** — *"arayüz dışarı ne geçirdi?"* |

Yalnızca dışarı bileşen sayılıyor (`v·r̂ > 0`); geri sekme ve salınım net
toplamı yapay olarak küçültürdü.

---

## 1. Ölçüm (job 1460705, H200, `t = 3e-5`, `n = 32`, `λ = 2`, `r_iç = 0,15`)

| kol | yargı | taşma | parantez genişliği |
|---|---|---|---|
| yalnız EOS | **arayuz_zararsiz** | **%0,0000** | %51,54 |
| + mukavemet | **arayuz_zararsiz** | **%0,0000** | %51,11 |
| + gözeneklilik | **arayuz_zararsiz** | **%0,0000** | %23,62 |
| **tam (+hasar), A′** | **arayuz_zararsiz** | **%0,0000** | %24,56 |
| tam, tek `h` (kontrol) | **arayuz_zararsiz** | **%0,0000** | %24,56 |

**Beş kolun beşinde de** dört ön koşul geçti: kollar ayırt edilebilir,
enjekte enerji eşit, enjeksiyon bölgesi eşit, kütle ihmal edilebilir.

> **Boşluk 3 kapandı.** Mukavemet, gözeneklilik ve hasar **birlikte**
> açıkken A′'nın arayüzü iletilen momentuma **hiçbir şey eklemiyor**.

---

## 2. Beklemediğim sonuç: A′ **kazancın 2/3'ünü** veriyor

Parantez içindeki **konum** okundu (`0` = tekdüze ince, `1` = tekdüze kaba):

| kol | `p` kaba | `p` iki bölgeli | `p` ince | konum | **incelme kazanımı** |
|---|---|---|---|---|---|
| yalnız EOS | 1070,62 | 973,88 | 710,85 | 0,731 | %26,9 |
| + mukavemet | 1287,20 | 1167,09 | 851,83 | 0,724 | %27,6 |
| + gözeneklilik | 347,76 | 303,96 | 281,31 | 0,341 | %65,9 |
| **tam, A′** | 350,42 | **304,04** | 281,33 | **0,329** | **%67,1** |
| **tam, tek `h`** | 350,42 | **344,15** | 281,33 | **0,909** | **%9,1** |

Son iki satır **aynı geometri, aynı malzeme, aynı `t`**. Tek fark
`h` politikası.

> **A′ ile iki bölgeli kol incelme kazancının `%67,1`'ini alıyor;
> tek `h` ile yalnızca `%9,1`.** Yani parçacık başına `h`, aynı parçacık
> dağılımından **7,4 kat** daha fazla kazanç çıkarıyor.

Bu, KAYIT-023'ün *"çözünürlüğü `h` belirliyor"* bulgusunun **tam malzeme
modelinde** doğrudan doğrulanmasıdır. O ölçüm ideal gazda ve dolaylıydı
(sabit `h` platosu `h→0` limitinden `%6,84` uzak). Bu ölçüm aynı şeyi
mukavemet + gözeneklilik + hasar açıkken ve **doğrudan** gösteriyor.

> **A yaklaşımının neden elendiğinin en net kanıtı bu satırdır**: sadece
> parçacık eklemek (tek `h`) kazancın `%9`'unu veriyor.

### Gözeneklilik neden kazanımı **artırıyor**

Gözeneksiz kollarda kazanım `%27`, gözenekli kollarda `%66`. Gözeneklilik
açıkken parantez de daralıyor (`%51 → %24`). Yorum: gözenek çökmesi
çözünürlüğe daha az duyarlı bir süreç, dolayısıyla kaba ve ince kollar
birbirine yaklaşıyor; kalan farkı ise `h` belirliyor. **Bu bir yorumdur,
ölçüm değildir** — ayrıca sınanmadı.

---

## 3. KAYIT-036'nın hangi yargısı düzeltiliyor

KAYIT-036 §1 şöyle yazdı:

> | + gözeneklilik | ölçülemedi (aşağıda) |
> | tam (EOS+muk+göz+hasar), A′ | ölçülemedi |

**Bu satırlar artık geçerli değil** — ama silinmiyor. O tabloda
ölçülemeyen şey **cephe yarıçapıydı** ve o gerçekten ölçülemedi; bu kayıt
**başka bir gözlenebilirle** ölçtü.

> **Ders:** bir büyüklük ölçülemiyorsa, bu *"soru yanıtlanamaz"* demek
> değildir. Önce **gözlenebilir** sorgulanır. Ben önce kutuyu büyütmeyi
> düşündüm (pahalı) ve arayüzü küçültmeyi denedim (yanlış); doğru yanıt
> ölçüyü değiştirmekti.

Aynı şekilde KAYIT-036 §2'nin `0,05` eşiği tartışması da duruyor: cephe
yarıçapı ölçütünün o eşikte gücü yoktu. Momentum ölçütünde böyle bir eşik
**yok** — integralin ayarlanacak parametresi `r_sonda` ve o da arayüzün
dışında, kenardan uzak seçildi.

---

## 4. Boşluk 3'ün son durumu

| bileşen | durum |
|---|---|
| Tillotson (gerilmesiz) | **ölçüldü** — taşma %0,0000 |
| mukavemet | **ölçüldü** — taşma %0,0000 |
| **gözeneklilik** | **ölçüldü** — taşma %0,0000 |
| **hasar** | **ölçüldü** — taşma %0,0000 |

> **ADR-0041 §5 boşluk 3 KAPANDI.**

### Yine de koşullu kalan

- Ölçüm **küp geometrisinde** ve **enerji enjeksiyonlu** bir kaynakla
  yapıldı; DART'ın gerçek geometrisi (moloz yığını + hızlı mermi)
  **değil**. ADR-0042'nin `N_komşu` salınımı da aynı şekilde koşulludur.
- `λ = 2` (8:1) ölçüldü; ADR-0026 DART için çok daha yüksek oran istiyor.

---

## 5. Sırada

| # | iş |
|---|---|
| 4.5 | gereken benzetim süresi (ADR-0028'in açık maddesi) |
| — | ADR-0042 + boşluk 3'ün DART geometrisinde sınanması |

---

## 6. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| bir büyüklük ölçülemiyorsa önce **gözlenebilir** sorgulanır | §0, §3 |
| yanlış çıkan yol **silinir ama nedeni yazılır** | §0 |
| önceki yargı düzeltilir, **silinmez** | §3 |
| yorum ile ölçüm **ayrı** işaretlenir | §2 (gözeneklilik yorumu) |
| kapanan boşluğun **koşulları** yazılır | §4 |
