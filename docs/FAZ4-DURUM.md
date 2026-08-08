# FAZ 4 — durum (2026-08-08)

> Bu belge **ne bittiğini ve ne bitmediğini** ayırır. Bitmemiş bir işi
> bitmiş göstermek RULES.txt'in ilk maddesine aykırıdır.

---

## 1. Görev tablosu

| # | görev | kod | ölçüm | kanıt |
|---|---|---|---|---|
| 4.1 | Kütle oranı toleransı | ✔ | **✔** | KAYIT-019…024; A elendi |
| 4.2 | Yaklaşımın seçimi | ✔ | **✔** | ADR-0041 (A′ kilitlendi) |
| 4.3 | Uygulama + GPU doğrulama | ✔ | **✔** | KAYIT-034 |
| 4.3b | `Ω` çelişkisi | ✔ | **✔** | KAYIT-035, ADR-0042 |
| — | ADR-0041 §5 boşluk 3 | ✔ | **✔** | KAYIT-036, KAYIT-037 |
| 4.4 | DART'ta çözünürlük yakınsaması | **✔** | **kısmen** | yerelde 4/6 kol; **A1 düştü** (§1b) |
| 4.5 | Gereken simüle süre | **✔** | ✘ | `settling_time` + koşucu |
| 4.6 | Sentetik kurtarma | **✔** | ✘ (kuru kip ✔) | `inference/` paketi |
| 4.7 | G4 kapısı | **✔** | ✘ | `g4_gate` + kapı raporu |

> **FAZ 4'ün kodu bitti; ölçümlerin dördü bitmedi.** 4.4–4.7 yazıldı,
> yerelde sınandı, uçtan uca bağlandı — ama GPU'da **koşulmadı**.

---

## 1b. YEREL GPU — TRUBA bağımlılığı **kırıldı** (2026-08-08)

Kota dolu ama yerelde bir GPU var ve **yeterli**:

| | ölçülen |
|---|---|
| kart | RTX 3050 Laptop, 4 GiB, sm_86 |
| adım maliyeti | `24 659 µs/1000 parçacık` (H200: `8 658`) |
| **yavaşlık** | **`2,85×`** — tahminim `~400×` idi, **yanlıştı** |
| atlanan GPU testleri | `test_adaptive_h_gpu` **4/4**, `test_solid_cross` **13/13** |

FAZ 4.4 yerelde koşuldu (**4/6 kol**, son ikisi PC kapanacağı için elle
durduruldu) ve **en önemli teknik bulguyu** verdi:

### G4-A1 DÜŞTÜ — mermi çözülmemiş

| kurulum | yerel aralık | **A1** | eşik |
|---|---|---|---|
| `s7_λ2` | 3,500 m | **0,215** | 2,0 |
| `s7_λ3` | 2,333 m | **0,322** | 2,0 |
| `s5_λ2` | 2,500 m | **0,300** | 2,0 |

Gereken `λ = 18,6` (**6478:1**) — ölçülmüş her şeyin (`λ ≤ 3`) ötesinde.
Bedeli `r_iç = 3 m` ile `96` GPU-günü ve **`9,3×`'i saf CFL**; tek
global adımlı şemada **küçültülemez**.
Ayrıntı: [KAYIT-041](defter/KAYIT-041_2026-08-08_yerel-gpu-ve-mermi-cozulmemis.md).

---

## 2. Neden koşulmadı — dışsal engel, **kanıtlanmış**

| kontrol | sonuç |
|---|---|
| `GrpTRESMins` (limit) | `cpu=7 200 000` |
| `GrpTRESRaw` (harcanan) | **`cpu=7 200 096`** — 96 dk aşılmış |
| benim payım | `cpu=133 053` (`%1,8`) |
| erişilebilen hesap | **yalnızca** `egitimg16` / `cuda` / QOS `normal` |
| donanım | **boş** (21 idle düğüm) — ama tahsis yok |
| **karar sınaması** | 1 dk, 16 çekirdek, 1 GPU, yalnızca `echo` → **`PENDING (AssocGrpCPUMinutesLimit)`** |

```
JOB 1460700 CANCELLED — exceeds association group max TRES(cpu) minutes
                        of 7200000 with 7200088
1460706  f44d  PENDING  (AssocGrpCPUMinutesLimit)
```

> **Kod sorunu değil, tahsis sorunu.** İş kuyrukta; kota yenilenince
> kendiliğinden koşacak. Etrafından dolaşılmadı.

Aynı nedenle HEAD'de **tam TRUBA doğrulaması yok** — son koşu `%23`'te
kesildi.

---

## 3. Ölçülenler (bu oturum)

### 4.3 — A′ GPU'da (job 1451544, 1460672)

| sınav | sonuç |
|---|---|
| skaler `h` ≡ tekdüze dizi `h`, bit düzeyinde | **True** |
| değişken `h`'de `Σ mᵢaᵢ` | **8,608e-17** |
| CPU = GPU (değişken `h`) | **True** (`<1e-10`) |
| GPU test takımı | **12/12** |

### 4.3b — `Ω` çelişkisi (job 1460675)

`h` sabit ⇒ `∂h/∂ρ = 0` ⇒ **`Ω ≡ 1`**. Ölçümle çözüldü:

| büyüklük | değer |
|---|---|
| `N_komşu` salınımı | **268,2 → 551,5** (`2,06×`) |
| çalışma aralığında yayılım | **%0,607** (tolerans %2) |
| karar | `sabit_h_yeterli` → **ADR-0042** |

### Boşluk 3 (job 1460697, 1460705) — **kapandı**

Beş kolun beşinde de taşma **%0,0000**:

| kol | `p` kaba | `p` iki bölgeli | `p` ince | **incelme kazanımı** |
|---|---|---|---|---|
| yalnız EOS | 1070,62 | 973,88 | 710,85 | %26,9 |
| + mukavemet | 1287,20 | 1167,09 | 851,83 | %27,6 |
| + gözeneklilik | 347,76 | 303,96 | 281,31 | %65,9 |
| **tam, A′** | 350,42 | **304,04** | 281,33 | **%67,1** |
| **tam, tek `h`** | 350,42 | **344,15** | 281,33 | **%9,1** |

> Aynı geometri, aynı malzeme, aynı `t`. Tek fark `h` politikası.
> **A′ aynı parçacık dağılımından 7,4 kat fazla kazanç çıkarıyor.**

### Yerelde ölçülenler (GPU'suz)

| büyüklük | değer |
|---|---|
| A′ DART sahnesinde tasarruf (`s=7/3,5`, `r_ince=25`) | **6,87×** |
| hedef kütle sapması | **2,25e-05** (G4-A3 eşiği `%0,5`) |
| çıkarım hattı, kuru kip: C1 / C2 / C3 | **%100 / 0,142 / 4,81×** |
| yerel test takımı | **830 geçti, 96 atlandı** (atlananlar GPU) |

---

## 3b. FAZ 5 hazırlığı — engellenmemiş kısım

Kota GPU ölçümlerini bloke ediyor ama FAZ 5'in iki ön koşulu **GPU
gerektirmiyor** ve ikisi de yapıldı:

### Ensemble **fizibil mi** — hesaplandı (KAYIT-040)

`1 s` simüle, 300 koşu:

| kurulum | GPU-günü | `~30` günlük bütçe | kullanılabilir mi |
|---|---|---|---|
| tekdüze kaba | 4,51 | ✔ | **✘** mermi çözülmemiş (ADR-0026) |
| **A′** | **9,73** | **✔** | **✔** |
| tekdüze ince | 66,85 | **✘** | ✔ |

> **A′, çözülmüş mermili bir ensemble'ı mümkün kılan tek seçenek.**
> ADR-0041'e **üçüncü kefe** olarak işlendi.

### Ensemble **kesintiye dayanıklı** — yazıldı

`~10` GPU-günü / `12` saatlik iş = kesinti **kaçınılmaz** (ve iş 1460700
zaten kesildi). `inference/ensemble.py` satır satır JSONL yazıyor;
yeniden başlatmada tamamlananlar atlanıyor, bozuk son satır ve tohum
uyuşmazlığı ayrıca ele alınıyor. On test.

---

## 4. Bu oturumda yazılan kod

| modül | ne yapar | test |
|---|---|---|
| `setup/refine.py` | A′'yı DART sahnesine bağlar | 8 |
| `validation/h_policy.py` | `Ω` çelişkisini çözen ölçüm | 13 |
| `validation/solid_interface.py` | boşluk 3 ölçümü | 34 |
| `validation/settling_time.py` | `β` durulma ölçütü | 13 |
| `validation/g4_gate.py` | kapıyı **kod** yargılar | 20 |
| `validation/g4_ozet.py` | ölçüm → kapı anahtarları | 13 |
| `inference/` (7 modül) | tasarım → vekil → posterior → G4-C + ileri + ensemble | 54 |
| `validation/ensemble_cost.py` | FAZ 5 ensemble bütçesi | 11 |

Koşucular: `faz43b`, `faz44`, `faz44b`, `faz45`, `faz46`, `faz47` ve
hepsini bağlayan `faz4_zincir.sh`.

---

## 5. Bu oturumda yakalanan kusurlar

**On üç kusur, hepsi kendi ölçüm düzeneğimde** — hiçbiri çözücüde:

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
| 10 | eski plato ölçütü "durulmadı" **diyemiyordu** | kod okundu |
| 11 | "yarım-pencere sınavı bağımsız" — **değil** | altı şekilde ölçüldü, oran tam 2 |
| 12 | `escape_speed_value` diye parametre yok | üç betikte birden |
| 13 | koşucunun **kendi** `GOZLENEBILIRLER`'i vardı | tek kaynağa indirildi |

Ve iki süreç hatası: metin değiştirme eşleşmeyi doğrulamadan `"ok"`
yazdı (iş `NameError` ile düştü); bir testte düzeltilen şeyin bozuk
olduğunu **ölçmeden** iddia ettim (ölçünce yanlış çıktı).

---

## 6. Kapanan riskler

| risk | durum |
|---|---|
| **R4** — krater çıkarımında `x_reference` zorunlu olmalı | **KAPANDI** — `None` gelirse `ValueError` |
| ADR-0041 §5 boşluk 3 | **KAPANDI** (koşullu — §7) |

---

## 7. FAZ 5'e geçilebilir mi

**Hayır.** Üç gerekçe:

1. **4.4–4.7 ölçülmedi.** Kod hazır, GPU'da koşulmadı.
2. **ADR-0041 ve ADR-0042 koşullu.** Ölçümler küp geometrisinde;
   DART geometrisinde doğrulanmadı. Boşluk 3 `λ = 2` (8:1) oranında
   kapandı, ADR-0026 daha yükseğini istiyor.
3. **G4 geçilmedi.** Kapı raporu üretildi ve `GEÇİLEMEDİ` diyor;
   on ölçütün onu da `koşulmadı`.

### FAZ 5 hazırlığı — durum

| ön koşul | durum |
|---|---|
| çıkarım makinesi doğrulanmış | **✔** (analitik haritaya karşı, kuru kip) |
| ensemble bütçesi biliniyor | **✔** (A′ ile fizibil) |
| ensemble kesintiye dayanıklı | **✔** |
| ileri model DART ölçeğinde çalışıyor | **✘** kota |
| gereken simüle süre | **✘** kota |
| G4 geçildi | **✘** kota |

### Kota yenilendiğinde — tek komut

```bash
sbatch f4z_job.sh    # scripts/faz4_zincir.sh: 4.4 -> 4.5 -> 4.6 -> 4.7
```

Zincir her adımın JSON'unu yazar, kapı hepsini okur ve raporu
**üretir**. Bir adım düşerse kalanlar yine koşar; kapı eksiği
`koşulmadı` sayar ve sessizce yeşil görünmez (çıkış kodu 1).
