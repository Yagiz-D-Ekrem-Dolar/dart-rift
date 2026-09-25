# Protokol A98K — kontrollü geç evre kazı akışında yapay viskozite ve çözünürlük

> **TASLAK — henüz KİLİTLİ DEĞİL.** `t_end` (§2.4) duman koşusundan sonra
> doldurulup ayrı commit'le kilitlenecek; o commit'ten önce hiçbir kol koşulmaz.
>
> **NOT (2026-09-26, kilit):** `t_end = 40 s` dolduruldu (§2.4). Bu commit'le
> **KİLİTLİ**; TRUBA'ya bundan sonra gönderilir. K2 tanıya indirildi (§4).

**Yazıldı:** 2026-09-26, **A98K koşularından ÖNCE**. Kilitlenmeden önce
görülenler §2.4'te **tek tek** yazılı: süre seçimi için kaba kolda iki CPU
duman koşusu yapıldı; başka hiçbir kol koşulmadı.
**Öncül:** rapor A98, A101 (`docs/FAZ4-SIKINTI-RAPORU.md`),
`docs/COZUNURLUK-DENETIMI.md`, PROTOKOL-A98 (tam sahne; koşuyor).
**Betikler:** `scripts/a98k_kazi_akisi.py` (koşu), `scripts/a98k_raporu.py`
(kilitli rapor) → `S_A98K.json`. **İş:** `truba/is_A98K_kazi.slurm`.

---

## 1. Neden

A98 hipotezi: geç evrede Monaghan yapay viskozitesi (AV; `α = 1, β = 2`)
akışı frenliyor; fren `h` ile doğrusal; kaba çözünürlükte fren güçlü → daha az
ejekta → daha küçük `β`. UY'nin `β(t)` eğrisi (0,2 s'de üç çözünürlük aynı,
fark sonra doğuyor) ve CPU güç ölçümü (aynı akışta `h` yarıya → AV gücü
`1,95–1,97` kat az) bunu destekliyor, ama **kanıtlamıyor**.

PROTOKOL-A98 bunu tam DART sahnesinde sınıyor. Tam sahnede başka
mekanizmalar da var: erken evre şoku, temas oranı (A100), yüzey diverjansı
(A101), dondurma, yerçekimi. A98K **yalnız geç evreyi** kontrollü bir
başlangıç değer problemi olarak kurar. Çözünürlük dışında her şey birebir
aynıdır ve AV'nin payı doğrudan ölçülür. Sorular:

1. Varsayılan AV'de sonuç çözünürlüğe bağlı mı, bağlılık birinci mertebe
   mi (AV `∝ h` ile tutarlı mı)?
2. Geç evre AV'sini küçültmek (A98 çaresi) bu bağlılığı kaldırıyor mu?
3. Çarenin yan etkisi var mı: düşük AV'de parçacıklar iç içe geçiyor mu?
   (A98 tam sahne koşularında AV `0,1` kolunda geçişten hemen sonra `Δt`
   geçici olarak küçüldü; KAYIT-068 §8.)
4. A101 çaresi (düzeltilmiş süreklilik) çözüm paketine zarar veriyor mu?

## 2. Tasarım

### 2.1 Problem (Maxwell Z-modeli kazı akışı)

- Blok `|x|, |y| ≤ L = 12 m`, `−D ≤ z ≤ 0`, `D = 10 m`. Bütün sınırlar
  serbest; üst yüzey `z = 0`. Merkezde `r < r₀ = 4 m` yarım küre boşluk
  (geçici krater).
- Kübik kafes, hücre merkezleri `(i + ½) s`. Kütle `ρ_yığın s³`
  (`ρ_yığın = 1600`).
- Malzeme: **üretimin geç evre malzemesi.**
  - Bazalt Tillotson; `gec_evreye_gec(A = 1e5 Pa)`, yani `a = b = B = 0`,
    kayma modülü aynı oranda.
  - `Y₀ = 10 Pa`, `μ_f = 0,6`, `YM = 1,5e9`.
  - P-α, `α₀ = 2700/1600`, `P_e = 1e6`, `P_s = 1e8`.
  - Matris çekmesi kırpık; A80 dayanım kesmesi (`η = 0,5`); A83 yoğunluk
    tabanı (`0,01`); `akma_kipi = "ara"`; BVH komşu arama; `CFL = 0,25`.
  - Yerçekimi kapalı. Geç evrede `g ~ 3e-5 m/s²`, yani süre boyunca
    `Δv ≲ 1e-3 m/s`, akış hızlarının `%1`'inden az.
- Başlangıç hızı: Maxwell Z-modeli, `Z = 3` (sıkışmaz),
  `u_r = V₀ (r₀/r)³`, `u_θ = u_r sin θ / (1 + cos θ)`, `V₀ = 0,5 m/s`.
  θ aşağı düşeyden ölçülür; yüzeyde akış 45° yukarı-dışa yönelir.
  Mach `V₀/c ≈ 0,05` (geç evreyle aynı).
- Başlangıç gerilmesi sıfır, iç enerji sıfır. Geçiş `t = 0`'da yapılır.

### 2.2 Kollar (12)

| ad | aralık `s` [m] | `r₀/h` | geç AV `(α, β)` | süreklilik |
|---|---|---|---|---|
| `K_s1_av1`, `K_s0p5_av1`, `K_s0p25_av1` | 1 / 0,5 / 0,25 | 2 / 4 / 8 | `(1, 2)` varsayılan | SPH |
| `K_s*_av01` | aynı | | `(0,1 ; 0,2)` (A98 çaresi) | SPH |
| `K_s*_av0` | aynı | | `(0 ; 0)` (sınır) | SPH |
| `K_s*_av01L` | aynı | | `(0,1 ; 0,2)` | `tr(L)` (A101 çaresi) |

`t_end = 40 s` (§2.4). Hepsi TRUBA'da tek GPU'da (H100, FP64),
sırayla koşar; kod tek commit'te sabitlenir (`AGAC_COMMIT`). Kod A99
düzeltmelerini **içerir** (yerel `HEAD`; PROTOKOL-A98'in tam sahne
koşuları içermez). İki deney ayrı sorulara cevap verir; A98K içinde her kol
aynı kodla koşar.

### 2.3 Gözlenebilir

`Q = P_up(|v| > 0,1 V₀)`, `t_end` anında: özgün yüzeyin üstündeki
(`z > 0`), yukarı giden (`v_z > 0`) ve hızı `0,05 m/s`'yi aşan maddenin
yukarı momentumu. `β − 1`'in benzeridir: kraterden atılan maddenin
momentumu. Eşik, gerçek sahnedeki `v_esc/V_akış` oranına yakın seçildi.
Tanı (kapı değil): `P_up` (eşiksiz), `M_up`, `E_AV`, `W_plastik`, `Δt`,
en yakın komşu mesafesi.

### 2.4 Kilitlemeden önce görülenler (dürüst kayıt)

1. CPU duman koşusu, `K_s1_av1` ayarıyla, `t_end = 1 s`: betik çalışıyor.
   `n = 5620`, 47 adım. `E_AV = 3,2e3 J`, `W_pl = 1,9e3 J`.
2. CPU duman koşusu, `K_s1_av1` ayarıyla, `t_end = 40 s`: **yalnız süre
   seçimi için.** `Q(t)` eğrisinin platoya ulaştığı an okundu:
   `n = 5620`, 2243 adım (`Δt` `4,7e-3 … 2,2e-2`), CPU 24 dk.
   `Q(t)`: 2 s `7,5e3`, 6 s `3,2e4`, 10 s `3,7e4`, 16 s `4,2e4`, 20 s `4,1e4`,
   30 s `3,93e4`, 40 s `3,91e4` (kg m/s). Plato 14–16 s'den sonra; 20–40 s
   arası ±%4. `E_AV` 20 s'ye kadar doyuyor (`9,5e3 J`); `W_pl` 40 s'de hâlâ
   yavaş artıyor (`1,26e4 J`); kabada AV payı `0,432`. Momentum sapması
   `2e-16`, enerji `−2,5e-4`, `nn_min/s = 0,85`.
   **Seçim:** `t_end = 40 s`. İnce kollarda AV zayıf, akış daha uzun sürer;
   kabada platonun 2,5 katı süre pay bırakır.
   **Görülen değerlerin etkisi:** `Q(s=1, av1)` ve kabanın AV payı biliniyor.
   K1, K3, K4 ince aralıklara bağlı (görülmedi). K2'nin kaba değeri
   görüldüğü için K2 **tanıdır, yargı değildir** (§4).

Başka hiçbir kol (hiçbir ince aralık, hiçbir düşük AV kolu) kilitlenmeden
önce koşulmadı.

## 3. Geçerlilik

- **G0:** Kol dosyası var, `sonlu = True`, parametreleri kol tanımıyla
  aynı (`s`, AV, süreklilik) ve toplam momentumun bağıl sapması
  `≤ 1e-6`. Değilse o kol **eksik** sayılır; girdiği her yargı OKUNMAZ.
- Rapor **beklenen 12 kolu** sayar. Eksik kol sessiz geçmez (A84/A88).

## 4. Kilitli yargı

`D_kol = |Q(s=1) − Q(s=0,25)| / |Q(s=0,25)|`, kaba ile en ince arasındaki
bağıl fark.

**K1 — mekanizma üretildi mi (varsayılan AV):**
`D_av1 ≥ 0,10` **ve** `Q(1) < Q(0,5) < Q(0,25)` (incelince artan; A98
yönü) → **VARSAYILAN AV'DE ÇÖZÜNÜRLÜK BAĞIMLILIĞI VAR**. Değilse
**ÜRETİLMEDİ**.

**K2 — AV payı (TANI; kaba değeri kilitlemeden önce görüldü, §2.4):** kaba kolda (`K_s1_av1`)
`E_AV / (E_AV + W_plastik) ≥ 0,5` → **AV KABADA BASKIN**, değilse
**İKİNCİL**. Üç aralığın payı ayrıca yazılır.

**K3 — ANA YARGI (çare):**

| yargı | koşul |
|---|---|
| **GEÇ AV KÜÇÜLTME ÇÖZÜNÜRLÜK BAĞIMLILIĞINI BÜYÜK ÖLÇÜDE KALDIRIYOR** | `D_av01 ≤ D_av1 / 3` |
| **… KISMEN KALDIRIYOR** | değilse, `D_av01 < D_av1` |
| **… KALDIRMIYOR** | `D_av01 ≥ D_av1` |

**K4 — mertebe (varsayılan AV):**
`p = log₂(|Q(1) − Q(0,5)| / |Q(0,5) − Q(0,25)|)`.
`0,5 ≤ p ≤ 1,5` → **BİRİNCİ MERTEBE (AV ∝ h İLE TUTARLI)**; değilse
**BİRİNCİ MERTEBE DEĞİL**. Farklar zıt işaretliyse OKUNMAZ.

**K5 — yan etki:** AV `0,1` kolunun üç aralığında da `t_end`'de
`min(nn)/s ≥ 0,3` **ve** `nn < 0,5 s` olan parçacık kesri `≤ %1` →
**AV 0,1'DE İÇ İÇE GEÇME YOK**; değilse **VAR**. AV 0 ve A101 kolları
ayrıca yazılır (kapı değil).

**K6 — A101:** `D_av01L ≤ D_av01` → **A101 ÇÖZÜNÜRLÜK FARKINI BÜYÜTMÜYOR**;
değilse **BÜYÜTÜYOR**.

`genel` = K3.

## 5. Dürüst sınırlar

- Kontrollü problem DART sahnesi değildir: başlangıç akışı analitik, şok
  yok, yerçekimi yok, blok sonlu. K1–K4 "tam sahnedeki farkın sebebi AV'dir"
  demez. Söylediği şudur: "aynı malzeme ve aynı AV, geç evre akışında şu
  büyüklükte ve şu mertebede bir çözünürlük bağlılığı üretir; çare onu şu
  kadar kaldırır". Tam sahne yargısı PROTOKOL-A98'dir. İkisi aynı yönü
  gösterirse kanıt güçlenir.
- Üç aralık bir mertebe tahmini verir, yakınsama **kanıtı** değildir.
- Sonuç ne çıkarsa çıksın gözlenen DART `β`'sına göre ayar yapılmaz.

## 6. Maliyet

Tahmini: `s = 0,25`'te ~360 bin parçacık; H100'de her kol `~0,5–1 sa`.
Toplam `~3–5 GPU-sa`, **1 GPU**, süre sınırı 12 sa. Otomatik yeniden
gönderim yok. İş kesilirse yeniden gönderimde var olan çıktılar atlanır.
