# Protokol I — geçiş noktası `x₀` çözünürlüğe dayanıklı mı

**Yazıldı:** 2026-09-06, **koşudan önce** · **Dayanak:** G1, H (A69)

---

## Neden

H ölçtü: krater derinliği **mutlak olarak yakınsamıyor**
(`0,36 → 0,61 m`, `%72`). Ama `Y₀` ile ilişkisi iki ölçekte de aynı
(`r = −0,943` vs `−0,925`).

Bu, iki ayrı sorunun karıştığını gösteriyor:

| soru | H'nin yanıtı |
|---|---|
| Derinliğin **değeri** yakınsıyor mu? | **hayır** |
| Derinliğin `Y₀`'a **tepkisi** yakınsıyor mu? | **belirsiz** — yalnız korelasyona bakıldı |

Fiziksel olarak anlamlı parametre derinliğin kendisi değil,
**geçiş noktası `x₀`**: kohezyon hangi değerin üstünde krateri
sınırlamaya başlıyor. Bizim kraterimiz `0,5 m`, DART'ınki `~10 m` —
**mutlak ölçek zaten aktarılamaz**. Aktarılabilecek olan `x₀`'dır.

## Tasarım

`G1` ile **aynı** `24` `θ`, **aynı** iki sahne tohumu, **orta**
merdivende (`N = 69 886`).

| | kaba (var) | orta (bu kampanya) |
|---|---|---|
| `N` | `17 201` | `69 886` |
| nokta | `24 × 2` | `24 × 2` |
| `t_end` | `0,024 s` | `0,024 s` |

`12` görev × `4` nokta ≈ `2` saat/görev.

## Ölçülen

Her ölçekte sigmoid uydurulur (`d_alt ≥ 0` kısıtı, A67):

```
d(x) = d_alt + (d_ust - d_alt) / (1 + exp((x - x0)/w))
```

Karşılaştırılan: **`x₀`** (geçiş) ve **`w`** (keskinlik).

## Yargı — **şimdi kilitleniyor**

Geçiş noktasının belirsizliği, birini-dışarıda-bırak ile
kestirilir: her ölçekte `24` kez uydurup `x₀`'ın örneklem sapması
`σ_x0` alınır.

| gözlenen | sonuç |
|---|---|
| `\|x₀ᵒʳᵗᵃ − x₀ᵏᵃᵇᵃ\| < 2 √(σ²ᵏᵃᵇᵃ + σ²ᵒʳᵗᵃ)` | **`x₀` DAYANIKLI.** Geçiş noktası çözünürlükten bağımsız; aktarılabilir sonuç budur. |
| `2σ` ile `4σ` arası | **ZAYIF.** Fark var ama yön aynıysa şartlı bildirilir. |
| `> 4σ` | **DAYANIKSIZ.** `x₀` da ölçeğe bağlı; niceliksel hiçbir şey aktarılamaz. |

### Ek şart — uydurma geçerliliği

Her iki ölçekte de:

1. `R² > 0,85` (yoksa sigmoid biçimi uygun değil, sonuç okunmaz)
2. `x₀` veri aralığının **içinde** (A67 uyarısı düşmemeli)
3. `d_alt` kısıt sınırında ise **bildirilir** ve `x₀` yine de okunur
   (kısıt yalnız alt asimptotu etkiliyor)

## Bu ne DEĞİL

Üç noktalı Richardson değil; `σ_num` üretmiyor. İki ölçek arasında
**tek bir parametrenin** dayanıklılığını sınıyor. A52 çözülmeden
tam yakınsama mümkün değil ve bu belge onun yerine geçmiyor.

Ayrıca `x₀` dayanıklı çıksa bile **mutlak derinlik hâlâ
yakınsamamış** olur (A69) ve `Y₀ = f(d)` eşlemesi aktarılamaz.
Aktarılabilecek tek şey `x₀`'ın kendisidir.

## Maliyet

`48` koşu × `~30` dk = `24` GPU-saat; `12` görevde **`~2` saat**.
