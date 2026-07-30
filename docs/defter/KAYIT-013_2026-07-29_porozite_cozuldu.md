```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 013
============================================================

**Tarih**       : 29.07.2026
**Saat**        : 20:00 – 03:00 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Yerel makine (RTX 3050) + TRUBA/ARF-ACC

## BUGÜNKÜ HEDEF

Tek iş: **ADR-0022'nin açık kusurunu kapatmak**. FAZ 3'ün önündeki tek engel
buydu ve gözeneklilik, çıkarımın asıl parametresi olduğu için ertelenemezdi.

## TEŞHİS — üç hipotez, ikisi çürüdü

**Hipotez 1: enerji muhasebesinde eksik terim var.** Şartnamenin sözde-kodu
sıkışma işini `u`'ya ekliyor; ADR-0008 bunu bilinçli uygulamamıştı. Ölçüldü:

| Yaklaşım | Enerji hatası |
|---|---|
| ADR-0008 (iş eklenmez) | %1,88 |
| Şartname (`+w/ρ`) | %20,33 |
| Termodinamik türetme (`−w/ρ`) | %51,51 |

Her iki işaret de **daha kötü**. ADR-0008 haklıymış; hipotez çürüdü.

**Hipotez 2: model şiddetli şok rejiminde zorlanıyor.** Sıkıştırmayı
yavaşlattım:

| v_iç | E hatası | max\|dα\| /adım |
|---|---|---|
| 5 m/s | **%8127,60** | 0,471 |
| 50 m/s | %79,80 | 0,395 |
| 500 m/s | %2,40 | 0,500 |

Yavaşlattıkça **kötüleşti** — hipotez çürüdü. Ama asıl ipucu buradaydı:
**`max|dα|` her koşuda ~0,5.** α, sıkıştırma hızından **bağımsız olarak**
1,5'ten 1,0'a **tek adımda** çöküyordu. Mutlak hata sabitti; oranın değişmesi
yalnızca `E₀ ∝ v²` küçüldüğü içindi.

**Hipotez 3: α güncellemesi açık yapıldığı için aşırı atıyor.** Doğrulandı.

## KÖK NEDEN

`porosity_update` distansiyonu **açık** güncelliyordu: bir önceki adımın
`P`'sinden `crush_alpha(P)` okunup doğrudan yazılıyordu.

Tillotson gibi sert bir EOS'ta bu kararsızdır. Başlangıçta `ρ=1800`, `α=1,5`,
`ρ_s=2700`, `P=0`. `ρ` yalnızca 1810'a çıkınca `ρ_s=2715` olur ve
`P ≈ 9,9×10⁷ ≈ P_s` — yani **crush eğrisinin tamamı %0,4'lük bir gerinimle
aşılır**. α bir anda 1'e iner, `ρ_s = ρ = 1810` olur ve katı gerilmesiz
2700'e göre **%33 genleşmiş** sayılır → devasa sahte çekme → negatif iç
enerji → patlayan defter.

Denklem aslında **örtüktür**: α kendi belirlediği basınca bağlıdır.

## ÇÖZÜM

`α = crush_alpha(P_katı(α·ρ, u)/α)` denklemi `[1, α_eski]` aralığında
**bisection** ile çözülüyor. Kalıntı monoton, adım sayısı **sabit** (40) —
determinizm korunuyor (ADR-0002). Hem CPU referansında hem GPU çekirdeğinde.

## SONUÇ

| v_iç | önce | sonra | u_min | ρ_s |
|---|---|---|---|---|
| 5 m/s | %8127,60 | **%0,4647** | −1,8e5 → **+1,64** | **2700,0** |
| 50 m/s | %79,80 | %0,4743 | | 2698,7 |
| 500 m/s | %2,40 | %0,5879 | | 2618,5 |

Çarpma senaryosu:

| nside | önce | sonra | gözenekliksiz |
|---|---|---|---|
| 32 | %6,74 | **%0,3798** | %0,2437 |
| 44 | **%15,81** | **%0,3955** | %0,2638 |

Hata artık **çözünürlükle büyümüyor** — kusurun imzası buydu. nside=44'te
**40 kat** iyileşme.

En önemlisi: **α artık sıkıştırmayı izliyor** (v=5'te 1,494, v=500'de 1,051).
Eskiden her durumda 1,000'e çöküyordu, yani model gözenekliliği **hiç
modellemiyordu** — sadece "hepsi ezildi" diyordu. Çıkarımın asıl parametresi
bu olduğu için bu, enerji defterinden bile önemli.

## DEĞERLENDİRME

Bu kusur üç kapıdan da geçmişti. Neden? G2 C3 gözenekliliği **nokta modeli**
olarak sınıyordu (crush eğrisi monoton mu, geri genleşme var mı, iş ≥ 0) ve
SPH tarafında yalnızca şok basıncı oranına bakıyordu. G2 C5 enerji korunumunu
ölçüyordu ama o senaryoda gözeneklilik **kapalıydı**. Yani gözenekliliğin
**dinamik bir koşudaki enerji davranışı** hiçbir ölçütte yoktu.

İki hipotezin çürütülmesi de kayda değer: doğru cevaba, yanlış cevapları
ölçerek varıldı. Özellikle "yavaşlatınca kötüleşiyor" sonucu, sezgiye aykırı
olduğu için asıl ipucunu verdi.

## SIRADA

- Kapılar ve dayanıklılık testi düzeltilmiş kodla yeniden koşuluyor
  (işler 1434417 / 1434418 / 1434419).
- Yerçekimi ağacının CPU'da Python'da kurulması hâlâ FAZ 3 için ölçek
  sınırı (KAYIT-012, BULGU 4).
