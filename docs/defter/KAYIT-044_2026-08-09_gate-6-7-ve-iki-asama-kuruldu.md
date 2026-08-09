# KAYIT-044 — Kapıda 6/7, iki aşama kuruldu, uzay düzeltildi (2026-08-09)

**Kapsam:** FAZ 4.5 · 4.6 · ADR-0043 · ADR-0044
**Durum:** G4 `A1` dışında **A/B'nin tamamı geçti**; `C` koşuyor
**Öncül:** [KAYIT-043](KAYIT-043_2026-08-09_lagrange-aktarimi-engeli-kaldirdi.md)

---

## 1. G4 kapısı: **6/7** ölçülen ölçüt geçti

| | ölçülen | eşik | |
|---|---|---|---|
| A1 | **0,214638** | `≥ 2` | **DÜŞTÜ** |
| A2 | 66,5573 | `≥ 3` | GEÇTİ |
| A3 | 3,48e-04 | `< 0,005` | GEÇTİ |
| B1 | 8,43e-04 | `< 0,10` | GEÇTİ |
| **B2** | **1** | `≥ 1` | **GEÇTİ** ← yeni |
| B3 | 1 | `≥ 1` | GEÇTİ |
| **B4** | **−0,0037** | `< 1` | **GEÇTİ** ← yeni |
| C1/C2/C3 | — | | FAZ 4.6 koşuyor |

`A1` **tek** düşen ölçüt ve kapının tamamını tutuyor.

---

## 2. FAZ 4.5: `β` bir **basamak**, relaksasyon değil

`40 000` adım, `t = 4,63 s`, `17 757 s` duvar.

| örnek | `t` | `β` |
|---|---|---|
| 1–3 | `0,0088 → 0,0290 s` | **`1,000000`** (ejekta **yok**) |
| 4 | **`0,040558 s`** | **`1,583620`** ← geçiş |
| 5–400 | `0,052 → 4,632 s` | `1,583620` |

Geçişten sonraki yayılım **`2,18e-13`**. FAZ 4.4 aynı sahnede bağımsız
olarak aynı değeri vermişti (`5,6e-16`).

> ### Kendi iddiamı düzelttim
>
> *"`B2` ölçülemez"* yazmıştım (A9). **Yanlıştı**: seri sabit değil,
> `yayilim_rel = 0,369`. `sabit` bayrağı haklı olarak kalkmadı ve `B2`
> meşru biçimde yazıldı.
>
> Özü doğru kaldı: yerçekimi kapalı (`GravityParams(enabled=False)`)
> olduğu için ejekta balistik ve `β` **donuyor**. `t_durulma` aslında
> *"ejektanın kontrol yüzeyini ilk geçtiği an"*. `B2` geçti ama `B4`
> ile aynı ağırlıkta okunmamalı.

---

## 3. ADR-0044: çıkarım uzayı **tutarsızdı** — kabul edildi ve düzeltildi

FAZ 4.6'nın GPU ileri modeli hiç koşulmamıştı. **2 dakikalık** duman
testi: **`29/29` nokta düştü**.

**Çatışma 1:** `ρ_yığın = 1800` sabitken `matrix_alpha0`, `f_boulder`'ın
**fonksiyonu** (`f=0 → 1,500`, `f=0,5 → 2,625`). `DART_UZAYI` ikisini
bağımsız ilan ediyordu → kutunun uygulanabilir oranı **tam olarak `0`**.

**Çatışma 2:** `f_boulder = 0` `M1` sınıfında **yasak**, ama kutunun alt
sınırı `0` ve `factorial_design` köşeleri alıyor.

**Kod kusuru değil:** `build_rubble_pile`'ın reddi ADR-0030'u koruyor.
Kusur **uzayın tanımında**, ve `inference/design.py` hiçbir ADR'ye
bağlı değildi.

### Karar: **Seçenek 3** — ölçülerek desteklendi

`alpha0` yerine **`boulder_alpha0`** çıkarıma giriyor; `matrix_alpha0`
`ρ_yığın`dan **türetiliyor**.

| ölçüm | sonuç |
|---|---|
| Seçenek 3 kutusunun uygulanabilirliği | **`0/36` yasak** |
| yasak sınır (`f_boulder`) | `0,667 … ~1,0` — tasarımın `0,5`'i rahat içeride |
| `build_scene` eski eşlemeyle | `ValueError: %10,58 sapiyor` |
| `build_scene` **Seçenek 3** ile | **kuruluyor**, `ρ_yığın` hedefin `%5` içinde |

Eski yol (`DART_UZAYI`, `secenek3=False`) **silinmedi** — karar geri
alınabilir.

> §6 madde 2 (gözlenebilirler yeni parametreleri ayırt ediyor mu) ucuza
> **ölçülemedi**; deneme kaydedildi (`spacing=14` çok kaba, `β=1,00000`
> = *"ejekta saptanmadı"*). Ölçüm G4-C `C2`'nin içine taşındı: `C2`
> düşerse uzay dejenere demektir ve ADR yeniden açılır.

---

## 4. `A1`'in yolu: iki aşama **uçtan uca kuruldu**

`setup/two_stage.py` + `scripts/faz48_iki_asama.py`.

### Çözülen asıl sorun: **çifte sayım**

Aşama-1'in maddesi ile aşama-2'nin aynı bölgedeki parçacıkları ikisi
birden kalırsa o bölgenin kütlesi **iki katına** çıkar.

> Çıkarma ölçütü **Lagrange'cı**: aşama-2'nin `r_iç_aşama1` içinde
> **başlamış** parçacıkları atılır. Naif yol (*"yakın olanı at"*) keyfî
> bir mesafe eşiği isterdi.

| ön uçuş ölçümü | değer |
|---|---|
| korunum (kütle/momentum/enerji) | `2,8e-15` / `2,6e-16` / `1,8e-16` |
| atama mesafesi | `0,672` hücre |
| komşu medyanı (birleşik sahne) | **229** |
| **bölge kütle uyuşmazlığı** | **`%2,82`** |

`%2,82`: aşama-1'in ince bölgesi ile aşama-2'nin atılan bölgesi aynı
hacmi **iki farklı kafesle** örnekliyor. Aktarım korunumu bunu
**görmüyor**. Küçük ama **sistematik** ve tam da krater bölgesinde.

---

## 5. Gerçek bir çözücü hatası

Tam test takımı (**1156 geçti**, `2:48:51`) üç hata verdi, hepsi aynı
yerden:

```
AttributeError: 'WarpSPH1D' object has no attribute 'h_arr'
```

`WarpSPH1D._accumulate_continuity` 3B'ye özgü `h_arr`'ı geçiyordu; 1B
çekirdek **skaler** `h` bekliyor. Yani `track_continuity=True` olan 1B
çözücü **hiç çalışmamış**. Tek satır.

---

## 6. Ölçüm aracının **kendisi** iki kez bozuktu

| araç | önce | sonra |
|---|---|---|
| komşu tanısı (yalnızca aktarılanlar arasında sayıyordu) | medyan **27**, `<30` oranı **1,000** | medyan **229**, oranı **0,000** |
| `is_impactor` (`state_numpy()`'da o anahtar **yok**) | mermi kütlesi **hiç** çıkarılmıyordu | zorunlu parametre |

> Birincisi *"her aktarılan parçacık komşusuz"* diyordu — paniğe
> değecek bir sayı ve **tamamen artefakt**. İkincisi sessizdi.

Ayrıca **raporun kendi testi** de iki kusurluydu: kapanan sıkıntılar
*yerinde kaldığı* için hepsini açık sayıyordu, ve §2'nin iki ayrı
biçimini (tablo satırı / alt başlık) tanımıyordu.

---

## 7. Durum

| | |
|---|---|
| FAZ 4.4 | **bitti** |
| FAZ 4.5 | **bitti** — B2, B4 geçti |
| FAZ 4.6 | **koşuyor** (`3/60`, `~7` saat) |
| FAZ 4.7 | 4.6 bitince |
| FAZ 4.8 (iki aşama) | kuruldu, ön uçuşu geçti; gerçek koşu `~30` dk |
| ADR-0043 | **ÖNERİLDİ** — madde 3 (`λ=19` arayüz) ölçülemiyor |
| ADR-0044 | **KABUL EDİLDİ** |
| açık sıkıntı | **5** (A4 ve A10 kapandı) |
