# KAYIT-082 — `kos` hatası: dünün üç yargısı düştü, `n_yön` ayakta

**Tarih:** 2026-10-16 (akşam) · **Hatayı yapan:** Claude, aynı gün
**Etkilenen:** KAYIT-080 (§5/§6), KAYIT-081 (SBC), `docs/sonuclar/`
**Düzeltilmiş çıktılar:** `UP_s5_s6.json`, `UP_sbc.json`,
`URETIM_posterior.json`

---

## 1. Hata ne

`uretim_posterior.py` girdi olarak `kos` sütunu istiyor ve onu
ADR-0060'ın dönüşümünde kullanıyor:

    b_model = (β − 1) / kos²

ADR-0060 `kos`'u **net momentum vektörünün** kosinüsü olarak tanımlar:

    P⃗ = Σ m v⃗  (kaçan hedef maddesi),  Ê = P⃗/|P⃗|,  θ = ∠(Ê, ê_U)

Ben girdi dosyasını kurarken `ejekta_ayrismasi`'ndaki **`kos_ort`**'u
koydum — o ise parçacık başına kosinüslerin momentum-ağırlıklı
**ortalaması**:

    ⟨cos⟩ = Σ m|v| cos_i / Σ m|v|      ≠      cos∠(Σ m v⃗ , ê_U)

Üçgen eşitsizliği gereği `cos θ_net ≥ ⟨cos⟩`, yani `1/⟨cos⟩²` daima
daha büyük. Ölçülen fark:

| | ortanca | aralık |
|---|---:|---|
| **doğru** `1/cos²θ_net` | **1,1663** | 1,063 – 1,275 |
| hatalı `1/⟨cos⟩²` | 1,6761 | 1,469 – **4,416** |

`b_model` ortancada **1,437 kat** şişmişti; en kötü noktada 3,5 kat.

## 2. Nasıl yakalandı

Üretim posterioru koşarken ekrana `ADR-0060 gelenek carpani: ortanca
1.6761` düştü. ADR-0060 ve rapor **1,166** diyor. İki sayı
uyuşmayınca durdum.

Doğru hesap yeniden yapıldığında ADR'nin 88 noktada bildirdiği değeri
**birebir** verdi: ortanca `1,1663`, aralık `1,063 – 1,275`. Yani ADR
baştan doğruydu, girdi dosyası yanlıştı.

> Hatayı yakalayan şey, aynı niceliğin **iki yerde** yazılı olması ve
> birbirini tutmamasıydı. Tek yerde dursaydı sessiz geçerdi.

## 3. Ne değişti

| ölçü | ÖNCE (hatalı) | SONRA (doğru) |
|---|---:|---:|
| gelenek çarpanı ortanca | 1,6761 | **1,1663** |
| vekil `β` ÇD-RMSE | 0,5019 | **0,1509** |
| vekil `β` `q²` | 0,9310 | **0,9765** |
| `R` küçültülmüş | 0,2047 | 0,4560 |
| §6 `I_min` | 0,504 | 0,325 |
| §6 **bağdaşır hacim** | **%7,37** | **%34,04** |
| §6 posterior %68 hacmi | %0,50 | %10,27 |
| §6 oran | 14,78 | **3,31** |
| **§6 yargı** | POSTERIOR DAR | **İKİ YÖNTEM UYUŞUYOR** |
| §5 `σ_onsel` | 0,254 dex | **0,0000 dex** |
| **§5 yargı** | ÖNSEL ETKİLİ | **SONUÇ VERİDEN GELİYOR** |
| posterior kipi `log10 Y₀` | +0,254 (kenarda) | **+1,271** (içeride) |
| `α_b` büzülme | 0,579 ÖĞRENİLDİ | 0,031 **ÖNSEL BASKIN** |
| `Y₀` büzülme | 0,815 ÖĞRENİLDİ | **0,882 ÖĞRENİLDİ** |
| `f` büzülme | 0,271 ZAYIF | −0,305 **ÖNSEL BASKIN** |
| Fisher öz değerler | [978,3 · 2,35 · 0,002] | [499,7 · 0,82 · 0,00] |
| **`n_yön`** | **1** | **1** ✅ |
| bilgi bütçesi (`β` vekil payı) | %77,1 | **%23,3** |

## 4. Geri çekilen bulgular

Dünkü kayıtlarda yazılı olan şu dört şey **bu hatanın ürünüydü** ve
artık geçerli değil:

1. **"POSTERIOR DAR"** — posterior bağdaşır bölgeden 14,8 kat dar
   değil; oran **3,31** ve yargı **İKİ YÖNTEM UYUŞUYOR**. Eleme
   bölgesini "ana sonuç", posterioru "koşullu ek" yapan gerekçe
   **ortadan kalktı**; ikisi artık birbirini doğruluyor.
2. **"ÖNSEL ETKİLİ"** — `σ_onsel` 0,254 dex değil **0**.
3. **"Posterior kipi önsel kenarına yapışık"** ve ondan türeyen
   **"önsel kutusunun tabanı fiziği kesiyor olabilir"** uyarısı —
   kip artık `Y₀ ≈ 18,7 Pa`, kutunun ortalarında. Literatürdeki
   `~0,5 Pa` ile kurduğum bağ **düşer**.
4. **"Belirsizliğin %77'si vekilden geliyor, en yüksek kaldıraç daha
   çok nokta"** — vekil payı **%23,3**. Baskın kalem artık
   **gözlem** (%48,4), ki onu biz iyileştiremeyiz.

## 5. Ayakta kalanlar

- **`n_yön = 1`** (KAYIT-079). Düzeltilmiş posteriorda Fisher
  `[499,7 · 0,82 · 0,00]`, eşik 36 — ikinci öz değer hâlâ 44 kat
  altında. Manşet sonuç **etkilenmedi**.
- **SBC: üç eksen de KALİBRE** (yeniden koşuldu, `p = 0,868 / 0,074 /
  0,299`). Posterior yayımlanabilir.
- **Kapı 1** 96/96, kayıp yok.
- **Model gözleme ulaşıyor**: `I_min` 0,504 → **0,325**, daha da iyi.

## 6. İki bağımsız teyit — düzeltme doğru

1. **Vekil hatası düştü.** `β` ÇD-RMSE `0,5019 → 0,1509`. Hatalı
   `⟨cos⟩` 0,476–0,825 arasında geziniyordu ve `1/⟨cos⟩²`'ye `1,47–4,42`
   gibi geniş bir saçılma sokuyordu; doğru `cos θ_net` ise yalnız
   0,886–0,970. Yani yanlış dönüşüm vekile **gürültü enjekte
   ediyormuş**.
2. **Büzülme sınıfları artık Fisher ile tutarlı.** Önce büzülme
   `α_b`'yi "ÖĞRENİLDİ" sayarken Fisher `n_yön = 1` diyordu — açık bir
   çelişki. Şimdi ikisi aynı şeyi söylüyor: `Y₀` öğrenildi, `α_b` ve
   `f` **önsel baskın**.

## 7. §5 artık dişsiz — saklanmıyor

`σ_onsel = 0` yargısı **SONUÇ VERİDEN GELİYOR** veriyor ama bu
göründüğünden zayıf bir kanıt: `KAYDIRILMIS` önsel `Y₀ < 3 Pa`'yı
kesiyor, posterior kipi ise `18,7 Pa`. Yani kesilen bölge posteriorun
zaten umursamadığı yer; perturbasyon **hiçbir şeye dokunmuyor**.

Kilitli yargı tablosu uygulandı ve sonuç bu. Ama sınavın bu haliyle
ayırt edici gücü düşük; raporda böyle yazılacak.

## 8. Niçin oldu, tekrarı nasıl engellenir

Hata kodda değil, **benim elle kurduğum ara dosyadaydı**. `kos`
sütununun hangi nicelik olduğu `uretim_posterior.py`'nin yorumunda
*"her koşunun kendi fırlatı alanından"* diye yazıyordu — iki aday da
bu tarife uyuyor. ADR-0060'ın kesin tanımına bakmadan en yakındaki
alanı (`kos_ort`) aldım.

**Önlem:** girdi dosyası artık elle değil,
`beta_gelenegi.firlati_dogrultusu` + `gelenek_carpani` çağrılarak
üretiliyor — yani ADR-0060 için yazılmış olan kodla. Hatalı dosya
`analiz/HATALI_kos_ort_girdi.csv.yedek` olarak duruyor, silinmedi.

Ek olarak: bu sütun için bir sınav yazılmalı — `kos` değerleri
`[0,80 ; 1,00]` dışına çıkarsa durmalı. Hatalı dosyada alt sınır
`0,476`'ydı ve hiçbir şey şikâyet etmedi.

## 9. Not — KAYIT-079 bu hatadan etkilenmedi

`up_gozlemli_secimi.py` durum dosyalarını doğrudan okuyor ve `β`'yı
`beta_hedef`'ten alıyor; ara CSV'yi **kullanmıyor**. Dolayısıyla
`n_yön = 1` ölçümü hatalı `kos`'a hiç dokunmadı.

Ayrı bir soru olarak kalıyor: o ölçüm ham `β` üzerinden yapıldı,
ADR-0060'ın `Ê` geleneğine çevrilmiş `b` üzerinden değil. Düzeltilmiş
posteriorun Fisher'ı (`[499,7 · 0,82 · 0,00]`) aynı yargıyı verdiği
için sonuç dayanıklı, ama bu fark kayda geçiyor.
