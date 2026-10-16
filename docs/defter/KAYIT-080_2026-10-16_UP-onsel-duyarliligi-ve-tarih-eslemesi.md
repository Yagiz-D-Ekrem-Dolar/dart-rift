# KAYIT-080 — PROTOKOL-UP §5 ve §6 koşuldu

**Tarih:** 2026-10-16 · **Havuz:** 96/96 · `n_grid = 60` ·
**Koşucu:** `scripts/up_onsel_ve_tarih.py` ·
**Çıktı:** [`docs/sonuclar/UP_s5_s6.json`](../sonuclar/UP_s5_s6.json)
**Öncül:** [PROTOKOL-UP](../truba/PROTOKOL-UP-POSTERIOR.md) §5/§6
(2026-10-08, veriden önce), ADR-0053, ADR-0058, KAYIT-079


> ## ⚠ DÜZELTME — 2026-10-16 akşam
>
> Bu kaydın §5 ve §6 yargıları **geçersizdir**. Girdi dosyasında
> `kos` sütunu yanlış nicelikti (`kos_ort`, parçacık kosinüslerinin
> ortalaması) ve ADR-0060 net momentum doğrultusunun kosinüsünü
> istiyor. `b_model` 1,437 kat şişmişti.
>
> Düzeltilmiş değerler: §6 **İKİ YÖNTEM UYUŞUYOR** (oran 3,31,
> bağdaşır hacim %34,04), §5 **SONUÇ VERİDEN GELİYOR**
> (`σ_onsel = 0`). "Posterior kenara yapışık" ve "vekil %77"
> bulguları da geri çekildi.
>
> **Hiçbir satır silinmedi** (kural 5); tam döküm:
> [KAYIT-082](KAYIT-082_2026-10-16_kos-hatasi-ve-duzeltilmis-sonuclar.md).

---

## 1. İki yargı

| § | yargı |
|---|---|
| **§6** tarih eşleme | **POSTERIOR DAR** |
| **§5** önsel duyarlılığı | **ÖNSEL ETKİLİ** |

İkisinin birlikte anlamı, protokolün kendi tablolarından:

> Tarih eşleme bölgesi **ana sonuç** olarak verilir; posterior
> *"olabilirlik varsayımına koşullu"* etiketiyle yayımlanır. Ayrıca üç
> önselin tablosu **zorunlu ek** olur ve özet cümlede yazılır.

## 2. §6 — model gözleme ulaşıyor mu? **Evet**

    I(θ) = maks_j |E_j(θ) − z_j| / sqrt( Var_j(θ) + σ_j² ) ,  kesme I > 3

| ölçü | değer |
|---|---|
| `I_min` | **0,504** |
| `I` ortanca | 7,687 |
| `I_maks` | 29,520 |
| **bağdaşır hacim** `V_bagdasir` | **%7,37** (15 916 / 216 000 düğüm) |
| posterior %68 hacmi | %0,50 |
| oran `V_bagdasir / V_post68` | **14,78** (eşik 10) |
| post68 kütlesinin bağdaşır oranı | **1,0000** (eşik 0,90) |

`I_min = 0,504` önemsiz bir sayı değil: **model DART'ın gözlemine
ulaşabiliyor.** Hiçbir `θ` gözlemle bağdaşmasaydı `I_min > 3` çıkardı ve
projenin ileri modeli reddedilirdi. Önsel hacminin **%7,37'si** ayakta
kalıyor; geri kalan %92,63 elendi.

**Çelişki yok, fazla güven var.** Posteriorun %68 kütlesinin
**tamamı** (oran `1,0000`) bağdaşır bölgenin içinde — yani iki yöntem
aynı yeri gösteriyor. Ama posteriorun hacmi bağdaşır bölgenin
**1/14,8'i**. Bu, Gauss olabilirliğinin + köşegen kovaryans
varsayımının klasik aşırı-güven imzası. Protokol bu durumu önceden
tanımlamış ve çözümü de yazmış: ana sonuç tarih eşleme bölgesidir.

## 3. §5 — sonuç veriden mi önselden mi? **Arada**

| önsel | kip `log10 Y₀` | kip `Y₀` (Pa) |
|---|---:|---:|
| `KILITLI` | +0,2542 | 1,796 |
| `DUZ_LOG` | +0,2542 | 1,796 |
| `KAYDIRILMIS` (×3) | +0,5085 | 3,225 |

`σ_onsel` = **0,2542 dex**. Eşikler: `≤ 0,15` veriden, `> 0,50`
önselden. Arada kaldı → **ÖNSEL ETKİLİ**. `α_b` ve `f` için bağıl kayma
`0,0508` — küçük.

### 3.1 Protokolün bir kusuru: iki önsel aynı dağılım

`KILITLI` ile `DUZ_LOG` **birebir aynı çıktı** ve bu bir hata değil,
tanım gereği: ADR-0053 kilitli önseli `Y₀ ∈ [1e0, 1e5] Pa` (log, 5
dekad) seçti, yani `log10 Y₀ ~ Düzgün[0,5]` — protokolün "bilgisiz uç"
diye yazdığı dağılımın ta kendisi.

Protokolü 2026-10-08'de yazarken bunu fark etmemişim. Üç önselli sınav
pratikte **iki** önselli: kilitli (= bilgisiz) ve kaydırılmış.
Düzeltilmiyor, kaydediliyor — ve `σ_onsel` bu yüzden *tek* bir
karşılaştırmadan geliyor, üçünün en büyüğünden değil.

### 3.2 Kenar uyarısı — ayrı bir bulgu

`KILITLI` posterior kipi birim küpte `u = (0,661 ; 0,051 ; 0,949)`:

- `Y₀` önselin **alt** kenarına yapışık (1,80 Pa, önsel 1 Pa'dan başlıyor)
- `f` önselin **üst** kenarına yapışık (0,477, önsel 0,50'de bitiyor)
- `KAYDIRILMIS`'ta `f` tam `u = 1,0`

Veri önsel kutusunun **dışını** istiyor. Bu, ADR-0053'ün
`ÖNSEL GÖZLEMİ İÇERMİYOR` yargısıyla aynı yöne işaret ediyor ve
`σ_onsel`'in neden sıfır olmadığını da açıklıyor: kaydırılmış önsel
verinin istediği düşük `Y₀` bölgesini kestiği için kip zorunlu olarak
yukarı kayıyor.

`KAYDIRILMIS`'ta `α_b` ve `f` büzülmeleri **negatif** (`−0,079`,
`−0,509`), yani posterior o eksenlerde önselden *daha geniş*. Kesilmiş
önselin kütleyi köşeye itmesinin yan etkisi.

## 4. Vekilin durumu

| vekil | `q²` | ÇD-RMSE | Bachoc çarpanı | kalibre %68 kapsama |
|---|---:|---:|---:|---:|
| `β` (fırlatı geleneğinde) | **0,9310** | 0,5019 | 1,2896 | 0,7083 |
| `ln M_ejekta` | **0,9882** | 0,1806 | 1,0953 | 0,7188 |

θ-gruplu 4-kat ÇD. Bachoc kalibrasyonu ikisini de **büyüttü** (yalnız
büyütme açık), kalibre kapsama `0,68` hedefinin biraz üstünde — yani
muhafazakâr tarafta. Ölçülen artık korelasyonu `ρ_ham = 0,2924`,
küçültülmüş `ρ = 0,2047` (λ = 0,3).

## 5. Ne değişmedi

`I > 3` kesmesi (Vernon, alanın kuralı), `0,15 / 0,50 dex` sınırları,
`%90` kütle örtüşmesi ve `10×` hacim oranı eşiği — dördü de
2026-10-08'de kilitliydi, hiçbirine dokunulmadı.

## 6. Bu üçlünün birlikte söylediği

KAYIT-079 ile birlikte okunduğunda projenin sonucu şu hâle geliyor:

1. **Kaç yön:** bir (`n_yön = 1`, KAYIT-079).
2. **Model gözleme ulaşıyor mu:** evet (`I_min = 0,504`).
3. **Geriye ne kalıyor:** önsel hacminin **%7,37'si**.
4. **Posterior ne kadar güvenilir:** bağdaşır bölgeden 14,8 kat dar →
   ana sonuç tarih eşleme bölgesi, posterior koşullu etiketle.
5. **Önsel ne kadar etkili:** `0,254 dex` → üç önsel tablosu zorunlu ek.

Yani savunulabilir çıktı *"iç yapı şudur"* değil; **ölçülmüş,
eleme ile daraltılmış bir parametre bölgesi** ve onun hangi
varsayımlara ne kadar bağlı olduğunun nicel dökümü.

## 7. Teknik not

Giriş düğümünde `n_grid = 60` ilk denemede **çekirdek dökümüyle**
düştü: OpenBLAS'ın açtığı iplik sayısı. `OMP_NUM_THREADS=4` ile sorun
kalmadı (7 saniye). İleride aynı tuzak için: analiz betikleri giriş
düğümünde iplik sınırıyla koşulmalı.
