# G4 kapı ölçütleri — **ölçümden önce** yazıldı (2026-08-08)

> **Neden şimdi.** ADR-0040: *bir kriter düşebilmelidir.* Ölçüm yapıldıktan
> sonra yazılan eşik, ölçüme uydurulmuş eşiktir. Bu belge 4.4–4.6
> koşulmadan **önce** yazılıyor; sayılar sonra doldurulacak, eşikler
> **değiştirilmeyecek**.
>
> Bir eşik değiştirilmek zorunda kalırsa, değiştirilmez — **düşer** ve
> nedeni bir ADR'ye yazılır.

**Durum:** 4.4 kuyrukta (job 1460706), 4.5 kısmen, 4.6 başlamadı.
TRUBA kotası dolu ([FAZ4-DURUM.md](FAZ4-DURUM.md) §2).

---

## 1. G4 neyi kanıtlamalı

FAZ 4'ün tek cümlelik iddiası:

> **DART çarpmasını, çıkarımın gerektirdiği doğrulukta çözebiliyoruz.**

Bu üç parçaya ayrılır ve **üçü de** geçmeden kapı geçilmez.

| # | parça | ölçüt kimlik |
|---|---|---|
| A | mermi **çözülüyor** | G4-A |
| B | gözlenebilirler **yakınsıyor** | G4-B |
| C | bilinen parametreler **geri bulunuyor** | G4-C |

---

## 2. G4-A — mermi çözülüyor

ADR-0026'nın kapattığı sorun: mermi hedefin çözünürlüğünden küçükse
erken zamanlı şok bağlanması **sayısal bir yapaydır**.

| ölçüt | eşik | nasıl ölçülür |
|---|---|---|
| **A1** mermi çapı / yerel aralık | **≥ 2,0** | `faz44_dart_yakinsama.py` raporluyor |
| **A2** A′ ince bölgesi mermiyi **kapsıyor** | `r_ince ≥ 3·R_mermi` | `refine_scene` tanısı |
| **A3** kütle sapması (kaba/ince ek yeri) | **< %0,5** | `refine_scene` tanısı |

> **Düşme koşulu:** A1 iki farklı `λ`'da da `2,0`'ın altında kalırsa,
> A′ DART için yetersizdir ve ADR-0041 yeniden açılır.

**Bilinen durum:** A3 yerelde ölçüldü — `2,25e-05`, eşiğin `220` kat
altında. A1 ve A2 koşuya bağlı.

---

## 3. G4-B — gözlenebilirler yakınsıyor

`β` ve krater çapı, çözünürlük artarken **oturmalı**.

| ölçüt | eşik | gerekçe |
|---|---|---|
| **B1** ardışık iki çözünürlük arası `β` farkı | **< %10** | `β` ana üründür; bundan büyük bir sayısal belirsizlik, çıkarımın hata çubuğunu domine eder |
| **B2** `β` **durulmuş** olmalı | `settling_time.is_settled` → `True` | durulmamış bir `β` yakınsama tartışmasına giremez |
| **B3** A′ ile tek `h` arasındaki fark | A′, ince kola **daha yakın** | KAYIT-037 küpte `%67,1` vs `%9,1` ölçtü; DART'ta yön **aynı** olmalı |
| **B4** enerji sapması (log-log eğim) | **≤ 1,0** | ADR-0020: `O(dt)`; süperlineer büyüme kararsızlıktır |

> **Düşme koşulları:**
> - B1 `%10`'u aşarsa: çözünürlük yetersiz, daha ince koşu gerekir.
> - B2 düşerse: koşu süresi yetersiz (FAZ 4.5'e geri dönülür).
> - **B3 düşerse ADR-0041 düşer** — A′'nın seçilme gerekçesi buydu.
> - B4 `1,0`'ı aşarsa: entegratör veya `dt` politikası bozuk.

### B1 eşiği neden `%10`

Keyfî değil, **geriye doğru** hesaplandı: ADR-0026 DART için `β`'yı
`±0,1` mertebesinde ayırt etmek istiyor; `β ~ 3` için bu `%3,3`. Sayısal
belirsizliğin **fiziksel** belirsizliğin altında kalması gerekir, ama
`%3,3`'ün altına inmek bu çözünürlükte gerçekçi değil. `%10` ilk kapı
için **bilinçli olarak gevşek** seçildi ve **G5'te sıkılacaktır**.

> Bu gevşeklik **yazıldığı için** dürüsttür: G4 `%10` ile geçse bile
> ana ürün henüz `±0,1` doğrulukta değildir.

---

## 4. G4-C — bilinen parametreler geri bulunuyor

Sentetik kurtarma: bilinen `(α₀, Y₀, f_boulder)` ile ileri koşu yapılır,
çıktılardan parametreler geri çıkarılır.

| ölçüt | eşik | gerekçe |
|---|---|---|
| **C1** her parametre `%1-σ` bandı gerçek değeri **içermeli** | 3/3 | temel doğruluk |
| **C2** en az bir parametre **bilgilendirici** | posterior genişliği, önselin **< %50**'si | hiçbiri daralmıyorsa veri parametre taşımıyor demektir |
| **C3** **boşluk kontrolü**: gürültü artırıldığında bant **genişlemeli** | monoton | genişlemiyorsa çıkarım veriyi kullanmıyordur |

> **C3 neden zorunlu:** KAYIT-030'un dersi. Bir kurtarma "çalışıyor"
> görünebilir çünkü posterior **önselin kendisidir**. Gürültüye tepki
> vermeyen bir çıkarım hiçbir şey öğrenmiyordur.

> **Düşme koşulu:** C2 düşerse gözlenebilir kümesi yetersizdir; yeni
> gözlenebilir eklenmeden G4 geçilemez.

---

## 5. Kapının kendisi hakkında iki kural

1. **Kısmi geçiş yok.** A, B, C üçü de geçmeden G4 geçilmez. Bir parça
   geçemezse kapı raporu *"geçilemedi"* yazar; *"kısmen geçildi"* diye
   bir durum yoktur.
2. **Koşullu geçiş açıkça işaretlenir.** ADR-0041 ve ADR-0042 şu an
   koşulludur (ölçümler küp geometrisinde). G4 geçse bile bu koşullar
   kapı raporunda **listelenir**.

---

## 6. Şu an bilinen durum

| ölçüt | durum | değer |
|---|---|---|
| A1 | koşulmadı | — |
| A2 | koşulmadı | — |
| **A3** | **geçti** | `2,25e-05` (eşik `%0,5`) |
| B1 | koşulmadı | — |
| B2 | araç hazır | `settling_time` (13 test) |
| B3 | küpte ölçüldü, DART'ta koşulmadı | küp: `%67,1` vs `%9,1` |
| B4 | önceki koşularda ölçülüyordu | — |
| C1–C3 | başlanmadı | — |

> **G4 geçilmedi ve bu belge onu geçirmek için yazılmadı** — eşikleri
> ölçümden önce sabitlemek için yazıldı.
