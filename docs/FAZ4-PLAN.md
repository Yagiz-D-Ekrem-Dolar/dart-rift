# FAZ 4 planı — Doğrulama V4 ve Sentetik Kurtarma

**Durum:** 4.1 tamamlandı, **4.2 karar uzayı ölçümle daraltıldı** (4 Ağustos)
**Önkoşul:** G3 geçti (`9561864`, iş 1450156)
**Taşınan borç:** ADR-0026 (mermi çözünürlüğü), EKSIKLER §B, §D

---

## 0. FAZ 4 ne sorar

> **Bilinen parametrelerle bir çarpma üret. Çıkarım o parametreleri geri
> bulabiliyor mu?**

Bu, FAZ 5'in vekil modelinin ve Bayes çıkarımının **doğruluk kanıtıdır**.
Geri bulamıyorsa, FAZ 5'in ürettiği her sayı anlamsızdır.

FAZ 3 *hangi gözlenebilirlerin* kaydedileceğine karar verdi (β, krater
şekli, ejekta kataloğu, periyot). FAZ 4 o gözlenebilirlerin **bilgi taşıyıp
taşımadığını** ölçer: iki farklı iç yapı ayırt edilebilir mi?

---

## 1. Önce çözülmesi gereken: mermi çözünürlüğü

**Bu bir ön koşuldur, bir görev değil.** ADR-0026 ölçtü:

| büyüklük | değer |
|---|---|
| DART mermisi çapı boyunca 6 parçacık için gereken | **1,72e9 parçacık** |
| ölçülmüş fizibil üst sınır | **1,12e7 parçacık** |
| oran | **153×** |
| fizibil sınırda mermi çapına düşen parçacık | **1,12** |

ADR-0026 §2 açıkça diyor ki: *"Yerel incelmenin nasıl yapılacağı FAZ 4'te
**ölçümle** seçilecek ve ayrı bir ADR ile kaydedilecek."*

### Seçenekler ve her birinin ölçülmesi gereken sınırı

| # | yaklaşım | ölçülmesi gereken |
|---|---|---|
| **A** | **Değişken kütle bölgeleri** (çarpma yakınında ince, uzakta kaba) | çözücü **hangi kütle oranına** kadar dayanıyor? Arayüzde yapay kuvvet ve defter kayması ne zaman başlıyor? |
| **B** | **Parçacık bölme** (adaptif) | bölme kuralı kütle/momentum/enerjiyi koruyor mu; bölme anında defter ne kadar kayıyor? |
| **C** | **İki alan eşlemesi** (ince + kaba, örtüşme bölgesi) | arayüzden geçen momentum akısı doğru mu? |
| **D** | **Mermiyi hiç çözme** — momentum/enerji kaynak terimi | kaynak teriminin krater ve β üzerindeki etkisi, çözülmüş referansla ne kadar örtüşüyor? |

> ## GÜNCELLEME (4 Ağustos) — ölçümler bu tabloyu değiştirdi
>
> | # | yaklaşım | mermiyi çözer | arayüz hatası | şok geçişi | **momentum** | mimari bedel |
> |---|---|---|---|---|---|---|
> | ~~A~~ | global `h`, değişken kütle | **HAYIR** | 0,168 *(en iyi)* | **zararsız** ✔ | **1e-16** ✔ | yok |
> | **A′** | parçacık başına `h` | evet | **0,55–1,10** | (A'da zararsız) | **1e-16** ✔ | çekirdek+grid+CFL+Ω |
> | **B** | parçacık bölme | yalnızca A′ ile | = A′ | = A′ | = A′ | = A′ |
> | **C** | iki alan eşlemesi | evet | **yok** (ara değerleme `O(h²)`) | ölçülmedi | **7,5e-03 ✘ sistematik** | iki çözücü + örtüşme + MLS **+ korunum düzeltmesi** |
> | **D** | kaynak terimi | çözmez, **atlar** | yok | — | ✔ (tek çözücü) | ılımlı |
>
> Kaynaklar: [023](defter/KAYIT-023_2026-08-04_cozunurlugu-h-belirliyor.md) ·
> [024](defter/KAYIT-024_2026-08-04_degisken-h-arayuzu-kotulestiriyor.md) ·
> [025](defter/KAYIT-025_2026-08-04_C-eslemenin-bedeli.md) ·
> [026](defter/KAYIT-026_2026-08-04_E3-sok-arayuzden-gecerken.md) ·
> [027](defter/KAYIT-027_2026-08-04_C2-esleme-momentumu-kaybediyor.md)
>
> **A elendi:** çözülen ölçeği `h` belirliyor (`h` skaler; sabit `h`'de plato
> `h → 0` limitinden %6,84 uzakta ve parçacık eklemekle kapanmıyor).
> **B bağımsız bir seçenek değil:** bölme `dx`'i küçültür, `h` skaler
> kaldıkça faydasız.
> **A′ pahalı:** çözünürlüğü verir ama arayüzü 3,2–6,5 kat gürültülendirir;
> `Ω` düzeltmesi kurtarmıyor.
> **Arayüz, şok geçişi açısından zararsız** (E3: 8:1'de %0,125 fark) — yani
> karar arayüz kalitesine değil **çözünürlük** ve **korunum** eksenlerine
> bakmalı.
> **C momentumu korumuyor:** `7,5e-03`, ve kayma **tamamen sistematik**
> (`|x|/|v| = 1,000000`) → adım sayısıyla **doğrusal birikir**. A/A′ `1e-16`.
>
> **Kalan tek ölçüm: D-1** (kaynak teriminin model-form hatası, dolaylı
> kıyasla). ADR-0041 ondan sonra yazılır.
>
> Aşağıdaki özgün metin **silinmedi**: o zamanki bilgiyle doğru yazılmıştı.

**Sıra ölçümle belirlenir, tercihle değil.** İlk ölçüm **A** içindir çünkü:

- mevcut çözücüde **kod değişikliği gerektirmez** (kütleler zaten parçacık
  başına, ADR-0030'dan sonra tutarlı),
- diğer üçünün hepsi **A'nın sınırını bilmeyi gerektirir** (B bölme oranını,
  C arayüz kontrastını, D "ne kadar kaba yeterli"yi),
- bir sınır çıkarsa (örn. "8:1'e kadar temiz"), gereken seviye sayısı
  doğrudan hesaplanır: `153 = 8^k → k ≈ 2,4` yani **3 seviye**.

---

## 2. İlk ölçüm — kütle oranı toleransı

### Soru
Aynı fiziksel cismi, iki farklı kütleli parçacık popülasyonuyla ayrıklaştır.
**Kütle oranı arttıkça ne bozulur ve ne zaman?**

### Ölçülecekler

| büyüklük | neden | beklenen (temiz) |
|---|---|---|
| `a_SPH(t=0)` | başlangıç **gerilmesiz** olmalı (ADR-0022) | **tam 0** |
| birim bölünmesi `Σ(m/ρ)W` | ADR-0030'un değişmezi | **1,0** |
| enerji hatası (N adım) | defter kayması | G1 eşiği %0,5 |
| momentum hatası | korunum | ~1e-15 |
| arayüzde yapay ivme | asıl tehlike | 0'dan ayırt edilemez |

### Boşluk kontrolü *(ADR-0040)*
Kütle oranı **1:1** iken sonuç **tam temiz** çıkmalı. Çıkmazsa ölçüm
düzeneğinin kendisi bozuktur ve hiçbir sayı yorumlanamaz.

### Neden bu ölçüm şimdi yapılabilir
ADR-0030'dan **önce** yapılamazdı: kütleler tekdüzeydi ve `m/ρ ≠ V_p`
tutarsızlığı (K7) her sonucu kirletirdi. Şimdi `m_i = ρ_i·V_p` tam tutuyor
(ölçülen `[1,000000 ; 1,000000]`), yani **kütle oranını değiştirmek yalnızca
kütle oranını değiştiriyor.**

> Bu, hata ayıklama kampanyasının FAZ 4'e doğrudan katkısıdır: K7 düzeltilmemiş
> olsaydı bu ölçüm yorumlanamazdı.

---

## 3. FAZ 4'ün görev sırası

| # | görev | çıktı |
|---|---|---|
| ~~4.1~~ | ~~**Kütle oranı toleransı** ölçümü~~ | **TAMAMLANDI** — KAYIT-019…024; A elendi |
| 4.2 | Yerel incelme yaklaşımının **seçimi** | **ADR-0041** |
| 4.3 | Seçilen yaklaşımın uygulanması | kod + çapraz kontrol |
| 4.4 | DART kurulumunda **çözünürlük yakınsaması** | krater çapı ve β'nın N'e duyarlılığı |
| 4.5 | **Gereken simüle süre** (EKSIKLER §D) | β ne zaman duruluyor |
| 4.6 | **Sentetik kurtarma**: bilinen (α, Y0, f_boulder) → geri bulunuyor mu | G4 kanıtı |
| 4.7 | G4 kapısı | kapı raporu |

**4.5 ve 4.6, 4.3 tamamlanmadan yapılamaz** — ADR-0028'de ölçüldüğü gibi,
çözülemeyen bir mermiyle "β durdu" ölçümü merminin geri sıçramasını ölçer,
ejektayı değil.

---

## 4. FAZ 4'ün taşıdığı bilinen riskler

Hata ayıklama kampanyasından devreden ve FAZ 4'ü **doğrudan** etkileyenler
([`DURUM-DEGERLENDIRMESI.md`](DURUM-DEGERLENDIRMESI.md) §3):

- **R1/R2** — bu fazın 4.1–4.3'ü tam olarak bunları kapatmak içindir.
- **R3** — hasarda Weibull parametreleri global; 4.6'da β'nın hasara
  duyarlılığı taranırken karara bağlanmalı.
- **R4** — krater çıkarımı gerçek koşuya bağlanınca `x_reference` **zorunlu**
  yapılmalı.

---

## 5. FAZ 4'e girerken uyulacak kurallar

Kampanyadan çıkan ve bu fazda **baştan** uygulanacak olanlar
([`YONTEM.md`](YONTEM.md)):

1. Her yeni kriterin yanına **boşluk kontrolü**: "bu test boş bir doğruyu mu
   sınıyor?"
2. Her "ayrışıyor / çalışıyor / yakınsıyor" iddiası bir **pozitif kontrol**
   ister.
3. Bir büyüklük iki yerde yazılırsa ikincisi **türetilmeli** ya da ayrışma
   **hata vermeli**.
4. Bir alt küme, ölçülen büyüklüğe göre **seçilmemeli**.
5. Yeni bir GPU çekirdeği yazılırsa **CPU referansı ve çapraz kontrolü**
   aynı commit'te gelir — K1'in kök nedeni bu boşluktu.
6. Bir GPU testinin tahmini **önce ölçülür, sonra yazılır** (S1, S3).
