# Durum değerlendirmesi — ne kanıtlandı, nerede hâlâ risk var

**Tarih:** 2026-08-03 · **Commit:** `a5d9fa2` · **Kapsam:** FAZ 0–3

Bu belge iki soruya yanıt verir ve ikisini **karıştırmaz**:

1. **Ne kanıtlandı?** — ölçümle, iş numarasıyla.
2. **Nerede hâlâ hata olma potansiyeli var?** — kanıtlanmamış olan.

---

## 1. Bu turda ne oldu

FAZ 3 daha önce **"tamamlandı, 0 hata"** diye sunulmuştu: 627 test, G3 7/7,
kırmızı takım 14/14, kapsam %97. Bu sunum **yanlıştı**.

Üç ardışık hata ayıklama turu **20 kusur + 2 süreç hatası + 3 kapsam boşluğu**
buldu. Tam döküm ölçülen sayılarıyla: **`docs/KUSUR-KAYDI.md`**.
Kararlar: **ADR-0029 … ADR-0040**.

### Turların anatomisi

| tur | odak | bulunan | ortak imza |
|---|---|---|---|
| 1 | en yeni/en az sınanmış kod | K1–K6 | testler **parçaları** sınıyordu, bütünü değil |
| 2 | veri tutarlılığı | K7–K12 | aynı büyüklük **iki yerde**, biri türetilmiyor |
| 3 | **denetim kodunun kendisi** | K13–K20 | ölçüt yanlış şeyi ölçüyor ya da **hiç düşemiyor** |

### En ağır dördü

| # | ölçülen etki |
|---|---|
| K1 | hiçbir fizik yokken gerilme **1000 kat** sönüyordu (S: 1,0e7 → 4,88e3) |
| K10 | tavanı aşan parçacık ilk adımda eziliyor → **−1,14 GPa** yapay çekme; KE bağlanma enerjisinin **2,9 milyon katı** |
| K7 | kütle/yoğunluk tutarsızlığı → toplam yoğunlukla bloklarda **−7,62 GPa** |
| K2 | **kratersiz** Dimorphos elipsoidinde **9,04 m hayali krater** |

**Hiçbiri testlerle yakalanamazdı** — 20 kusurun tamamı **kapsanan
satırlardaydı** (kapsam %96,5–100).

---

## 2. Kanıtlanmış olan

TRUBA H100'de, `9561864`..`a5d9fa2` aralığında ölçülen:

| kanıt | değer |
|---|---|
| Hasar durumu bozulmuyor | S sabit **1,000000e+07** (önce 4,88e3) |
| Settling yakınsıyor | KE/E_bağ = **3,360e-12** (önce 2,873e+06) |
| Kütle-gözeneklilik tutarlılığı | `m/(ρ·V_p)` = **[1,000000 ; 1,000000]** |
| Yığın yoğunluğu hedefi | **1800,0000** (tam) |
| Blok kesri (hacim) | **0,3034** / hedef 0,30 (%1,15) |
| Komşuluk (geometrik iç) | **12,00** (n = 4226), FCC teorik 12 |
| Çözünürlük yakınsaması | çap boyunca **6,46 → 10,26 → 16,29**, kesin artan |
| Mermi mesh içinde | **0** (küre ve elipsoit, iki eksende) |
| Krater/küresel ayrımı | fazlalık **0,000000**; %10 büzüşme **−7,8466** yakalanıyor |
| Mesh yönelimi | tutarlı; 20 ters yüzde **yakalanıyor** (hacim %3,1 sapıyor) |
| Sahne karması | `ca730c2c…` — **iki bağımsız ortamda birebir** (Linux/numpy 1.26.4, Windows/numpy 2.4.6) |
| Yerel test takımı | **596 geçti / 0 kaldı** |

**Yapısal önlemler** (kusur *sınıfını* kapatır):

- `_eval()` **saflık değişmezi** — durum yazılamaz (üç yolda)
- Hasarın **CPU döngü referansı** + GPU↔CPU çapraz kontrol *(yoktu)*
- **`dt` çapraz kontrolü** *(yoktu — çapraz testler sabit dt kullanıyordu)*
- Sabitlerin **tek doğruluk kaynağı** kilidi (G 7 yerde, DART sabitleri 2 yerde)
- **Kusur kaydının kendisi sınanıyor** (tablo↔gövde, her kayıtta ölçülen sayı)
- Konfigürasyonda **10³ birim hatası** yakalanıyor + sıra/tutarlılık şartları
- İçbükey mesh üyeliği (32007 nokta, 0 yanlış)

---

## 3. Nerede hâlâ hata olma potansiyeli var

**Bu bölüm dürüstlük içindir.** Aşağıdakiler *bilinen* ve *kayıtlı* açıklardır;
"kusursuz" denmemesinin sebebi bunlardır.

### Yüksek — bilimsel sonuca girer

**R1. Mermi çözünürlüğü (ADR-0026, EKSIKLER §B).**
DART mermisini çapı boyunca 6 parçacıkla çözmek **1,72e9 parçacık** ister;
fizibil sınır **1,12e7** — **153 kat** fark. Fizibil sınırda mermi çapına
**1,12 parçacık** düşer. FAZ 4 tekdüze ağla yapılamaz. *Bu bir kusur değil,
ölçülmüş bir ölçek gerçeği* — ama β'yı doğrudan etkiler.

**R2. Gereken simüle süre ölçülemedi (ADR-0028, EKSIKLER §D).**
Kararlılık koşusunda ejekta sayısı **tam 1009**'da dondu; bu merminin kendi
parçacık sayısıdır — yani hedeften hiçbir parçacık kaçmadı, ölçülen şey
**merminin geri sıçramasıydı**. Sebep R1. **β = 1,557 bir DART β'sı olarak
sunulamaz.**

**R3. Hasarda Weibull parametreleri global (EKSIKLER §E).**
`k_weibull`/`m_weibull` tek malzeme için tanımlı; bloklar (sağlam kaya) ve
matris (gözenekli regolit) aynı kusur dağılımını alıyor. Kısmen giderildi
(kusur **sayısı** artık katı hacimle orantılı — %56 yayılım), ama `k` ve `m`
ortak. **Etkisi ölçülmedi.**

### Orta — yanlış kullanımla tetiklenir

**R4. Krater çıkarıcıda `x_reference` isteğe bağlı (EKSIKLER §F).**
Verilmezse cisim **küre** kabul edilir. Tanı (`reference_is_spherical`)
bildiriyor ve düzensiz cisim senaryosu G3 C5'te şart, ama üretim yolunda
unutulabilir. Ölçülen bedel: **9,04 m hayali krater**.

**R5. `units.py` üretimde bağlı değil (EKSIKLER §G).**
Boyut modülü var, fizik kodu kullanmıyor. Km/m hatası bir kez bu boşluktan
çıktı. Kısmi önlem: konfigürasyon aralık testleri (10³ hatayı yakalar). **Tam
çözüm (boyut-denetimli fizik) yapılmadı.**

### Düşük — bilinen ve karakterize edilmiş

**R6. Yüzey örneklem yanlılığı.** "Yüzey" = yön kutusundaki en uzak parçacık;
gerçek yüzeyin içinde kalır. Ölçülen: küre yarıçapında **−1,53 m**, krater
derinliğinde **+%5,5 … +%13**. Artık **ayrıştırılıp raporlanıyor** (ADR-0039)
ama ortadan kalkmadı.

**R7. Enerji kayması `O(dt)`.** Uzun koşuda **1,4558e-02**'de sabit (birikmiyor);
CFL dörtte bire inince **0,2201**'e düşüyor. Kontrol edilebilir bir düğmeye
bağlı, ama sıfır değil.

**R8. M1'de toplam-yoğunluk yöntemi keskin sıçramayı yumuşatır.** Matris
+%20,3, blok −%11,0. Bu **fizik**, bookkeeping değil — ADR-0015'in süreklilik
yoğunluğunu seçme gerekçesi. M0'da ayrışma **+%0,0**.

### Sınanmamış kalan bölgeler

**R9. Gerçek PDS ağı yalnızca yerel olarak sınandı.** `is_consistently_oriented`
kontrolü PDS testine bağlandı ama PDS ürünleri yalnızca TRUBA'da; sonucu son
koşuda görülecek.

**R10. FAZ 4+ hiç yazılmadı.** Bu değerlendirme **yalnızca FAZ 0–3** içindir.
Çarpma koşusunun kendisi, ensemble çıkarımı, Hera karşılaştırması — hiçbiri
mevcut değil.

---

## 4. Verdikt

**"Kusursuz" demiyorum ve bir daha demeyeceğim.**

Bu turun kendisi bunun kanıtı: aynı tabloya (627 test, 7/7, 14/14, %97 kapsam)
bakıp "0 hata" demek yanlıştı ve arkasından **20 kusur** çıktı — hepsi
kapsanan satırlarda.

Söylenebilecek dürüst şey şudur:

> `a5d9fa2` commit'inde, **bilinen ve kaydedilmiş** hiçbir açık kusur yoktur.
> Bulunan 20 kusurun tamamı düzeltilmiş, ölçülmüş ve **sınıfını kapatan
> yapısal önlemlerle** kilitlenmiştir. Kalan riskler §3'te **numaralandırılmış
> ve ölçülmüştür**; hiçbiri gizli değildir.

Bir sonraki tur bakılacak yerler, öncelik sırasıyla: **R1/R2** (FAZ 4'ün
tasarım kararı, β'yı belirler), **R3** (hasarın β'ya duyarlılığı), **R5**
(boyut denetimi), **R4** (zorunlu `x_reference`).

---

## 5. Yöntem notu — bu tur nasıl çalıştı

Bulunan her kusur şu üç sorudan biriyle çıktı:

1. **"Fiziği dondur, değişmemesi gerekeni ölç."** → K1
2. **"Aynı büyüklük iki yerde mi yazılı?"** → K7, K10, K11, K12
3. **"Bu ölçüt gerçekten sormak istediğim soruyu mu ölçüyor?"** → K13–K20

Üçüncüsü en verimlisi oldu ve dört alt biçime ayrıldı:
yanlış **büyüklük** (K13) · **vekil** (K14) · **yanlı örneklem** (K15) ·
yanlış **davranış beklentisi** (K16) · **düşemeyen** koşul (K19-B, K20).

Ve her yeni kriterin yanına bir **boşluk kontrolü** kondu: *"bu test boş bir
doğruyu mu sınıyor?"* — ADR-0040.
