# DEVAM — projeyi kaldığı yerden sürdürme kılavuzu

Bu belge, bağlam kaybolsa bile **hatasız devam edebilmek** içindir. Depoyu ilk
kez gören birinin (veya sıfırdan başlayan bir oturumun) bilmesi gereken her
şey burada: nerede duruyoruz, neyin kanıtı var, neyin yok, hangi tuzaklar
zaten öğrenildi.

**Son güncelleme:** 2026-07-29 · **Commit:** `2c76e42` · **Durum:** FAZ 0–2
kanıtla tamamlandı, FAZ 3 başlayabilir.

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
| G0 | **GEÇTİ** 8/8 | iş 1434417 |
| G1 | **GEÇTİ** 8/8 | iş 1434418 |
| G2 | **GEÇTİ** 7/7 | iş 1434418 |

Üçü de aynı commit üzerinde, TRUBA/ARF-ACC H100'de, temiz git ağacıyla.
**396 test geçiyor** (yerel ve TRUBA), kapsam %97,6, kırmızı takım 6/6.

Açık kusur **yok**. `xfail` **yok**.

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
pytest -q                          # tam paket (396 test)
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

## 8. FAZ 3'e başlarken

Sırayla:

1. **Yerçekimi kararını verin** (§6). Ölçüm var, seçim yok.
2. **Gereken simüle süreyi ölçün.** Momentum aktarımının (β) ne zaman
   durulduğu koşu maliyetini 10 kat değiştirir.
3. **DART kurulumunda çözünürlük yakınsaması** gösterin — krater çapı ve β'nın
   parçacık sayısına duyarlılığı.
4. Kapı ölçütlerini şartnameden (`DR-RIFT-P3`) alın, **gevşetmeyin**.

Ensemble (FAZ 5) için ADR-0004 "yüzlerce koşu" öngörüyor; yerçekimsiz
~30 GPU-günü ile fizibil. Vekil (surrogate) model planı **belgelerde yok** —
FAZ 4-5 tasarlanırken karara bağlanmalı.

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
