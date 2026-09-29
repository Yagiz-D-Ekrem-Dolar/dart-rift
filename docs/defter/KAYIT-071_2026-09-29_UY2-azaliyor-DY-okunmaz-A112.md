# KAYIT-071 — UY2: AZALIYOR (bütçe kurtuldu) · DY: sahne gerçekleşmedi (A112) → OKUNMAZ (2026-09-29)

**Kapsam:** çözünürlük kesişimi + DART sahnesinin ilk koşusu ·
**Durum:** bir kilitli yargı okundu, bir kilitli yargı **okunmaz** sayıldı,
üç kusur (A110, A111, A112) · **Kaynak:** `docs/olcumler/UY2_DY_2026-09-29/`,
[PROTOKOL-UY2](../truba/PROTOKOL-UY2-KESISIM.md),
[PROTOKOL-DY](../truba/PROTOKOL-DY-DART-GEC-EVRE.md) ·
**Öncül:** [KAYIT-070](KAYIT-070_2026-09-28_gpusuz-guclendirme-turu.md)

---

## 1. UY2 — **AZALIYOR** (geçerli, okunur)

| kol | `β(300 s)` | parçacık |
|---|---|---|
| kaba, `t_geçiş = 1,0 s` | 4,097 | 14 616 |
| orta, `t_geçiş = 1,0 s` | 4,272 | 66 601 |

`Δ_kesişim = 0,0534`. Aynı iki merdivenin `t_geçiş = 0,2 s`'deki farkı
**0,098** idi (UY). **Geçiş anı düzeltilince çözünürlük farkı yarıya indi.**

Kilitli üretim kararı: **kaba merdiven + çok doğruluklu vekil**,
`σ_çözünürlük = 0,053`. Bütçe `~1400` değil **`~750 GPU-saat`**.

**Kapı olmayan tanı (KAYIT-070 §2'nin ilk gerçek kullanımı):**
`s(1 s)` farkı **0,001**, `t50` oranı **0,97**. Yani iki kol yalnız aynı
sayıyı değil **aynı mekanizmayı** veriyor. "Doğru sebeple mi tutturuyoruz"
sınavı geçti.

> ADR-0052'nin açık bıraktığı tek soru kapandı: eksenler bağımsız değil.
> İki hatanın birbirini götürdüğü senaryo **elendi**.

## 2. DY — yargı hesaplandı ama **OKUNMAZ**

Koşu teknik olarak kusursuzdu: momentum artığı `4,6e-15`, enerji `−%0,66`,
600 s tamam, bütün denetimler geçti. Kilitli kural `MODEL AŞIYOR` dedi
(`β = 4,719`, `I = 3,07`, kesme 3,0; `M_ejekta = 9,45e7` — gözlemin **6 katı**).

**Ama koşu, protokolün §2'de yazdığı sahneyi gerçekleştirmedi (A112).**
Merdiven inceltmesi kabuğu her zaman küre olarak kuruyordu; elipsoit hedefte
bu yanlış kabuk basık ekseni şişirdi:

| | yarı-eksenler (p99,5) | kütle |
|---|---|---|
| kaba yığın | 83,1 / 81,7 / **52,6** | 4,430e9 |
| inceltmeden sonra (hatalı) | 80,2 / 76,8 / **72,9** | 4,674e9 (**+%5,5**) |
| inceltmeden sonra (düzeltilmiş) | 80,2 / 81,6 / **57,9** | 4,428e9 (−%0,05) |

Yani gerçek şekli kullanmak için açtığımız elipsoit, simülasyona girerken
**neredeyse küreye dönüşmüştü**. W→W2 emsali: yargı kayıtta olduğu gibi
kalır, **okunmaz** sayılır, koşu `DY2` önekiyle tekrarlanır. Kural değişmedi.

### Nasıl bulundu

**Dün yazılan denetim bugün kendi koşumuzu yakaladı.** A108 için eklenen
`kutle_tutarliligi`, DY'nin `4,683e9 kg`'ını `%8,9` sapmayla işaretledi
(tolerans `%5`). Kütlenin peşine düşünce şekil bozulması çıktı.

### DY'nin sayısı ne işe yarar

Protokolün cevabı değil, **tanı**: küreye yakın, `%9` ağır bir DART benzeri
cisim `Y₀ = 10 Pa`'da `β = 4,72` ve gözlemin 6 katı ejekta veriyor.
L1'e göre basık elipsoit küreden **daha yüksek** `β` verdiği için, gerçek
şekille aşmanın artması beklenir — ama bu bir **beklenti**, DY2 söyleyecek.

U/V'nin `β ≈ 2,05` ile gözlemin **altında** kaldığı durumdan, gözlemin
**üstünde** kalınan bir duruma geçtik. Bu okuma da DY2 ile doğrulanacak.

## 3. Üç kusur

- **A112** (KAPANDI): inceltme kabuğu artık sahnenin şeklinden kuruluyor;
  küresel dal **bit-aynı** (sınav bunu doğruluyor — ilk denememde kabuk
  yarıçapını değiştirmiştim, sınav yakaladı). 5 sınav.
- **A111** (KAPANDI, kendi hatam): yoğunluğu şekil modelinin hacminden
  hesaplamıştım; doğrusu kalibrasyon → `2306,1` (elipsoit) / `2305,8` (küre),
  ikisi de `4,3000e9 kg`.
- **A110** (açık): DART sahnesinde `t_end = 600 s` yetmiyor; `β` son on
  yılda hâlâ `−%2,7` düşüyor, `1/t` ekstrapolasyonu `β∞ ≈ 4,55`.

## 4. Gönderildi: DY2 + DK (`1583605`)

`DY2` (elipsoit, düzeltilmiş kabuk, kalibre yoğunluk) ve **`DK`**
(hacim-eşdeğer küre, aynı kütle). DK bir kontrol kolu değil, **ölçüm**:
NUSAP soy kütüğü `hedef_sekli = 0,20` teriminin doğrulamasının sıfır
olduğunu göstermişti; iki kolun farkı o terimi **kendi kodumuzda ölçülmüş**
hale getirecek (`σ_şekil`, PROTOKOL-DY §6.3, koşudan önce kilitli).

## 5. Dürüst değerlendirme

- İyi: UY2 bütçe riskini kaldırdı ve mekanizma doğrulaması geçti.
- Kötü: DART sahnesinin ilk koşusu yanlış şekille gitti; `~6 GPU-saat` ve bir
  günlük bekleme kayboldu.
- Ama kusur **üretim havuzundan önce** yakalandı. Aynı hata 96 koşuluk
  havuzda çıksaydı `~500 GPU-saat` giderdi. Uçuş öncesi duman koşularının
  gerekçesi tam olarak budur.
- Zincir şuydu: NUSAP → "şekil terimi doğrulanmamış" → DK kolu düşüncesi →
  kütle denetimi → şekil bozulması. **Belgeleme disiplini kusuru buldu**,
  şans değil.
