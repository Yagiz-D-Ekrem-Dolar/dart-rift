# KAYIT-096 — Geç döküm yargısı: **1/4**, yol **yeterli değil**

**Tarih:** 2026-11-04 · **İşler:** `1639229_[0-3]` (**4 GPU**, ~`80` GPU-saat),
`6912804` / `6912813` / `6912817` / `6912824` / `6912832` (okuma + tanı, **0 GPU**)
**Protokol:** [HT EK-2](../truba/PROTOKOL-HT-EK2-2026-11-01.md) — yargı
**koşudan önce** yazıldı (`cb4a072`)
**Öncül:** [KAYIT-092](KAYIT-092_2026-11-01_doluluk-hipotezi-CURUDU-muhur-atildi-gec-dokum-gonderildi.md) §6

---

## 1. Koşu temiz bitti

Dört görev `COMPLETED`, `ExitCode 0:0`, `stderr` **boş**, duvar süresi
`19:57` – `22:53`. Dördü de `t ≈ 4990 s`'ye ulaştı (`~1,55e6` adım) —
`--azami-adim` tavanı `8e7`'ydi, yani **tavana çarpılmadı**. EK-2 §7'nin
*"sessiz kısa koşu kabul edilmez → BELİRSİZ"* şartı **devreye girmedi**.

## 2. Kilitli yargı uygulandı — **1/4**

Okuma: `scripts/havuz_krater_yeniden_oku.py` (EK-2 §5 bu betiği adıyla
anıyor), varsayılan `distan`. `600 s` sınıfları EK-2 §3'te yazılı:
dördü de ÖRTÜLÜ.

| idx | `Y₀` (Pa) | `600 s` | `5000 s` | **yargı (EK-2 §5)** |
|---:|---:|---|---|---|
| `16` | 1,15 | ÖRTÜLÜ | **ÖLÇÜLDÜ** `d = +8,5928` m | **ÖRTÜ AÇILDI** |
| `20` | 6,46 | ÖRTÜLÜ | ÖRTÜLÜ | ÖRTÜ AÇILMADI |
| `84` | 18,57 | ÖRTÜLÜ | YÜZEY_YOK | BELİRSİZ |
| `87` | 1,35 | ÖRTÜLÜ | YÜZEY_YOK | BELİRSİZ |

EK-2 §5: *"Dört noktanın en az üçünde 'ÖRTÜ AÇILDI' çıkmazsa, geç döküm
yolu krater ön kaydı için **yeterli değildir** ve bu yazılır."*

> **YARGI: GEÇ DÖKÜM YOLU KRATER ÖN KAYDI İÇİN YETERLİ DEĞİLDİR.**
>
> Eşik `3/4`'tü ve **şimdi, sonuç görülmeden** konmuştu. Çıkan `1/4`.
> Eşik oynatılmıyor, yargı yazılıyor.

EK-2 §1'in öngördüğü sonuç devreye giriyor: *"'Hayır' ise `600 s` anlık
görüntüsünün sınırı kesinleşir"* ve mühürlü kaydın **geçici krater
şerhi son söz olur**. `ONKAYIT_HERA_KRATER_uretim66`'ya
**dokunulmadı** ve dokunulmayacak; `gec_dokum4` etiketiyle ikinci bir
mühür **kurulmuyor**, çünkü kurulacak bir sayı çıkmadı.

## 3. Niçin — ölçüldü, ve iki tahminim çürüdü

### 3.1 Çürüyen birinci tahmin: dondurma şeması örtüyü tutuyor

Kütükte `donmus = 4503 – 6168` parçacık görünce "örtü donduruldu, geri
düşemedi" diye düşündüm. Ölçüte baktım — `solver_solid.py:895`:

```
sec = act & (r > k_uzak*R) & (vr > v_esc)
```

`--dondurma-k 3.0`, `R ≈ 88 m` → `r > 264 m` **ve** kaçış üstü. Örtü
ise `r ≈ 60 – 110 m` ve tanımı gereği kaçış **altı**. **Dondurma örtüye
dokunmuyor.** Tahmin, ölçüm yapılmadan okumayla çürüdü.

### 3.2 Çürüyen ikinci tahmin: örtü oturmuş, hiç düşmeyecek

`idx 20`'nin örtü yüksekliği `600 s`'te `30,89` m, `5000 s`'te
`28,40` m — 4400 saniyede `2,5` m. "Demek oturmuş, hareketsiz" diye
düşündüm ve eksen kolonunun hızını ölçtüm. Çıkan: `|v_r| ≈ 2,0 – 2,3`
m/s, **hepsi dışa doğru**. Yani hareketsiz değil, **kaçıyor**.

### 3.3 Ve kendi tanımımda hata buldum

İlk bant taramasında yüksekliği **küresel en büyük yarıçapa**
(`R₀ ≈ 88,2` m) göre ölçtüm. Hedef üç eksenli (`88,5 × 87,0 × 58,0`) ve
**çarpma ekseni kısa eksen**: eksendeki referans yüzey `≈ 59` m.
Dolayısıyla bant etiketlerim **~29 m kayıktı**.

Düzeltildi: referans yüzey artık operatörün kendi `tepe_ad`ı gibi
hesaplanıyor (referans durumda, eksen kolonunda en büyük `z`) ve
lateral pencere operatörün kullandığı `2h = 5,6` m. Ölçülen
`z_ref = 58,89 / 59,29 / 58,92 / 59,21` m — kesişim tanısının
(KAYIT-094) bağımsız olarak verdiği `59,5` m ile tutuyor.

**Değişim sinyali kayık tanımda da hayatta kaldı** (aynı pencere, iki
zaman), ama mutlak yükseklikler yalnız düzeltilmiş hâlde geçerli.

## 4. Ölçülen mekanizma: **engel ile ölçülen şey aynı malzeme**

Eksen kolonu (`yan < 2h`), yüzeyin `0 – 60` m üstündeki parçacık sayısı:

| idx | `600 s` | `5000 s` |
|---:|---:|---:|
| `16` | 1 | **0** |
| `20` | **12** | **1** |
| `84` | **13** | **1** |
| `87` | **4** | **0** |

**Örtü dördünde de temizlendi.** Ama ölçülebilir hâle gelen yalnız
biri. Sebep: temizlendikten sonra kolonda `0 – 1` parçacık kalıyor ve
`h_eksen = 2,8` m ile bir `φ = 0,5` eş-yüzeyi **kurulamıyor** →
`YUZEY_YOK`.

Yani geç dökümün yaptığı şey "örtüyü indirip tabanı göstermek" değil,
**örtüyü ve onunla birlikte ölçülecek yüzeyi boşaltmak**. Engel ile
ölçülen şey aynı malzemedir.

Hızlar bunu tamamlıyor: yakın bantta `600 s`'te `|v_r| = 0,008 – 0,09`
m/s (kaçış `0,082` m/s mertebesi), uzak bantta (`120 – 400` m)
`|v_r| ≈ 2` m/s — **kaçışın 25 katı**. Yani ADR-0050/L1'in düşük ses
hızlı vekilinde geç evre **oturmuyor, boşaltıyor**. EK-2 §6 bu sınırı
niteliksel olarak yazmıştı (*"gerçek granüler oturmanın aynısı
değildir"*); bu ölçüm onu **niceliklendiriyor**.

## 5. Sınır: sayılar küçük

Bütün §4 analizi, yarıçapı `5,6` m olan bir kolonda **en çok 13**
parçacık üzerinde duruyor. Bu zayıf istatistiktir ve öyle
raporlanıyor. Kolonun boşalması **gerçek bir değişim** (`12 → 1`,
`13 → 1`), ama "boş kolon" ile "hiç çözülmemiş kolon" arasındaki ayrımı
bu çözünürlükte kesin çizemem. Daha ince bir koşu bunu değiştirebilir —
ve o koşu S10/A52'nin maliyet duvarının arkasında.

## 6. Bu koşu niçin boşa gitmedi

`80` GPU-saat harcandı ve kurulacak yeni bir mühür çıkmadı. Ama:

1. Mühürlü kaydın **geçici krater şerhi artık bir varsayım değil,
   sınanmış bir sınır**. "Daha uzun koşsak düzelir" savunması kapandı.
2. Vekilin geç evre davranışı **niceliklendi**: ejekta `25 × v_kaçış`
   ile ayrılıyor, geri birikmiyor.
3. Krater gözlemlisinin yapısal sınırı adlandırıldı: *engel ile ölçülen
   şey aynı malzeme.* Bu, daha uzun zaman ya da başka tarama yönüyle
   çözülmez (ADR-0063/0064 zincirinin neden tıkandığının cevabı).

## 7. Kilitli yargılara etkisi — YOK

`krater_derinlik` ADR-0055 ile isteğe bağlı, posteriora girmiyor.
`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), mühürlü spin ön kaydı (KAYIT-084) ve
mühürlü krater ön kaydı (`uretim66`, KAYIT-092) **etkilenmez**. Hiçbir
mühre dokunulmadı.
