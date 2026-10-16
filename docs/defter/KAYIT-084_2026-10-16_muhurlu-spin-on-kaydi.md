# KAYIT-084 — Hera için mühürlü spin ön kaydı üretildi

**Tarih:** 2026-10-16 (gece) · **Sıfır GPU**
**Protokol:** [PROTOKOL-HS](../truba/PROTOKOL-HS-HERA-SPIN.md) (aynı gün,
öngörü hesaplanmadan **önce** kilitlendi)
**Koşucu:** `scripts/hera_spin_onkayit.py`
**Kayıt:** [`docs/onkayit/ONKAYIT_HERA_SPIN_uretim96.json`](../onkayit/ONKAYIT_HERA_SPIN_uretim96.json)
**SHA-256:** `6464cf81f68f09e195c14c0fc4ee1dbb2e3334eedbaddf61f37b610184cd80d7`
**Künye commit:** `c894d47`

---

## 1. Mühürlenen öngörü

`ω` = çarpmanın bağlı malzemeye kattığı açısal hız (PROTOKOL-SI §5
tanımı, değiştirilmeden). 96/96 noktada ölçüldü, **atlanan yok**.
`θ` örnekleri eleme bölgesinden (`I ≤ 3`, hacmin %34,04'ü), bölge
içinde düzgün; 20 000 örnek, tohum `20261016`.

| kantil | `ω` (rad/s) | `ω/ω₀` | eklenen dönme periyodu |
|---|---:|---:|---:|
| q05 | 2,3142e−06 | %1,58 | 31,4 gün |
| q16 | 3,1967e−06 | %2,18 | 22,8 gün |
| **q50** | **5,1799e−06** | **%3,54** | 14,0 gün |
| q84 | 8,7735e−06 | %5,99 | 8,3 gün |
| q95 | 1,5120e−05 | %10,33 | 4,8 gün |

`ω₀ = 1,4642e−04` rad/s (çarpma öncesi `P = 11,92` sa). **Bu sabit
`si_son_isleme.py`'de `TEYITSIZ` etiketli**; yüzdeler o yüzden bilgi
amaçlıdır, mühürlenen sayı `ω`'nın kendisidir.

İki not:

- PROTOKOL-SI §5'in eşiği "periyot değişimi `> %1` → **SPIN DEĞİŞİMİ
  ÖLÇÜLEBİLİR**". Bizim **q05**'imiz bile `%1,58` — yani dağılımın
  en düşük ucundan bile ölçülebilir bölgedeyiz.
- Hera spin hızını `10⁻³`'ten iyi veriyor; öngörülen değişim o
  hassasiyetin **~3500 katı**. Yani sınırlayıcı etken Hera'nın
  hassasiyeti **değil**, aradaki dört yıllık evrim (§4).

## 2. Asıl ürün: `ω → f` eşlemesi

Hera bir `ω` ölçtüğünde `f` için ne çıkar:

| `ω` aralığı (rad/s) | n | `f` q05 | **q50** | q95 |
|---|---:|---:|---:|---:|
| 6,86e−07 – 3,24e−06 | 3334 | 0,050 | **0,134** | 0,492 |
| 3,24e−06 – 4,22e−06 | 3333 | 0,065 | **0,203** | 0,485 |
| 4,22e−06 – 5,18e−06 | 3333 | 0,065 | **0,264** | 0,485 |
| 5,18e−06 – 6,39e−06 | 3333 | 0,081 | **0,302** | 0,477 |
| 6,39e−06 – 8,61e−06 | 3333 | 0,088 | **0,309** | 0,469 |
| 8,61e−06 – 7,86e−05 | 3334 | 0,126 | **0,309** | 0,462 |

Eşleme **tekdüze**: `ω` arttıkça `f`'nin ortancası `0,134 → 0,309`,
yani 2,3 kat. `ρ(ω, f) = +0,459` ile tutarlı.

### 2.1 Ama gücü asimetrik — saklanmıyor

Aralıklar birbirine **fena hâlde giriyor**. En alt `ω` kutusunda `f`
`0,050 – 0,492` arasında, yani **önselin neredeyse tamamı**. En üst
kutuda ise `0,126 – 0,462`.

Pratik sonuç:

- **Hera yüksek bir `ω` ölçerse** (`> 8,6e−06`), `f < 0,126` elenir.
  Gerçek ama mütevazı bir kısıt.
- **Düşük bir `ω` ölçerse**, neredeyse hiçbir şey öğrenilmez.

Bu, `f`'nin önselden baskın olmasının (`n_yön = 1`) doğrudan sonucu ve
PROTOKOL-HS §7(2) bunu önceden yazmıştı: *"öngörü genişliği büyük
ölçüde önselin genişliğidir; dar çıkarsa bu bir başarı değil, bir hata
işaretidir."* Dar çıkmadı — yani öngörü kendi tutarlılık sınavını
geçti.

## 3. Üretim sırasında yakalanan kusur

İlk koşumda betik TRUBA'da depo dizini dışından çalıştı ve
`os.popen("git rev-parse HEAD")` **boş** döndü — kayıt künyesiz çıktı.
Künyesiz bir ön kayıt mühür sayılmaz: PROTOKOL-HS §5 commit'i meta'nın
parçası yapıyor ve commit tarihi zaman damgasının ikinci kanıtıdır.

Kusurlu dosya **hiç commit'lenmemişti**, yani mühürlenmemişti; silindi
ve betik düzeltildikten sonra yeniden üretildi. Artık commit betiğin
kendi deposundan (`git -C <kök>`) okunuyor ve okunamazsa betik
**duruyor**.

> Bu "mühürlü kaydın üzerine yazmak" değildir — mühür, depoya
> commit'lenmekle tamamlanır ve o dosya hiç commit'lenmedi. Yine de
> burada yazılı olsun diye kaydediliyor.

## 4. Kaydın ayrılmaz uyarıları

JSON'un gövdesinde duruyor ve karşılaştırma raporuna aynen geçecek:

1. **Zaman ölçeği.** Model `ω`'sı `t_end = 600 s`'deki, yani çarpmanın
   **kattığı** açısal momentum. Hera **dört yıl evrilmiş** bir durum
   ölçecek: NPA sönümü, gelgit etkileşimi, yeniden birikme araya
   giriyor. İkisi aynı nicelik **değil**; doğrudan karşılaştırma bir
   geri-yayma modeli ister ve o model bu depoda **yok**. Sınırlayıcı
   etken budur, Hera'nın hassasiyeti değil.
2. **`f` önselden baskın**, öngörü genişliği büyük ölçüde önselin.
3. **Tek sabit sahne**; öngörü ona koşullu.
4. **ADR-0059 açık**: ince koşu yanlılık gösterirse bu kayıt yeniden
   üretilmeli.

## 5. `σ` konusunda ne yapılmadı

`ω` için **ölçülmüş bir `σ_model` yok** — `tarih_esleme`'deki terimler
`β` ve `M_ejekta` için. Öngörüye yalnız vekilin öngörü varyansı girdi.
Protokolün "vekil belirsizliği ve ölçülmüş `σ_model` dâhil" şartı,
var olmayan bir terimi uydurmakla karşılanmaz; eksiklik kaydın
içinde yazılı.

## 6. Bu kayıt ne işe yarıyor

`n_yön = 1` sonucu *"`β` bu ekseni göremiyor"* diyor. Bu ön kayıt
onun devamını yazıyor: *"ama şu gözlem görebilir, işte sayımız, işte
yanlışlanma kuralımız, işte tarihi."*

Hera'nın ölçeceği değer `q05–q95` dışında çıkarsa **TUTARSIZ** yazılır
ve kayda dokunulmaz.
