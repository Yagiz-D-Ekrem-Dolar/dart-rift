# FAZ 4 — durum (2026-08-08)

> Bu belge **ne bittiğini ve ne bitmediğini** ayırır. Bitmemiş bir işi
> bitmiş göstermek RULES.txt'in ilk maddesine aykırıdır.

---

## 1. Görev tablosu

| # | görev | durum | kanıt |
|---|---|---|---|
| 4.1 | Kütle oranı toleransı | **BİTTİ** | KAYIT-019…024; A elendi |
| 4.2 | Yerel incelme yaklaşımının seçimi | **BİTTİ** | ADR-0041 (A′ kilitlendi) |
| 4.3 | Seçilen yaklaşımın uygulanması | **BİTTİ** | KAYIT-034 (GPU), ADR-0042 |
| 4.3b | `Ω` çelişkisinin çözümü | **BİTTİ** | KAYIT-035, ADR-0042 |
| — | ADR-0041 §5 boşluk 3 | **BİTTİ** | KAYIT-036, KAYIT-037 |
| **4.4** | **DART kurulumunda çözünürlük yakınsaması** | **KOD HAZIR, KOŞULMADI** | job 1460706 kuyrukta |
| 4.5 | Gereken simüle süre | **BAŞLANMADI** | — |
| 4.6 | Sentetik kurtarma | **BAŞLANMADI** | — |
| 4.7 | G4 kapısı | **BAŞLANMADI** | — |

> **FAZ 4 bitmedi.** 4.1–4.3 ve boşluk 3 bitti; 4.4 kodu yazıldı ve
> yerelde sınandı ama **GPU'da koşulmadı**; 4.5–4.7 başlamadı.

---

## 2. Neden 4.4 koşulmadı — dışsal engel

TRUBA hesabının **grup CPU-dakika kotası doldu**:

```
JOB 1460700 CANCELLED AT 2026-08-08T12:28:00 DUE TO TIME LIMIT
REASON: Job is at or exceeds association group max TRES(cpu) minutes
        of 7200000 with 7200088
```

Sonraki iş (1460706) kuyrukta ve nedeni açık:

```
1460706  f44d  PENDING  (AssocGrpCPUMinutesLimit)
```

> **Bu bir kod sorunu değil, bir tahsis sorunudur.** İş kuyrukta
> bırakıldı; kota yenilendiğinde kendiliğinden koşacak. Etrafından
> dolaşılmadı.

Aynı nedenle **HEAD'deki tam doğrulama koşusu da tamamlanamadı** —
%23'te kesildi. Son tam doğrulama `a203d44`'ten önceki HEAD'e aittir.

---

## 3. Bu oturumda ölçülenler

### 4.3 — A′ GPU'da (job 1451544, 1460672)

| sınav | sonuç |
|---|---|
| skaler `h` ≡ tekdüze dizi `h`, bit düzeyinde | **True** |
| değişken `h`'de `Σ mᵢaᵢ` | **8,608e-17** |
| değişken `h`'de CPU = GPU | **True** (`< 1e-10`) |
| GPU test takımı | **12/12** |

### 4.3b — `Ω` çelişkisi (job 1460675)

`h` sabit ⇒ `∂h/∂ρ = 0` ⇒ **`Ω ≡ 1` tam olarak**. Madde 2 ile madde 4
çelişiyordu; ölçümle çözüldü:

| büyüklük | değer |
|---|---|
| `N_komşu` salınımı (gerçek koşu) | **268,2 → 551,5** (`2,06×`) |
| çalışma aralığında yarıçap yayılımı | **%0,607** (tolerans %2) |
| karar | `sabit_h_yeterli` → **ADR-0042** |

### Boşluk 3 (job 1460697, 1460705)

Beş kolun beşinde de `arayuz_zararsiz`, taşma **%0,0000**:

| kol | `p` kaba | `p` iki bölgeli | `p` ince | **incelme kazanımı** |
|---|---|---|---|---|
| yalnız EOS | 1070,62 | 973,88 | 710,85 | %26,9 |
| + mukavemet | 1287,20 | 1167,09 | 851,83 | %27,6 |
| + gözeneklilik | 347,76 | 303,96 | 281,31 | %65,9 |
| **tam, A′** | 350,42 | **304,04** | 281,33 | **%67,1** |
| **tam, tek `h`** | 350,42 | **344,15** | 281,33 | **%9,1** |

> Son iki satır aynı geometri, aynı malzeme, aynı `t`. Tek fark `h`
> politikası. **A′ aynı parçacık dağılımından 7,4 kat fazla kazanç
> çıkarıyor.**

### 4.4 hazırlığı — A′ DART sahnesinde (yerelde ölçüldü)

`setup/refine.py` ile `radius = 82 m`, `s = 7,0/3,5`, `r_ince = 25 m`:

| büyüklük | değer |
|---|---|
| toplam parçacık | 11 164 |
| her yer ince olsaydı | 76 722 |
| **tasarruf** | **6,87×** |
| hedef kütle sapması | **2,25e-05** |

---

## 4. Bu oturumda yakalanan kusurlar

Hepsi **kendi ölçüm düzeneğimde**, hiçbiri çözücüde:

| # | kusur | nasıl yakalandı |
|---|---|---|
| 1 | "yayılım varsa suçlu komşu sayısıdır" — ayrıştırma yok | eğri hâlâ düşüyordu |
| 2 | tarama salınımı kapsamadı (523,6 < 551,5) | `judge` kapsam koruması |
| 3 | kapsadı ama çalışma aralığında tek nokta | `judge` iç-nokta koruması |
| 4 | `rho_ilk = 0,0` | `_eval()` çağrılmadan okunmuş |
| 5 | `E = 5e9 J` → buharlaşmanın 3 katı | koşu patladı |
| 6 | eşik `1,05·ρ₀` hiç tetiklenmedi | gözeneklilikte `ρ₀/α₀` |
| 7 | enjeksiyon yarıçapı kolun `dx`'ine bağlı | ince kol patladı (262144 NaN) |
| 8 | eşik `max\|v\|`'ye bağlı → kollarda farklı | `r = 0,839` = kutu köşesi |
| 9 | GPU testleri `PYTHONPATH=src` ile atlandı | 4 test "skipped" |
| — | *süreç:* metin değiştirme eşleşmeyi doğrulamadı | iş `NameError` ile düştü |

7 numaralı kusur ön koşul listesinde bir **boşluk** açığa çıkardı: üç
kolun enerjisi `3,8e-16` içinde aynıydı ama **dağıldığı bölge** farklıydı.
Yeni ön koşul eklendi.

---

## 5. FAZ 5'e geçilebilir mi

**Hayır — henüz değil.** Gerekçe:

1. **4.4 koşulmadı.** ADR-0041 ve ADR-0042 açıkça **koşullu** yazıldı:
   ölçümler küp geometrisinde yapıldı, DART geometrisinde değil. O
   koşul kaldırılmadan A′ kararı DART için kanıtlanmış sayılmaz.
2. **4.5–4.7 başlamadı.** G4 kapısı FAZ 5'in ön koşuludur.
3. **HEAD'de tam doğrulama yok** — son tam koşu kotadan kesildi.

### Kota yenilendiğinde sıra

| # | iş | hazır mı |
|---|---|---|
| 1 | job 1460706 (4.4 yakınsama) | **kuyrukta** |
| 2 | HEAD'de tam doğrulama | betik hazır |
| 3 | 4.5 gereken simüle süre | `measure_longrun.py` var |
| 4 | 4.6 sentetik kurtarma | başlanmadı |
| 5 | 4.7 G4 kapı raporu | başlanmadı |
