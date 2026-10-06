# KAYIT-076 — Üç kilitli yargı: önsel **içermiyor**, çekme **4,2 kat daha etkili**, kaçıklık **L12'den 3,3 kat küçük** (2026-10-06)

**Kapsam:** DO (önsel), DC (matris çekmesi), DN (çarpma yeri) ·
**`~20,4 GPU-saat`** · **Durum:** üç kilitli yargı okundu, iki ödünç terim
daha ölçüldü, bir **bilimsel sonuç** çıktı ·
**Kaynak:** `docs/olcumler/DO_DC_DN_2026-10-06/`,
[PROTOKOL-DO](../truba/PROTOKOL-DO-DAYANIM-ONSELI.md),
[PROTOKOL-DY §8/§9](../truba/PROTOKOL-DY-DART-GEC-EVRE.md) ·
**Öncül:** [KAYIT-075](KAYIT-075_2026-10-05_bes-karar-verildi.md) (beş karar)

---

## 1. Dört kol yan yana

| | DY2 (`Y₀ = 10`) | **DO1** (`500`) | **DO2** (`5000`) | **DC** (çekme açık) | **DN** (`25 m` kaçık) |
|---|---|---|---|---|---|
| `β` | 3,7480 | **2,6247** | **1,8738** | **1,0807** | **3,6650** |
| `M_ejekta` | 1,964e7 | 3,649e6 | 7,516e5 | **2,777e2** | 2,321e7 |
| koni | 85,2° | 77,1° | 83,8° | 47,9° | **107,7°** |
| `t50` | 0,541 s | 0,107 | 0,015 | 0,001 | 0,845 |
| dondurulan | 4103 | 3124 | 2021 | **34** | 4365 |
| enerji sapması | −%0,78 | −%0,79 | −%0,79 | −%0,79 | −%0,80 |
| kütle tutarlılığı | −%0,05 | −%0,05 | −%0,05 | −%0,05 | −%0,06 |

Dördü de `COMPLETED`, `gecerli = True`, momentum artığı `≤ 9e-15`.

## 2. DO — **ÖNSEL GÖZLEMİ İÇERMİYOR** (A2 ölçümle kilitlendi)

DART sahnesinde üç nokta: `10 / 500 / 5000 Pa`. Güç yasası uydurması
`p = −0,1791`, en büyük bağıl artık `0,1198` (kapı `0,15` — **altında,
ama yakın**).

> **Dışdeğerleme interpolasyona döndü:** gözlem artık ölçülen aralığın
> **içinde** (`disdegerleme = False`). PROTOKOL-DO'nun varlık sebebi tam
> bu ve işe yaradı.

### 2a. W2'den taşınan tahmin **yanlıştı** — ve bu iyi haber

| | `β(500 Pa)` | `β(5000 Pa)` | üs `p` |
|---|---|---|---|
| W2 güç yasasından **beklenen** | `~3,20` | `~3,05` | `−0,0760` |
| DART sahnesinde **ölçülen** | **`2,625`** | **`1,874`** | **`−0,1791`** |

DART sahnesinin `β(Y₀)` eğrisi kıyas sahnesinden **2,4 kat dik**.
ADR-0053'ün `644 Pa`'lık dışdeğerlemesi bu yüzden kaydı; gerçek yer
çok daha aşağıda:

| hedef `β` | ima edilen `Y₀` | eski önsel `[1e3,1e7]` | **yeni `[1e0,1e5]`** |
|---|---|---|---|
| `3,12` (PROTOKOL-U, kilitli) | **`55,5 Pa`** | **dışında** (`−1,26` dekad) | içinde |
| **`3,5418`** (ADR-0054) | **`20,1 Pa`** | dışında | içinde |
| `3,730` (`+1σ`) | `13,5 Pa` | dışında | içinde |
| `3,295` (`−1σ`) | `35,6 Pa` | dışında | içinde |

**Dördü de interpolasyon** (`10 – 5000 Pa` arasında). A2 kararı
(`DART_UZAYI_S4`) ölçümle doğrulandı ve **PROTOKOL-HAVUZ §3.1'in kapısı
`DART_UZAYI_S4`'ü seçiyor.**

### 2b. İkinci sürpriz: **`Y₀` sandığımdan çok daha iyi tanımlanabilir**

Eğim dikleşince `1σ`'nın `Y₀`'daki bedeli küçülür:

| | `1σ` → `Y₀` çarpanı | dekad |
|---|---|---|
| W2 serisinden (ADR-0053 §3) | `×12,41` | `1,09` |
| **DART sahnesinde ölçülen** | **`×2,67`** | **`0,43`** |

**`4,6` kat iyileşme.** `Y₀`, `5` dekadlık önselde yarım dekaddan iyi
kısıtlanabilir. Projenin ana parametresi için bu çok iyi bir haber.

Bunun yan etkisi: `M_ejekta`'nın kazancı `6,3` kattan **`1,8` kata**
düşüyor (`p_M = −0,5150`, çarpan `×1,52`) — çünkü `β`'nın kendisi
bilgilendirici oldu. Yargı yine **`M_EJEKTA TANIMLAYICI`** (`1,52 < 3,0`),
yani ADR-0053 §4.2'nin "`M_ejekta` ikinci gözlemli olur" kararı ayakta.

## 3. DC — `σ_çekme = 0,971` ve bu bir **bilimsel sonuç**

PROTOKOL-DY §8.4: `σ_çekme = |b_DY2 − b_DC| / b_DY2`.

    |2,7480 − 0,0807| / 2,7480 = 0,9706   →   CEKME DARTTA DAHA ETKILI

Kıyas sahnesinde bu etki `0,23` idi. **DART sahnesinde `4,2` kat büyük.**
Sayılar:

| | çekme KAPALI (DY2) | çekme AÇIK (DC) |
|---|---|---|
| `β` | 3,748 | **1,081** |
| `M_ejekta` | `1,964e7 kg` | **`278 kg`** |
| dondurulan | 4103 | **34** |
| koni | 85,2° | 47,9° |

`T_m = Y₀/μ_f ≈ 16,7 Pa`'lık bir çekme dayanımı, DART sahnesinde ejektayı
**tamamen** durduruyor: kaçan kütle `70 000` kat düşüyor ve `β` birin
hemen üstüne iniyor.

### Kayıt değil, sonuç

> **Gözlenen `β ≈ 3,5`, çekme açıkken HİÇBİR `Y₀` ile elde edilemez.**
> `Y₀ = 10 Pa`'da (önselin en zayıf bölgesi) bile `β = 1,081` çıkıyor;
> `Y₀` büyüdükçe `T_m = Y₀/μ_f` de büyüdüğü için durum **kötüleşir**.
> Dolayısıyla DART'ın ölçtüğü momentum aktarımı, Dimorphos matrisinin
> `~10 m` ölçeğinde **esasen sıfır çekme dayanımına** sahip olmasını
> **gerektirir**.

Bu, ADR-0056'nın fizik gerekçesini (moloz yığını çekmeye dayanmaz)
**gözlemle** destekliyor. Kararı sonuca göre vermedik — karar
2026-10-05'te, DC koşarken verildi — ama sonuç kararı doğruladı.

**Bütçeye hâlâ girmiyor** (ADR-0056 §3): reddedilen bir model belirsizlik
değildir. Terim `matris_cekme_olculen = 0,971` olarak kayıtta ve her
raporda **koşullu duyarlılık** cümlesi olarak duruyor.

## 4. DN — `σ_çarpma_yeri = 0,0302`: L12'nin `0,10`'u **3,3 kat büyüktü**

PROTOKOL-DY §9.4: nişan kutuptan `25,0 m` kirişe taşındı (gerçek DART
kaçıklığı, Daly 2023). `β` `3,748 → 3,665`.

    |2,7480 − 2,6650| / 2,7480 = 0,03019   →   L12 ILE UYUMLU

**Eşik sırtında:** `KACIKLIK ONEMSIZ` dalı `≤ 0,03` ve ölçülen değer onu
**`0,00019` ile** aşıyor. Yargı kilitli kurala göre `L12 ILE UYUMLU`;
sayı kıl payı farkla öteki dala düşmedi ve bunu **olduğu gibi** yazıyorum.
Kural değiştirilmedi.

### Ama `β` yine yanıltıcı

| | DY2 (kutup) | DN (`25 m` kaçık) | fark |
|---|---|---|---|
| `β` | 3,748 | 3,665 | **`%2,2`** |
| `M_ejekta` | 1,964e7 | 2,321e7 | **`%18`** |
| koni tam açısı | 85,2° | **107,7°** | **`%26`** |
| `t50` | 0,541 s | 0,845 s | **`%56`** |
| `v_ort` (kaçan) | — | `0,491 m/s` | — |

Üçüncü kez aynı desen (KAYIT-072 şekil, KAYIT-074 gerçeklem, şimdi
kaçıklık): **`β` değişmiyor, ejektanın dağılımı değişiyor.** Eğik ve kaçık
çarpma koniyi `85° → 108°` açıyor — `β`'nın kör olduğu yer tam burası.

## 5. Ejekta ayrışması — önçarpan **sahneye bağlı** (KAYIT-073'e düzeltme)

İlk kez gerçek koşularda kaydedildi (`fizik_tani["ejekta_ayrismasi"]`):

| kol | `M_kaçan` | `v_ort` | `kos_ort` | `M·v·kos/p` | `b` | oran |
|---|---|---|---|---|---|---|
| DO1 | 3,658e6 | 1,980 | 0,7986 | 1,624 | 1,625 | **1,000** |
| DO2 | 9,251e5 | 4,466 | 0,7524 | 0,873 | 0,874 | **0,999** |
| DN | 2,416e7 | 0,4913 | 0,8047 | 2,682 | 2,665 | **1,006** |

**Kimlik DART sahnesinde TAM:** `M·v·kos/(p·b) = 1,000 ± 0,006`.
KAYIT-073'ün W2'de ölçtüğü `0,835` **o sahneye özgüymüş** (momentum
defterinin `R` yüzeyi `75 m` küreye göre tanımlı). Kod'a
`ONCARPAN_K_DART = 1,000` olarak eklendi; `b_tahmin` bir **tanı**,
kilitli sayı değil.

**Götürme burada da var ve daha net:** `Y₀` `500 → 5000` giderken
`M_kaçan` `4` kat düşüyor ama `v_ort` `2,3` kat artıyor — `β` ikisinin
çarpımını görüyor.

**DC'de ayrışma okunamadı** ve bu doğru davranış: kaçan parçacık `4`,
eşik `30` → `ejekta_bilesenleri` reddetti (*"üç çarpan gürültüden
okunamaz"*). Koruma çalıştı.

## 6. Krater: **iki ölçü de `600 s`'de krateri vermiyor**

İlk gerçek yan yana karşılaştırma (A19/A114):

| kol | `crater_profile` (`y[1]`) | `krater_yerdegistirme` |
|---|---|---|
| DO1 | **`−3,02 m`** | `0,757 m` (çap `nan`) |
| DO2 | **`−2,97 m`** | `0,564 m` (çap `nan`) |
| DC | **`−3,83 m`** | `0,383 m` (çap `nan`) |
| DN | **RED** (kutu 0'da 3 parçacık) | `0,634 m` (çap `95,62 m`) |

İki ayrı kusur birlikte görünüyor:

1. **`crater_profile` negatif derinlik veriyor** (`−3 m`) ya da reddediyor.
   A19'un *"yokken var, varken yok"* tanısı aynen duruyor.
2. **`krater_yerdegistirme` reddetmiyor** (A114'ün kök nedeni yapısal
   olarak yok — ADR-0055 §2d doğrulandı) **ama** verdiği derinlik
   `0,4 – 0,8 m`, yani DART ölçeğinde beklenen onlarca metrenin çok
   altında; çapı da üç kolda `nan`.

**Teşhis:** `600 s`'de krater **yok**. Kazı malzemesi gitmiş, kalan
yüzey oturmuş. İki ölçü de "kraterin kalıntısını" ölçüyor, krateri değil.

> **PROTOKOL-HT için sonucu:** Hera krater öngörüsü `600 s`'den
> okunamaz. Krater, **oluştuğu ve çökmeden önceki** bir anda
> (`t ~ 10 – 60 s` mertebesi) ve daha yüksek çözünürlükte ölçülmeli.
> ADR-0055 §3'ün `2c` seçeneği (krateri HT'nin kendi turuna taşımak)
> bu ölçümle **gerekli** hale geldi — tercih değil.

DN'nin `y: null` olması A114'ün **dördüncü** canlı örneği: DART sahnesinin
dört koşusundan (`DY2`, `DM`, `DN` ve kıyas için `DT`) **üçü** `y`
üretmedi.

## 7. Bütçenin durumu — **ödünç terim kalmadı**

| terim | ödünç | **ölçülmüş** | nerede |
|---|---|---|---|
| `cozunurluk_uzak` | `0,15` | `0,004` | KAYIT-067 |
| `cozunurluk_yakin` | — | `0,053` | KAYIT-071 |
| `hedef_sekli` | `0,20` | `0,009` | KAYIT-072 |
| `plato` | `0,01` | `0,016` | KAYIT-072 |
| `gerceklem_beta` | `0,033` | `0,013` | KAYIT-074 |
| `gerceklem_M_ejekta` | `0,15` | `0,129` | KAYIT-074 |
| `mermi_geometrisi` | `0,15` | `0,134`* | KAYIT-074 |
| **`carpma_yeri`** | **`0,10`** | **`0,030`** | **bu kayıt** |
| **`matris_cekme`** | — | **`0,971`*** | **bu kayıt** |
| `carpma_acisi` | `0,05` | ölçülmedi | kapsam dışı |

`*` paydaya girmez (reddedilen alternatif ya da daha kaba yaklaşım);
koşullu duyarlılık olarak raporlanır.

**Paydaya giren altı terim** (`β` için), hepsi ölçülmüş:
`gerceklem_beta_DART 0,013` · `cozunurluk_uzak 0,004` ·
`cozunurluk_yakin 0,053` · `plato_olculen_DART 0,016` ·
`hedef_sekli_olculen 0,009` · **`carpma_yeri_olculen 0,030`**
→ bağıl toplam **`0,0658`**, yani `σ_model = 0,181` (`b = 2,748`).
Eski ödünç kümeyle `0,291` idi: **payda `%38` küçüldü** ve sınav
**zorlaştı**.

## 8. Dürüst değerlendirme

- **İyi:** üç kilitli yargı da net; `Y₀` beklediğimden `4,6` kat iyi
  tanımlanabilir; bütçede ödünç terim kalmadı; DC'den bir **bilimsel
  sonuç** çıktı (gözlem `~0` çekme dayanımı gerektiriyor).
- **Düzeltme:** KAYIT-073'ün `0,835` önçarpanı evrensel değil, **sahneye
  bağlı**. DART sahnesinde `1,000`. Yan yana yazıldı.
- **Yanlış çıkan tahminim:** W2'den taşınan `β(Y₀)` eğimi `2,4` kat
  yanlıştı. ADR-0053'ün `644 Pa`'sı bu yüzden kaydı. Kararın kendisi
  doğru çıktı ama **gerekçesinin sayısı** yanlıştı — ve bunu DO'nun
  ölçmesi için zaten protokol yazmıştım.
- **Yeni açılan iş:** krater `600 s`'de ölçülemiyor. PROTOKOL-HT yeniden
  yazılacak ve kendi turu gerekecek (`~3-5` koşu).
- **Eşik sırtı:** `σ_çarpma_yeri` `0,0302`, eşik `0,03`. `0,0002` ile
  öteki dala düşmedi. Kural değiştirilmedi, sayı olduğu gibi yazıldı.
