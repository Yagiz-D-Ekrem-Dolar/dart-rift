# DEVAM — **2026-08-21 durumu** (yeni oturum buradan başlar)

> Bu bölüm, hiçbir önceki bağlam olmadan işe devam edebilmek için
> yazıldı. Altındaki `2026-08-03` bölümü **arşivdir**; sayıları
> bayattır, oraya karar için bakma.

---

## 0. Otuz saniyede durum

| | |
|---|---|
| **En büyük sonuç** | `β` **ölçümle çözüldü**: motorun `β = 1,4112`'si fizik değil, **çözülmemiş çarpışmanın artığı**. Hedef ejektası **yok** (kaçan kütle her koşuda merminin tamamı, hedef payı tam `0`). |
| **Kapı sonucu** | **`G4-B1` düşüyor** — yakınsama `λ₂`'de (hedef) ölçülmüştü, `λ₁`'de (mermi) eşiğin `268` katı. Kapı raporu hâlâ `GEÇİLDİ` diyor ve **yeniden üretilmeli**. |
| **Bekleyen karar** | **ADR-0047** (ÖNERİ) ve **ADR-0046** (kapsam) — ikisi de kullanıcıda. |
| **Açık sıkıntılar** | A11 (`krater_capi` ölü), A12, A17 (artık **ölçülmüş**, karar bekliyor). |
| **Depo** | `main`, GitHub'a push edildi. |
| **Koşan işler** | TRUBA `1515233` (`λ₂ = 4`), yerelde `λ₁ = 55`. |

---

## 1. Nerede çalışılıyor

### 1a. Yerel dizüstü — **üretim sayılarını birebir veriyor**

Bu turun en kullanışlı yan sonucu: TRUBA olmadan da ilerlenebilir.

| | |
|---|---|
| depo | `C:/Users/yagiz/Desktop/videos/dart-rift` |
| ortam | `.venv` (Python 3.12), warp `1.15.0` |
| GPU | RTX 3050 Laptop, 4 GB (fp64 zayıf ama sahne küçük) |

Doğrulanmış eşleşme:

| | TRUBA / kayıtlı | yerel |
|---|---|---|
| iki aşamalı `β` (`t_end = 0,2 s`) | `1,4112162721355217` | **aynı** |
| `A1` | `2,0390593305845943` | **aynı** |
| aktarım momentum hatası | `8,76e-15` | **aynı** |
| tek aşamalı `β` | `1,6175832076207557` | `1,617583208` |

Süre: iki aşamalı `t_end = 0,2 s` koşusu **~14 dk**. H100 aynısını
`55 s`'de yapıyor (`~15×`).

### 1b. TRUBA — çalışma alanı **yeniden kuruldu**

**Eski alan artık erişilemez.** MCP bağlantısı `egitimg16u1` olarak
açılıyor; `/arf/scratch/egitimg16u4` `Permission denied` ve
`/arf/scratch/egitimg16/driftclaude` **yok**. Bunun etrafından
dolaşılmadı, yenisi kuruldu:

| | |
|---|---|
| yol | `/arf/scratch/egitimg16u1/driftclaude` |
| depo | `dart-rift/` — GitHub'dan klon |
| ortam | `module load apps/truba-ai/gpu-2024.0` → Python `3.10.15`, numpy `1.26.4` |
| warp | `pylib/` altında `1.15.0` (login node'da **internet var**, `pip --target`) |
| çıktılar | `ciktilar/` |

Koşu ortamı:

```
export PYTHONPATH="$KOK/pylib:$KOK/dart-rift/src"
export WARP_CACHE_PATH="$KOK/.warp_cache"
```

**Kurulum tuzağı (kayda geçiyor):** `pip` numpy `2.x`'i de kurmaya
kalkar ve **dosya kotasına** takılıp yarım bırakır. Yarım
`pylib/numpy` **silinmeli** — yoksa modülün `1.26.4`'ünü sessizce
gölgeler. Kullanılan numpy modülünkidir.

**Kuyruk kuralı:** `kolyoz-cuda` için `--cpus-per-task` **16 ve
katları** olmalı (`-n 16` yetmiyor; doğrulayıcı `cpus_per_task`
istiyor). `palamut-cuda` düğümleri drain.

Koşan/koşmuş işlerin betikleri ve **ölçüt belgeleri** depoda:
`docs/truba/` — dosyalar TRUBA'daki kopyalarla **md5 eşleşiyor**.

---

## 2. `β` sonucu — kanıt zinciri

### 2a. `β`'nın payında hedeften hiçbir şey yok

| | |
|---|---|
| kaçan kütle (her koşuda) | `579,40 kg` = **DART'ın kütlesi** |
| kaçan **hedef** kütlesi | **`0,0000e+00`** (iş `1512733`) |
| `p_eksen` hedef | **`0`** |

### 2b. Sekme çözünürlükle **kayboluyor**

Tek değişen `λ₁` (mermi inceltmesi):

| `λ₁` | `A1` | `β` | `n_ejekta` |
|---|---|---|---|
| — (tek aşamalı, `λ = 2`) | `0,215` | `1,617583` | `803` |
| `19` | `2,039` | `1,411216` | `28` |
| `38` | `4,078` | `1,185066` | `40` |
| `55` | `5,903` | **koşuyor** | — |

Ardışık farklar `-0,206`, `-0,226` — azalma **yavaşlamıyor**. Limit
gözlemin `3,2225`'i değil **`β → 1`**.

### 2c. Hedef güçlü şok **görmüyor**

| | |
|---|---|
| merminin özgül `KE`'si | `1,888e7 J/kg` |
| iç enerjiye dönen | **`%29,7`** |
| `u_kaçan` (kütle ağırlıklı) | `5,613e6` = `1,19 × u_iv` → **şoklanmış** |
| sahnedeki **en yüksek** `u` | `5,644e6` — ve o **merminin** üstünde |

Yani sekme soğuk elastik bir yapay değil, ama merminin enerjisinin
`%70`'i kinetik kalıp geri çıkıyor ve hedef ısınmıyor.

---

## 3. Elenenler — **BUNLARI TEKRAR KOŞMA**

| aday | nasıl elendi | kanıt |
|---|---|---|
| koşu süresi | `t_end` `0,2 → 600 s` (`3000×`), `β` bit düzeyinde aynı | iş `1506765` |
| yerçekimi | `t = 100 s`'de `%0,14`; zayıf cisimde `%0,001` | `1501241/2`, `1515196` |
| matris `Y0` | `1 → 2,15e6 Pa` (6 mertebe) | `1506779`, FAZ 4.12 |
| **blok `Y0`** | `1e7 → 1 Pa`, yerçekimi açık | **`1515196`** |
| **hasar** (ADR-0027) | `Δβ = 5,9e-6`; `11 183` parçacığın `3`'ü kırılıyor | yerel, 21.08 |
| gözeneklilik | katı sahnede `+%7,5` — gereken `2,3×` | rapor A17 |
| `λ₂` (hedef ızgarası) | `Δβ = 0,000843` | G4-B1 |
| aktarımın durum sıfırlaması | etkilenen kütle payı `1e-3`–`1e-5` | yerel, 21.08 |

**Yakınsamamış tek yön `λ₁`** ve o `β`'yı gözlemden **uzağa** itiyor.

---

## 4. Bulunan kusurlar

| # | kusur | durum |
|---|---|---|
| 1 | İki aşamalı aktarım Grady-Kipp hasarını **siliyordu** (aşama-1'de `D_max = 0,562` → aktarımdan sonra `0`) | **DÜZELTİLDİ** — `coarsen_to_sites(hasar=)`, `WarpSolid3D(D0=)`, `Σ m D` defteri, 6 gerileme testi |
| 2 | FAZ 4'ün **bütün** koşuları `damage=enabled=False` ile koştu, oysa `configs/p3_dimorphos.yaml` `true` diyor | **AÇIK** — çelişki `tests/test_hasar_kolu.py` ile sabitlendi; hangi tarafın doğru olduğu bir karar |
| 3 | `_sahne_Y0` yalnızca `matrix_Y0`'ı eziyordu; `boulder_Y0` (hedefin kütlece `%36,3`'ü) hiç taranmamıştı | **DÜZELTİLDİ** — `--boulder-Y0` |
| 4 | Aktarım `rho`, `alpha`, `S`'yi sıfırlıyor | **ÖLÇÜLDÜ, küçük** (kütlece `1e-3`) — açık ama öncelikli değil |
| 5 | Rapor başlığı A3'ü kapandıktan sonra da açık listeliyordu | **DÜZELTİLDİ** (sayaç `4 → 3`) |

---

## 5. Bekleyen kararlar — **kullanıcıda**

1. **ADR-0047** (ÖNERİ) — `β` bu ileri modelin çıktısı değil. Dört
   seçenek: S1 krater bölgesini incelt · S2 model-form · S3 `β`'yı
   gözlenebilir olmaktan çıkar · S4 dış ölçekleme.
   Eğilim **S3**, ama S1'in sonucu (iş `1515233`) onu geri alabilir.
2. **ADR-0046** — çıkarım uzayını `S1`'e indirmek fiilen uygulandı
   ama kapsam kararı resmen kapatılmadı.
3. **`G4-B1`** — ADR-0047 kabul edilirse kapı raporu yeniden
   üretilmeli. Kapı betiğine **dokunulmadı**; bu bir karar.

### Kaba kuvvetin maliyeti (karar için)

`λ₂` inceltmesiyle ejekta perdesine inmek:

| aralık | `λ₂` | maliyet (bugüne göre) |
|---|---|---|
| `3,5 m` (bugün) | 2 | `1×` — `t_end = 5 s` için `1056 s` (H100) |
| `1,75 m` | 4 | `~5×` |
| `0,5 m` | 14 | `~150×` → **~9 gün**, tek nokta, `5 s` |
| `0,1 m` (gerçek ejekta ölçeği) | 70 | `~1,5e6×` |

Üstüne hedef ejektasının `2R`'yi geçmesi `~100 s` ister (`20×` daha).
Yani S1 doğru çıksa bile `β = 3,22`'ye kaba kuvvetle **ulaşılamaz**.

---

## 6. Koşan işler ve nasıl bakılır

| iş | ne | nerede |
|---|---|---|
| TRUBA `1515233` | `λ₂ = 4` — **çözünürlük mü mekanizma mı** | `ciktilar/c_1515233.out` |
| yerel `λ₁ = 55` | `β → 1` trendinin 4. noktası | scratchpad `f48_lam55.log` |

`1515233` ölçütü `docs/truba/OLCUT-krater-cozunurlugu.md`'de,
**koşudan önce** yazıldı. Karar `β`'ya **değil** `bekleyen` ve
`beta_bal`'a bağlı — çünkü `λ₂` büyüyünce `A1` de artıyor ve `β`'yı
`1`'e iter (karışık sinyal).

Son bakışta (`t = 1,77 / 5 s`): `beta_bal = 1,34064` **sabit**,
`hedef_ej = 2` (donmuş), `bekleyen = 0`.

---

## 7. Bu turda tekrarlanan **hata kalıpları**

Üç hipotezim de çürüdü ve üçü de ölçütü **önce** yazdığım için
temiz çürüdü:

1. *"Çarpma bir bloğun içine düşüyor"* — `r ≤ 8 m`'de blok payı `0`.
2. *"Ejekta ayrıklaştırma tabanının altında"* — krater içinde `223`
   parçacık var.
3. *"Mermi soğuk sekiyor"* — `u_kaçan = 1,19 × u_iv`.

Ayrıca **iki kez kendi iddiamı geri aldım**:

- *"Aktarımın durum sıfırlaması hasar kolunu kirletiyor"* — ölçtüm,
  kütlece binde bir.
- `β` için yazdığım `1,3 ≤ β < 2,0 → kısmi` bandı **kötü eşikti**:
  taban değerin kendisi o bandın içinde. Bandı sonradan
  değiştirmedim, sonucu *"oynamadı"* diye okudum.

---

## 8. Sık kullanılan komutlar

Yerel üretim kolu:

    .venv/Scripts/python.exe scripts/faz48_iki_asama.py --device cuda:0 --t-end 0.2 --out out.json

Mermi çözünürlüğü taraması:

    .venv/Scripts/python.exe scripts/faz48_iki_asama.py --device cuda:0 --lam1 38 --t-end 0.2 --out out.json

Hasar kolu (aktarım artık `D` taşıyor):

    .venv/Scripts/python.exe scripts/faz48_iki_asama.py --device cuda:0 --hasarli --t-end 0.2 --out out.json

Zayıf hedef (moloz yığını rejimi):

    .venv/Scripts/python.exe scripts/faz48_iki_asama.py --device cuda:0 --Y0 1 --boulder-Y0 1 --yercekimli --t-end 5 --out out.json

Analiz:

    .venv/Scripts/python.exe scripts/a17_hasar_karsilastir.py --kontrol K.son_durum.npz --hasarli H.son_durum.npz --beta-kontrol B --beta-referans R
    .venv/Scripts/python.exe scripts/a17_kacan_enerji.py --durum X.son_durum.npz
    .venv/Scripts/python.exe scripts/a17_carpma_bolgesi_malzemesi.py --tohum-sayisi 8

Lint (CI kapsamı) ve hızlı testler:

    .venv/Scripts/python.exe -m ruff check src tests scripts
    .venv/Scripts/python.exe -m pytest -m "not gpu and not warp" -q

TRUBA'da iş göndermek: `docs/truba/is_*.slurm` şablonlarını
`/arf/scratch/egitimg16u1/driftclaude/` altına koy ve `sbatch` et.

---

## 9. Kurallar — bu turda uyulanlar

- **Ölçüt koşudan önce yazılır ve commit'lenir.** Bu turdaki her
  koşunun ölçütü ayrı bir commit'te, koşudan önce.
- **Tesisat sınavı ölçütün ilk maddesidir.** İlk hasar çifti tam bu
  yüzden *"geçersiz"* sayıldı (`D_max = 0`) ve sonucu okunmadı.
- **Hiçbir satır silinmez** (`docs/FAZ4-SIKINTI-RAPORU.md`); düzelen
  şey `KAPANDI` işaretlenir, yanlış çıkan yargı yerinde kalır.
- **Etrafından dolaşılmaz.** TRUBA erişimi yoktu; yerelde koşuldu ve
  sonra TRUBA **yeniden kuruldu** — sonuç uydurulmadı.

---
---

# ARŞİV — 2026-08-03 durumu

> Aşağısı bayattır. G4 o tarihte geçilmemişti, kota doluydu ve `β`
> henüz ölçülmemişti. Karar için **yukarıya** bak.

﻿# DEVAM — projeyi kaldığı yerden sürdürme kılavuzu

Bu belge, bağlam kaybolsa bile **hatasız devam edebilmek** içindir. Depoyu ilk
kez gören birinin (veya sıfırdan başlayan bir oturumun) bilmesi gereken her
şey burada: nerede duruyoruz, neyin kanıtı var, neyin yok, hangi tuzaklar
zaten öğrenildi.

**Son güncelleme:** 2026-08-02 · **Durum:** FAZ 0–3 kanıtla tamamlandı, ama
**"0 hata" iddiası yanlıştı ve düzeltildi.**

> ### ⚠ DÜZELTME — hata ayıklama turu (2026-08-02)
>
> Burada daha önce şu yazıyordu: *"Açık kusur, xfail ve kanıtlanamayan kriter
> yok."* Bu, o an geçerli olan kanıta dayanıyordu (627 test, G3 7/7, 14
> kırmızı-takım maddesi temiz) ama **yanlıştı**. Silinmiyor, not düşülüyor
> (RULES.txt).
>
> Aktif bir hata ayıklama turu **altı kusur** buldu; ikisi bilimsel sonucu
> birinci mertebede bozuyordu:
>
> 1. **Hasar, `S` durum değişkenini bozuyordu.** `_eval()` adım başına iki kez
>    çağrıldığı için `S <- (1-D)^2 S` birikimliydi. Ölçüldü: hiçbir fizik
>    yokken **S 1,0e7 → 4,88e3 (5 adımda, 1000 kat)**.
> 2. **Krater çıkarıcı cismi küre sanıyordu.** Dimorphos 88×87×65 m.
>    **Kratersiz** elipsoitte **9,04 m hayali krater**; bilinen 8 m'lik çukur
>    17,43 m.
> 3. β duyarlılık taramasının **hız ekseni tamamen ölüydü** (`0,0`), kriter
>    yine geçiyordu.
> 4. Varsayılan hedef yarıçapı **%21 küçüktü** (`median(dist)`).
> 5. `period_change` belgesinde `dv/v ~ 1e-3` yazıyordu; gerçek **1,72e-02**.
> 6. `2.5 < beta_dart < 4.5` testi hiçbir şey ayırt etmiyordu.
>
> Hepsi düzeltildi, ölçümleriyle birlikte: **ADR-0029**, `docs/EKSIKLER.md` §0,
> **KAYIT-016**. Düzeltmelerden sonra dört kapı da yeniden geçti
> (iş 1448947, `c1ba7e0`).
>
> **"Kusursuz" bir daha iddia edilmeyecek.** Bu tur, aynı tabloya (627 test,
> G3 7/7, kırmızı takım 14/14, kapsam %97) bakıp "0 hata" demenin yanlış
> olduğunu gösterdi. Altı kusurun hepsi **kapsanan satırlardaydı** — ne
> testler ne kapsama onları bulabilirdi. Kapı geçmek, kusursuzluğun değil,
> **o kriterlerin** kanıtıdır.
>
> **Ders:** testler *parçaların doğruluğunu* sınıyordu, *bütünün davranışını*
> değil. Bir kriter geçtiğinde **geçme sebebinin de ölçülmüş olması gerekir**.

---

## 1. Proje tek paragrafta

NASA'nın DART aracının Dimorphos'a çarpmasından elde edilen verilerden,
asteroidin **iç yapısını olasılıksal olarak** geri hesaplamak ve bu tahmini
ESA'nın Hera aracı ölçmeden **önce** kilitlemek. Bu depo o çıkarımın
dayanacağı **motordur**: deterministik altyapı (FAZ 0), SPH şok-fiziği
çekirdeği (FAZ 1), gerçek malzeme fiziği (FAZ 2).

Çıkarımın asıl parametresi **gözenekliliktir**. Bu yüzden P-α modelinin
doğruluğu, diğer her şeyden önce gelir.

---

## 2. Nerede duruyoruz

| Kapı | Sonuç | Kanıt |
|---|---|---|
| G0 | **GEÇTİ** | iş 1448947 (`c1ba7e0`) |
| G1 | **GEÇTİ** | iş 1448947 (`c1ba7e0`) |
| G2 | **GEÇTİ** | iş 1448947 (`c1ba7e0`) |
| **G3** | **GEÇTİ** 7/7 | iş 1448947 (`c1ba7e0`) |

Dördü de aynı commit üzerinde, TRUBA kolyoz12 / H100'de, hata ayıklama
turunun **altı düzeltmesi uygulandıktan sonra**. **639 test geçiyor / 0
kaldı**, kapsam **%96,5**, kırmızı takım **14/14 temiz**, 28 kriterin tamamı.
İş COMPLETED, çıkış kodu 0:0, süre 01:30:55.

Kanıt: [G0–G3 hata ayıklama sonrası](docs/evidence/G0-G3_HATA-AYIKLAMA-SONRASI_c1ba7e0.md)

Sahne karması iki bağımsız ortamda birebir aynı: `6d6f1d10eaff64e2…`
(Linux/numpy 1.26.4 ve Windows/numpy 2.5.1). Bu eşitlik önce tutmuyordu —
bkz. [ADR-0025](docs/adr/ADR-0025-sahne-makineler-arasi-determinizm.md).

Ayrıntı: [G3 kanıtı](docs/evidence/G3_GATE_0b88ae9.md) ·
**eksikler kaydı:** [docs/EKSIKLER.md](docs/EKSIKLER.md).

### FAZ 3 sonrası kapatılan eksikler

| eksik | sonuç | kayıt |
|---|---|---|
| Hasar/kırılma modeli (`D = 0`) | Grady-Kipp + Weibull, 32 test | ADR-0027 |
| Makineler arası determinizm | 2 kusur bulundu ve düzeltildi | ADR-0025 |
| Blok kesri hedefe ulaşmıyordu | 0,267 → **0,303** | EKSIKLER §4 |
| Uzun koşu kararlılığı | **30 000 adım**, hata birebir sabit | ADR-0028 |
| Çarpma enerji kayması | `O(dt)` kesme hatası, CFL ile ayarlanır | ADR-0028 |
| Mermi çözünürlüğü | **1,72e9 parçacık** gerekiyor → FAZ 4 yerel incelme | ADR-0026 |
| PDS veri manifestosu (C7) | 10 ürün çekildi, **10/10 resmi MD5** doğrulandı | EKSIKLER §7 |

Açık kusur **yok**. `xfail` **yok**.

**Kanıtlanamayan kriter yok.** G3 C7 (PDS veri manifestosu) kapandı: paket
`urn:nasa:pds:dart_shapemodel::1.0` çekildi, **10/10 ürün arşivin resmi
MD5'iyle** doğrulandı, kapı sağlamaları diskte yeniden hesaplayıp eşleştirdi.
Okunan Dimorphos eşdeğer yarıçapı **75,0 m** (Daly ve dig. 2023 ile birebir).

> **BİRİM:** PDS şekil modelleri **kilometre** cinsindendir. `obj_units: km`
> yazılmazsa cisim 1000 kat küçük olur ve hiçbir yerde hata vermeden bütün
> fizik anlamsızlaşır. `load_obj` dönüşümü sessizce yapmaz.

Taşınan tek tasarım kararı: **mermi çözünürlüğü** (ADR-0026) — FAZ 4 yerel
incelme gerektirir.

---

## 3. Çalışma ortamı — kritik ayrıntılar

### TRUBA

```
Kullanıcı : egitimg16u4
Çalışma   : /arf/scratch/egitimg16/driftclaude
Depo      : /arf/scratch/egitimg16/driftclaude/dart-rift
Kütüphane : /arf/scratch/egitimg16/driftclaude/pylib   (wheel'ler açılmış)
Modül     : apps/truba-ai/gpu-2024.0  → Python 3.10.15, NumPy 1.26.4
```

**TRUBA'ya pip/conda ile kurulum YAPILMAZ** (kural). Paketler wheel açılarak
`PYTHONPATH` üzerinden kullanılır.

**NumPy 1.26.4 tabandır.** NumPy 2.0+ API'leri (`np.trapezoid`, `np.concat`,
…) kullanılamaz — yerelde geçer, kümede kırar. Bu bir kez gerçekten oldu ve
G1 kapısında iki ölçütü birden düşürdü (ADR-0005).

### Arızalı düğümler (betiklere gömülü)

```
kolyoz13  → nvidia-smi H100'ü GÖRÜYOR ama warp "CUDA error 999" ile init edemiyor
palamut5  → /arf'a VERİ yazamıyor (metadata yazılır, dd 5MB → 0 bayt)
palamut6  → /arf'tan büyük dosya OKUYAMIYOR (warp import'u sessizce çöker)
```

Sağlam doğrulanan: `kolyoz9`, `kolyoz14`, `kolyoz19`, `kolyoz23`, `palamut4`.

Dışlama listesi `#SBATCH --exclude` ile **betiklerin içindedir**, yorumda
değil. Sebebi acı: "sbatch --exclude=… ile gönder" diye yazan bir yorum vardı,
unutuldu ve iş tam da o düğüme düştü.

### Kapı koşuları

```bash
sbatch slurm/faz0_g0_gate.sh      # G0
```

```bash
sbatch slurm/faz12_gates.sh       # G1 + G2 (~45 dk)
```

Her iki betik de donanım arızasında **75 (EX_TEMPFAIL)** ile çıkar — arıza,
kapı sonucundan ayrılır.

### Yerel

Windows + RTX 3050 (sm_86). FP64 hızı FP32'nin 1/32'si, yani GPU testleri
TRUBA'dan ~50 kat yavaş. Tam paket ~20 dakika.

```bash
pytest -q                          # tam paket (620 test)
```

```bash
pytest -q -m "not gpu"             # GPU'suz
```

`.coveragerc` varsayılan adda olduğu için bayrak gerekmez.

---

## 4. Mimarinin değişmez kuralları

1. **Her GPU çekirdeğinin Warp'tan bağımsız bir NumPy FP64 referansı vardır**
   ve ikisi çapraz kontrol edilir (< 1e-8). Bu kural iki kez gerçek çekirdek
   hatası yakaladı (ADR-0015, ADR-0019). Yeni çekirdek eklerken çapraz
   kontrolü de ekleyin — kapsam raporu bunu hatırlatmaz (ADR-0016).

2. **Determinizm zorunludur** (ADR-0002). Aynı girdi → bit-eşit çıktı.
   Ensemble çıkarımının ön koşulu: iki koşu arasındaki fark yalnızca
   parametreden gelebilir. Ölçekte doğrulandı (65 840 parçacıkta bit-eşit).

3. **Test geçilmediyse iddia edilmez.** Kapı koşucuları CUDA'sız ortamda
   "GEÇTİ" demez; `KANITLANAMADI` yazıp exit 2 döner. CI bunu her commit'te
   sınar.

4. **Sessiz değişiklik yasak.** Her büyük teknik karar bir ADR ile kayıtlı.
   Yanlış çıkan iddia silinmez, düzeltme notuyla kayda geçer.

---

## 5. Öğrenilmiş tuzaklar — tekrar düşmeyin

### 5.1 Kombinasyon boşlukları

**En verimli hata sınıfı bu.** İki modül ayrı ayrı doğru olup birlikte bozuk
olabilir. Bulunanlar:

- *süreklilik yoğunluğu + gözeneklilik*: hiçbir testte birlikte
  koşulmuyordu; başlangıç yoğunluğu `alpha0`'a bölünmüyordu ve malzeme
  13,35 GPa basınç altında başlıyordu (ADR-0022).
- *GPU + Barnes-Hut*: `mode="barnes_hut"` hiçbir testte çözücüye
  verilmemişti; GPU ağaç gezinmesi hiç çalıştırılmamıştı.
- *gradyan düzeltmesi + 1B*: `_embed3` boyut gömmesi `det(B)=0` yaptığı için
  düzeltme 1B'de **hiç** uygulanmıyordu (ADR-0019).

**Kural: kapsamayı modül başına değil, KOMBİNASYON başına düşünün.**

### 5.2 Denetlenmeyen tanı, olmayan tanıdır

- `grad_correction_used` hesaplanıyordu, kimse bakmıyordu → 1B'de %0.
- `kinetic_fraction` hesaplanıyordu, ADR "raporlanır" diyordu → raporlanmıyordu.

Bir alan üretiyorsanız, onu **denetleyen bir test** de yazın.

### 5.3 Ölçmeden optimize etmeyin — ve ölçüp vazgeçmeyi bilin

- Barnes-Hut gezinmesi, hızlandırdığı yöntemden **27 kat yavaştı** (saf NumPy
  dispatch yükü). Skaler aritmetiğe çevirince 10–14×.
- `np.einsum(optimize=True)` **her yerde kazanç değil**: 15 imzanın 5'i
  1,9–6,5× hızlanıyor, 3'ü 1,5–2,5 kat **yavaşlıyor**. İmza başına ölçüldü.
- Hash-grid'in adım içinde gereksiz yeniden kurulumu: mantıklı görünüyordu,
  ölçünce eval'in **binde beşi** çıktı → dokunulmadı.

### 5.4 Ayırt edici ölçüm kurun

"Hata var" yetmez; **hangi sınıftan** olduğunu ayıran bir ölçüm kurun:

- Enerji hatası sızıntı mı, kesme hatası mı? → **CFL'i yarıya indir.** Hata
  yarıya inerse `O(dt)` kesme hatasıdır (ADR-0020).
- Hata çözünürlükle **büyüyorsa** kesme hatası olamaz; sistematik bir
  boşluktur (ADR-0022 bunu böyle yakaladı).
- Sapma ayrıklaştırma farkı mı, toplama sırası mı? → **aynı çekirdekleri iki
  farklı cihazda** koştur; aradaki fark sıra etkisinin alt sınırıdır.

### 5.5 Kabuk / araç tuzakları

- PowerShell **heredoc desteklemez**; çok satırlı commit mesajı için Bash
  aracını kullanın.
- `Set-Content -Encoding utf8` **BOM ekler**; config dosyalarını bozar. Dosya
  yazarken `Write` aracını kullanın.
- PowerShell'de native exe'ye çift tırnaklı argüman geçerken parçalanabilir.
- `git add` bir pathspec'te hata verirse **kalan dosyalar sahnelenmez** ama
  commit yine de gidebilir — eksik commit oluşur. `git show --stat` ile
  doğrulayın.
- PowerShell `@'...'@` here-string'i, içinde **kesme işareti** geçen bir commit
  mesajında parçalandı (`z'ye` → `-m` argümanı bölündü, git pathspec hatası
  verdi ve commit atlandı). Çok satırlı commit mesajını **dosyaya yazıp
  `git commit -F dosya`** ile verin.
- Bir PowerShell komut satırı **ayrıştırma hatası verirse, `;` ile zincirlenen
  önceki komutlar da çalışmaz.** `git add ...; git commit -F - << EOF` denedim;
  satır hiç ayrıştırılamadı ve `git add` de yapılmadı. Sahnelemeyi
  `git diff --cached --name-only` ile **her seferinde** doğrulayın.

### TRUBA kuyruk kuralları — ölçülerek öğrenildi

- **`kolyoz-cuda` çekirdek sayısı 16'nın katı olmak zorunda.** `-c 8` denendi:
  `CPU count specification invalid`. Yani çekirdek küçültülemez.
- **`AssocGrpCpuLimit` ile beklemek, grup 0 CPU kullanırken bile olabiliyor.**
  Ölçülen: `sacctmgr` hesap için `cpu=512` gösteriyor, `squeue` grubun çalışan
  toplam CPU'sunu 0 veriyor, iş yine de 16 CPU için bekliyor. Nedeni
  çözülemedi — muhtemelen eğitim hesapları için görünmeyen bir havuz sınırı.

  > **Düzeltme:** Önce "`--time` kısaltmak çözdü" diye yazmıştım. Yanlıştı:
  > `--time=02:00:00` ile sebep bir an `Priority` göründü, sonra yine
  > `AssocGrpCpuLimit`'e döndü. Süre kısaltmanın kotayı çözdüğü **kanıtlanmadı**;
  > süreyi gerçeğe yakın tutmak yine de doğru davranış ama bu sorunun çaresi
  > değil. Yapılacak tek şey beklemek.
- **`sacct` bir kapının sonucunu okumak için YANLIŞ YERDİR.** `run_g3_gate.py`
  rc=3 döndürür (kanıtlanabilirler geçti, biri kanıtlanamadı) ve SLURM bunu
  `FAILED` gösterir. Doğru yer: `gate_runs/g3_*/G3_report.md`.

### Koşan bir işin ağacını değiştirmeyin

Kapı koşarken depoyu `git pull` etmek ya da yerelde dosya düzenlemek, kanıtı
**hangi commit'e ait olduğu belirsiz** hale getirir. Bunu bu fazda iki kez
yaptım; ikisinde de koşuyu iptal edip baştan başlamak zorunda kaldım.

Kural: **kapı kanıtı, iddia edilen commit üzerinde ve o commit dondurulmuşken
üretilir.** Kod değişecekse önce değişikliği bitirin, commit edin, sonra tek
temiz koşu yapın.

### FAZ 3'te öğrenilenler — ölçme yöntemi tuzakları

Bu fazın altı kusurundan **dördü kodda değil ölçmedeydi**. Ortak kalıp: *en
kötü örneklenen kutunun ya da en küçük paydanın belirlediği bir istatistik.*

- **Yerel değere bölmeyin.** Ağaç bayatlama hatasını yerel `|g|`'ye bölünce
  merkeze yakın parçacıklarda 0/0'a gidip "%14.8 hata" çıktı; gerçek değer
  maks`|g|`'ye göre %0.92 idi. Normalizasyonu global ölçeğe yapın.
- **Eşit açı ≠ eşit katı açı.** Küresel profil kutularını θ'da eşit aralıklarla
  bölerseniz eksene yakın kutu kürenin ~1.7e-4'ünü kapsar; oradaki medyan
  birkaç parçacıktan gelir, aşağı yanlıdır ve `max(sapma)` tam o gürültüyü
  seçer. Bilinen 20 m'lik çukur 40 m ölçüldü. **cos θ'da** bölün + kutu başına
  asgari örnek şartı koyun. (ADR-0017'deki hatanın aynısı — ikinci kez.)
- **Kutu sayısı N'e bağlı olmalı.** Sabit 60×120 yön kutusu, N=8000'de kutu
  başına ~1 örnek bırakır; "kutudaki en uzak parçacık" o zaman rastgele bir
  parçacıktır. Hiç çukuru olmayan bir kürede 41 m'lik hayali krater çıktı.
- **Sönümleme sinyali siler.** Yaklaşıklık hatasını sönümlemeli bir koşunun son
  konumlarından ölçmeye çalışmayın; sönümleme farkı yok eder. Doğrudan
  etkilenen büyüklüğü (burada ivmeyi) karşılaştırın.
- **Cebirsel özdeşlik çapraz kontrol değildir.** β'yı ejektadan ve bağlı
  kütleden hesaplayıp karşılaştırmak hiçbir şey doğrulamaz: momentum
  korunuyorsa ikisi özdeştir. Farkın adı `momentum_closure`'dır.
- **Sentetik doğrulama sahnesi de doğrulanmalıdır.** İlk sahnemde momentum
  korunmuyordu, ejekta hızları üslü yasadan gelmiyordu (R²=0.56 yakaladı) ve
  hedef çözünürlüğü krater çıkarıcı için yetersizdi (16 m → 2.95 m).

---

## 6. Ölçülmüş performans ve ölçek

TRUBA H200 (150 GB), tam FAZ 2 fiziği, `h/dx = 2` (~268 komşu):

| N | adım | µs/1000 parçacık | bellek |
|---|---|---|---|
| 1 000 000 | 287 ms | 126,9 | 1,09 GB |
| 2 744 000 | 805 ms | 131,6 | 2,00 GB |
| **11 239 424** | 3 009 ms | 123,6 | **5,99 GB** |

- Maliyet **N ile doğrusal**, gizli `O(N²)` yok.
- Bellek darboğaz **değil** — 11,2 M parçacık 150 GB'ın 6'sını kullanıyor.
- **Ama yukarıdaki tablo yerçekimi KAPALI.** Açıkken ~17 kat yavaş, çünkü
  Barnes-Hut ağacı **CPU'da Python'da** kuruluyor (~`O(N^1,2)`; 2 M
  parçacıkta tek kurulum ~29 s).

**FAZ 3 için karar gerekir** (ADR-0021'de üç seçenek): çarpma fazını
yerçekimsiz koşmak (literatürdeki standart), ağacı GPU'da kurmak, ya da K
adımda bir yenilemek.

Uzun koşu kararlılığı ölçüldü: 30 000 adımda enerji drifti **1,00×** (hiç
birikmiyor), kütle bit düzeyinde korunuyor.

---

## 7. Fizik kapsamı ve bilinen sınır

| Bileşen | Durum |
|---|---|
| Tillotson EOS | ✅ deneysel Hugoniot'a karşı doğrulandı (`Us = 3123 + 1,65·up`) |
| P-α gözeneklilik | ✅ **örtük** çözüm (ADR-0023) |
| Basınca bağlı dayanım + sürtünme | ✅ |
| Öz-yerçekimi (Barnes-Hut) | ✅ GPU↔CPU 3,1e-16 |
| **Hasar / kırılma (D)** | ❌ **yok** — `D = 0` sabit (P2 §1.3, STRETCH) |

Hasar modelinin yokluğu zayıf/gözenekli hedefler için savunulabilir (o
rejimde kratere hâkim mekanizma gözenek çökmesidir), ama **bir model
sınırlamasıdır** ve üretilecek her posteriorla birlikte belirtilmelidir.

---

## 8. Faz yol haritası (belge setinden)

Şartname seti `D-RIFT_Tum_Belgeler_2026-07-27.zip` içinde. Fazların tamamı:

| Faz | Belge | Durum |
|---|---|---|
| 0 | Altyapı ve Test İskeleti | ✅ G0 geçti |
| 1 | Hidrodinamik SPH Çekirdeği | ✅ G1 geçti |
| 2 | Katı, Porozite, Yerçekimi | ✅ G2 geçti |
| **3** | **Dimorphos, DART, Gözlenebilirler** | **sıradaki** |
| 4 | Doğrulama V4, Sentetik Kurtarma | |
| 5 | **Ensemble, Vekil Model, Bayes** | |
| 6 | Kilitli Hera Tahmini, Ön kayıt | |
| 7 | TÜBİTAK/ISEF, Açık Bilim, Derinleştirme | |

> **DÜZELTME (29.07.2026):** Bu belgenin önceki sürümünde "vekil (surrogate)
> model planı **belgelerde yok**" yazıyordu. **Yanlıştı.** İddia yalnızca bu
> deponun `docs/` içeriğine bakılarak kuruldu; şartname setinde bir fazın
> tamamı buna ayrılmış (`FAZ5_Ensemble_Vekil_Model_Bayes.pdf`). Ders: depo
> dokümanı, şartname setinin yerine geçmez.

### FAZ 3'e başlarken

1. **Yerçekimi kararını verin** (§6). Ölçüm var, seçim yok.
2. **Gereken simüle süreyi ölçün.** Momentum aktarımının (β) ne zaman
   durulduğu koşu maliyetini 10 kat değiştirir.
3. **DART kurulumunda çözünürlük yakınsaması** gösterin — krater çapı ve β'nın
   parçacık sayısına duyarlılığı.
4. Kapı ölçütlerini şartnameden alın, **gevşetmeyin**.

### FAZ 3'ün sonraki fazlara borcu

Sıralama tesadüf değil: FAZ 3'ün adı **"Gözlenebilirler"**, FAZ 4'ün adı
**"Sentetik Kurtarma"**, FAZ 5'in adı **"Ensemble, Vekil Model, Bayes"**.

- FAZ 3'te **hangi gözlenebilirlerin kaydedileceğine** karar verilir (krater
  çapı, β momentum aktarım katsayısı, ejekta konisi…). Vekil model tam olarak
  bunları öğrenecek — FAZ 3'te yanlış şey kaydedilirse FAZ 5'te düzeltilemez.
- FAZ 4'teki sentetik kurtarma ("bilinen parametrelerle üret, çıkarım onları
  geri bulabiliyor mu?") vekil modelin ve çıkarımın doğruluk kanıtıdır.
- FAZ 5'in ensemble'ı **uzay dolduran tasarımla** örneklenmelidir (Latin
  hypercube vb.), rastgele değil — birkaç yüz koşu doğrudan MCMC için az ama
  vekil model eğitmek için yeterlidir; vekil modelin varlık sebebi budur.

Maliyet (§6): yerçekimsiz 1 s'lik koşularla 300 koşu ≈ 30 GPU-günü — fizibil.

---

## 9. Belge haritası

| Yol | İçerik |
|---|---|
| `README.md` | genel bakış, kapı durumu, doğrulama sonuçları, marj analizi |
| `docs/FIZIBILITE.md` | motor hedefe yetiyor mu — ölçek, maliyet, fizik kapsamı |
| `docs/IZLENEBILIRLIK.md` | 38 gereksinimin kod + test + kanıt eşlemesi |
| `docs/adr/` | 23 mimari karar kaydı |
| `docs/defter/` | 14 mühendislik defteri kaydı (günlük çalışma) |
| `docs/evidence/` | kapı raporları, koşu künyeleriyle |

**Kritik ADR'ler:** 0002 (determinizm), 0008+0023 (P-α enerjisi), 0015
(süreklilik yoğunluğu), 0016 (kapsam politikası), 0020 (enerji mertebesi),
0022 (gözenekli başlangıç), 0021 (yerçekimi ağacı sınırı).
