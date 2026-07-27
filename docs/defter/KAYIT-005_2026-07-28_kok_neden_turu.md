```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 005
============================================================

**Tarih**       : 28.07.2026
**Saat**        : 00:00 – 02:30 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Çevrim içi — yerel makine (RTX 3050) + TRUBA/ARF-ACC

## BUGÜNKÜ HEDEF

KAYIT-004'te açık bırakılan iki kabul eşiğini kök nedenine kadar takip etmek:
Sedov şok yarıçapı (%15, eşik %5) ve Taylor bar enerji defteri (%288, eşik %1,5).

## BULGU 1 — Sedov: çekirdek doğru, komşu sayısı yanlıştı

Hata çözünürlükten bağımsız olarak %15–16'da takılıydı. Bağımsız gösterge de
aynı yöne işaret ediyordu: kinetik enerji oranı 0,121 ölçülüyordu, oysa γ=1,4
için Sedov benzerlik çözümü 0,28 verir — enerji şok cephesine geçmiyordu.

Yalnızca `h/dx` değiştirilerek, aynı başlangıç koşuluyla (n = 48):

| h/dx | komşu | şok yarıçapı hatası | KE/E |
|------|-------|---------------------|------|
| 1,25 | 65 | %15,8 | 0,121 |
| 1,60 | 137 | %6,5 | 0,161 |
| **2,00** | **268** | **%2,6** | **0,191** |

Aynı taramada yapay viskozite katsayıları da denendi (α=1,0/β=2,0 ile
α=0,5/β=1,0); etkisi ikincil kaldı. Yani sorun aşırı sönüm değil, **kernel
toplamının yetersiz örneklenmesiydi**.

Kök neden: Wendland C2'yi şartname "pairing kararsızlığına dirençli olduğu
için" kilitliyor, ama ben onu kübik spline'ın alışılmış 65 komşusuyla
çalıştırıyordum. Dehnen & Aly (2012) bu direncin ancak ~200 komşuda ortaya
çıktığını gösterir. Çekirdeği seçme gerekçesini kendi kurulumumla geçersiz
kılmışım. Düzeltme tüm 3B senaryolara uygulandı (ADR-0013).

## BULGU 2 — Taylor bar: aynı çifte sayım hatası, ikinci kez

Enerji hatası %288 çıkıyordu. Tek satırlık imkânsızlık kanıtı: biriken plastik
iş 1001 J, oysa sistemin **başlangıç kinetik enerjisi 352 J**. Plastik iş,
sisteme giren tüm enerjinin üç katı olamaz.

Kök neden: `return_mapping` plastik işi `u`'ya ekliyordu. Ama `dudt` tam
gerilme tensörünün (`−P·I + S`) işini zaten taşıyor; deviatorik iş orada
sayılıydı. Bu, ADR-0008'de porozitede yakaladığım hatanın **aynı sınıfı**:
*şartname sözde-kodu bir katkıyı açıkça eklerken, bizim ayrıklaştırmamız onu
zaten içeriyordu.* Düzeltme sonrası hata %288 → %7,66 (ADR-0012).

Ek olarak rijit duvar modeli değiştirildi: donmuş parçacık katmanına çubuk
parçacıkları gömülüyordu. z=0 simetri düzlemi aynı sınır koşulunu yapay
parçacık olmadan sağlar.

## BULGU 3 — Taylor'da kalan hata: tensile instability

Ayırt edici test (aynı kurulum, yalnızca malzeme modeli değişiyor):

| Vaka | Enerji hatası | Son iç enerji |
|------|---------------|---------------|
| Akma yok (Y₀=10¹²) | %4,08 | 139 J |
| **Dayanım tamamen kapalı** | **%10,36** | 61 J |
| EPP Y₀=4·10⁸ | %7,66 | 340 J |
| Düşük hız (v=20 m/s) | **%413** | **−282 J** |

İki şey birden söylüyor: hata dayanım *kapalıyken* daha büyük (yani return
mapping kaynaklı değil), ve düşük hızda iç enerji **negatife** düşüyor —
fiziksel olarak imkânsız. Lineer EOS'ta serbest yüzeyde ρ < ρ₀ olunca basınç
negatife geçiyor ve **tensile instability** başlıyor. Düşük hızda çarpma
enerjisi küçük olduğu için etki baskın hâle geliyor.

Şartname bu riski §9'da adıyla listeliyor ve çözümünü de veriyor: Wendland
kernel (mevcut) **+ artificial stress** (henüz uygulanmadı). Bu, açık kalan
tek maddedir ve G2 kapısı bu nedenle henüz geçmiş sayılmamaktadır.

## ALTYAPI

CI kapsamı %81,7'ye düşüp eşiği kırmıştı. Sebep: GPU kernel'leri GitHub
runner'ında koşulamıyor ama kapsam paydasında sayılıyordu — "test edilmemiş"
değil "test EDİLEMEZ" olan kod eksik gibi görünüyordu. Kapsam iki katmana
ayrıldı: CI'da CPU'dan erişilebilen kod (%94,2, 331 test), kapıda CUDA'lı
ortamda tüm kod.

TRUBA kümesi doldu (tüm düğümlerde 8/8 GPU tahsisli); kapı işleri kuyrukta
bekliyor. Kanıt bu nedenle yerel RTX 3050 (sm_86, gerçek CUDA) üzerinden
üretiliyor, TRUBA koşusu ikinci bağımsız kanıt olarak eklenecek.

## BUGÜNÜN DEĞERLENDİRMESİ

Üç bulgunun ortak yanı, hiçbirinin "motor çalışmıyor" olmamasıydı. Korunum
tanıları her üç durumda da sağlamdı ve dikkati doğru yere — kuruluma,
muhasebeye, çözünürlük parametresine — yöneltti.

En çarpıcı ders komşu sayısıydı: **çekirdek seçimi tek başına bir karar
değildir; çekirdek + komşu sayısı birlikte bir karardır.** Şartname çekirdeği
kilitlemiş ama komşu sayısını belirtmemişti; o boşluk bir alışkanlıkla
dolduruldu ve hata oradan girdi. Bir kilidin gerekçesini okumak, kilidin
kendisini okumak kadar önemli.

## SONRAKİ ÇALIŞMA

1. Artificial stress (Monaghan 2000) — Taylor'daki tensile instability.
2. G1 ve G2 kapı koşuları (yerel GPU + TRUBA).
3. Kanıt dosyaları ve kapı raporları.

**Kayıt Sahibi:** Yağız Ekrem Dalar
