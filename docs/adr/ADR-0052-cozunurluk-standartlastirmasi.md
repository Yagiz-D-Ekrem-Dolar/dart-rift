# ADR-0052 — Çözünürlükler arası standartlaştırma: ölçülmüş düzeltme, çarpma yasağı

**Durum:** ÖNERİ (karar kullanıcıda) · **Tarih:** 2026-09-28
**Öncül:** PROTOKOL-UY, PROTOKOL-UG, PROTOKOL-A98/A98K/A103/A104/A105,
[`docs/COZUNURLUK-STANDARDI.md`](../COZUNURLUK-STANDARDI.md), KAYIT-069
**Kod:** `inference/cozunurluk_standardi.py` · **Sınav:**
`tests/test_cozunurluk_standardi.py` (8)

---

## 1. Bağlam

Havuz (48–96 koşu) ucuz sayısal ayarla koşulmak zorunda; iddia ise mutlak
`β` üzerinden kuruluyor. Ölçülen ayar duyarlılıkları (hepsi aynı sahne,
aynı `θ`):

| eksen | etki (`β − 1`) |
|---|---|
| yumuşatma boyu `h` (kaba → doymuş) | **+%11,8** |
| geç evreye geçiş anı (0,2 s → yakınsak) | **+%18,7** |
| mermi parçacık sayısı (800 → 6400) | +%7,4 |
| geç evre yapay viskozitesi (`α` 1 → 0,1) | −%7,8 |
| matris çekme dayanımı (yok → `Y₀/μ_f`) | −%23 |
| uzak alan aralığı (7 → 3,5 m) | **+%0,4** (yok sayılabilir) |

Kullanıcının önerisi: "çözünürlükler arası bir formül bulup düzeltelim —
bilim değil clever engineering, ama bize lazım." Doğru; şartı şu: düzeltme
**ölçümden çıkmalı**, sonucu tutturmak için seçilmemeli.

## 2. Karar

**Standartlaştırma kabul edilir**, beş kuralla (kod bunları zorlar):

1. **Yalnız ölçülmüş çiftler.** `OLCUMLER` kaydındaki her satır hangi
   koşulardan çıktığını (`kanit`) ve tarihini taşır. Kayıtta olmayan
   dönüşüm `KeyError` ile reddedilir.
2. **Hata payı zorunlu.** `standartla` daima `beta_sigma` döndürür; bu pay
   posteriorda model eksikliğine girer.
3. **`β − 1` üzerinden.** `β`'daki `1` mermi katkısıdır; sayısal ayardan
   etkilenmez, ölçeklenmez.
4. **Ayrı ölçülmüş çarpanlar ÇARPILMAZ** (`carpan_carp` her zaman hata
   verir). Gerekçe ölçüldü: `1,118 × 1,187 = 1,327` → `β = 4,57`; birlikte
   ölçülen nokta `4,167`, literatür `4,18`. Çarpmak aynı eksikliği iki kez
   sayıyor (A103: katkılar toplamsal değil).
5. **İki noktalı ekstrapolasyon karar veremez.** `richardson_iki_nokta` her
   çağrıda uyarı döndürür; ölçüldü ki `p = 0,33` varsayımı `β_∞`'u `%27`
   fazla verirdi (5,11 vs ölçülen 4,01).

**Doyma eşiği:** `h_bağıl ≤ 0,75` (üç kol `%0,6` içinde). `yeterli_mi` bunu
sorar.

## 3. Reddedilen alternatifler

| alternatif | neden reddedildi |
|---|---|
| tek genel çarpan (ör. 1,13) her yere | çarpan eksene ve `θ`'ya göre kayıyor (geçiş ekseni `Y₀`'da `1,087–1,151`); eksenler bağımsız değil |
| Richardson ile `β_∞`'a ekstrapolasyon | `p` veriden çıkmıyor; iki noktayla `%27` sapma ölçüldü |
| düzeltmeyi yok sayıp "kontrast yeter" demek | Bitiş 3'ün sorusu **mutlak** `β`; kontrast argümanı yalnız `Y₀` için geçerliydi (M2), `f` için değil |
| çözünürlüğü sabitleyip hatayı görmezden gelmek | hata kaybolmaz, ölçülmemiş olur; ISEF'te ilk soru bu olur |

## 4. Sonucu ve sınırı

- Kaba merdiven + **doğru geçiş anı** literatürü `%0,3` farkla tutuyor
  (`4,167` vs `4,18`) → üretim kaba merdivenle koşulabilir **gibi görünüyor**.
- Ama `h` ekseni tek başına `+%11,8` diyor. İkisinin kesişiminde **tek bir
  ölçüm yok**. İki ihtimal ayırt edilmemiştir:
  (i) iki eksen bağımsız değil, düzeltme gereksiz;
  (ii) kaba koldaki uyum iki hatanın birbirini götürmesi (tesadüf).
- **Karar:** orta merdiven × `t_geçiş = 2,5 s` koşusu (~10–15 GPU-saat)
  yapılmadan üretim havuzu başlatılmaz. O koşu `OLCUMLER`'e üçüncü satırı
  ekleyecek ya da 4. kuralın gerekçesini güçlendirecek.
