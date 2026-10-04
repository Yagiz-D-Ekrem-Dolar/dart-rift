# Protokol DO — `Y₀` önselinin **ölçümle** sınanması (DART sahnesi)

**Yazıldı:** 2026-10-04, **DO koşularından ÖNCE.**
**Öncül:** [ADR-0053](../adr/ADR-0053-y0-onseli-ve-tanimlayici-gozlemli.md)
(önerilen karar), KAYIT-072 (DY2: `β = 3,748` @ `Y₀ = 10 Pa`),
KAYIT-067 (W2 `Y₀` serisi), PROTOKOL-DY §2 (sahne).
**Kod:** `inference/onsel_denetimi.py` · **Rapor:** `scripts/do_onsel_raporu.py`
→ `S_DO.json` (kilitli).

---

## 1. Neden

ADR-0053 ölçtü: W2 kıyas sahnesinde `b = β − 1 = 3,465 · Y₀^(−0,0760)` ve
gözlem (`β = 3,12`) **`644 Pa`**'ya düşüyor — üretim önselinin alt kenarı
(`1e3 Pa`) **gözlemin üstünde**. Eğer bu doğruysa havuzun `Y₀` posterioru
alt kenara çakılır ve `recovery.C2` onu bilgilendirici saymaz.

**Ama `644 Pa` bir dışdeğerlemedir:** ölçülen aralığın (`1 – 50 Pa`) üst
ucundan `1,11` dekad uzakta ve `p` küçük olduğu için kaldıraç büyük
(`p`'deki `%10` hata `Y₀`'da `~%30`). Üstelik o seri **kıyas sahnesinden**;
DART sahnesinin `p`'si farklı olabilir (KAYIT-072 §3: `β` dışındaki her
şey sahneye güçlü bağlı).

**Bu protokol dışdeğerlemeyi interpolasyona çevirir.** Önsel, DO okunmadan
**değiştirilmez**.

## 2. Tasarım (iki koşu)

Her ikisi de **DY2 ile birebir aynı sahne** (PROTOKOL-DY §2 + §6.2:
elipsoit `88,5 × 87 × 58 m`, `ρ_yığın = 2306,1`, üç küre mermi `579,4 kg`
`6144,9 m/s`, `17°`, `t_geçiş = 1,0 s`, `600 s`, kaba merdiven, `spacing 7 m`,
tohum `20260906`, `α_b = 1,15`, `f = 0,25`). **Değişen tek şey `Y₀`:**

| kol | `Y₀` | neden bu değer |
|---|---|---|
| **DO1** | **`500 Pa`** | literatürün üst ucu (L1/L2); önsel alt kenarının `0,3` dekad **altı** |
| **DO2** | **`5000 Pa`** | önselin **içinde** (alt kenarın `0,7` dekad üstü) |

DY2 (`10 Pa`) ile birlikte DART sahnesinde üç nokta: `10 / 500 / 5000 Pa`,
**`2,7` dekad**. ADR-0053'ün `644 Pa`'sı bu aralığın **içinde** → yargı
interpolasyonla verilir.

Maliyet kestirimi: DY2 `4:50:53`. `Y₀` zaman adımını belirlemiyor (CFL ses
hızından gelir), bu yüzden kol başına `~5 GPU-saat`, toplam **`~10 GPU-saat`**
(2 GPU, kullanıcının verdiği sınır).

## 3. Geçerlilik

Her kol için `gecerli = True` (sonluluk, enerji `≤ %5`, momentum defteri
`≤ 1e-3`, kurucu sınır), `t = 600 s` **ve** `kutle_tutarliligi` tutarlı
(`≤ %5`). Biri düşerse ilgili ölçüm **OKUNMAZ** ve önsel kararı DO ile
kilitlenmez (ADR-0053 ÖNERİ olarak kalır).

## 4. Kilitli ölçümler

`b = β − 1` (600 s). Üç DART-sahnesi noktasına (`10, 500, 5000 Pa`)
`onsel_denetimi.guc_yasasi_uydur` ile `b = C · Y₀^p` uydurulur.

1. **`p_DART`** ve en büyük bağıl artık.
2. **`Y₀_gözlem(DART)`** `= y0_coz(uydurma, 3,12)`.
3. **Önsel yargısı** `= onsel_denetle(..., onsel_lo = 1e3, onsel_hi = 1e7)`
   — üretim önseliyle, `ESIK_KENAR_DEKAD = 0,5`.
4. **`M_ejekta` kazancı:** aynı üç noktaya `M_ejekta` uydurulur ve
   `duyarlilik_tablosu` ile `β`'ya göre kazanç hesaplanır
   (`σ_β = payda`, `σ_M = hypot(0,3/1,6 ; 0,15)`).

## 5. Kilitli yargılar

### 5.1 Önsel (ADR-0053 §4.1'in sınavı)

| yargı | koşul | sonucu |
|---|---|---|
| **ÖNSEL GÖZLEMİ İÇERMİYOR** | `Y₀_gözlem ∉ [1e3, 1e7]` | ADR-0053 §4.1 **uygulanır**: önsel `[1e0, 1e5] Pa`'ya taşınır |
| **GÖZLEM ÖNSEL KENARINDA** | kenara `≤ 0,5` dekad | önsel alt kenarı **en az 1 dekad** aşağı çekilir (`[1e2, 1e7]` yetersiz sayılır) |
| **ÖNSEL GÖZLEMİ İÇERİYOR** | ikisi de değil | mevcut önsel **korunur**, ADR-0053 §4.1 **reddedilir** |

**Uydurma kalitesi kapısı (koşudan önce):** üç noktanın en büyük bağıl
artığı `> 0,15` ise güç yasası bu aralıkta **uygun değil** sayılır ve
yargı, gözlemi **kuşatan** iki nokta çiftinin yerel eğiminden okunur
(hangi çift olduğu veriden belli: `β` tekdüze azalıyor). Bu durumda
rapor `uydurma = UYGUN DEGIL, YEREL EGIM` yazar — yargı yine
yukarıdaki üç satırdan biridir.

### 5.2 Tanımlayıcı gözlemli (ADR-0053 §4.2'nin sınavı)

| yargı | koşul |
|---|---|
| **M_EJEKTA TANIMLAYICI** | `M_ejekta` çarpanı `< ESIK_CARPAN_TANIMLI = 3,0` |
| **M_EJEKTA KAZANCI KUCUK** | `≥ 3,0` ama `β`'nın çarpanının yarısından küçük |
| **KAZANC YOK** | `≥ β` çarpanının yarısı |

## 6. Kapı olmayan tanılar

`β` iki yöntem farkı, `M_ejekta`, `t50`/`t90`/`s(1s)` (mekanizma — `Y₀`
arttıkça `t50` **düşmeli**; düşmezse geç evre modeli dayanıma beklenen
yönde tepki vermiyor demektir), koni açıları (**A95**: gözlemle
kıyaslanmaz), dondurulan sayı, enerji sapması, duvar süresi,
`kutle_tutarliligi`, blok çözünürlüğü.

## 7. Bu protokolün çıkarmadığı şey

`θ`'yı çıkarmaz ve `Y₀`'yu **kestirmez**. Yalnız şunu söyler: *üretim
önseli, gözlemin düştüğü `Y₀` bölgesini içeriyor mu, ve `M_ejekta`'yı
posteriora katmak `Y₀`'yu gerçekten tanımlıyor mu.* `Y₀`'nun kestirimi
havuzun ve posteriorun işi.
