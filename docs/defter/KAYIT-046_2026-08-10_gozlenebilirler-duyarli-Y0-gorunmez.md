# KAYIT-046 — Gözlenebilirler **duyarlı**, ama `Y0` **görünmez** (2026-08-10)

**Kapsam:** FAZ 4.11 · ADR-0045 §7 düzeltmesi · FAZ 4.6'nın önkoşulu
**Öncül:** [KAYIT-045](KAYIT-045_2026-08-09_mermiyi-cozmek-rejimi-degistiriyor.md)
**Koşu:** `faz411_gozlenebilir_duyarliligi.py`, 9 nokta, `t_end = 0,2 s`,
`0/9` düşen. `ileri_kosu_ikiasama`'nın GPU yolu **ilk kez** koştu.

---

## 1. Neden `t_end = 0,2` yetti

`β` iki bağımsız koşuda **bit düzeyinde aynı** çıktı:

| kaynak | `t` | `β` |
|---|---|---|
| KAYIT-045 üç seviyeli | 0,2 s | `1.4112162721355217` |
| uzun koşu, 41 örnek | 0,127 → 5,0 s | `1.4112162721355217` |

`2` saat `43` dakikalık koşunun `β` için getirdiği bilgi **sıfır**.
Ensemble `25` kat ucuza koşabiliyor; bu deney saatler değil dakikalar
sürdü.

---

## 2. Ana tablo

| # | `a0_blok` | `Y0` | `f_blok` | `β` | kaçan (kg) | **hedef ejektası** |
|---|---|---|---|---|---|---|
| 0 | 1,00 | 1e3 | 0,05 | 1,42815 | 579,2 | ≈ 0 |
| 1 | 1,30 | 1e3 | 0,05 | 1,43746 | 579,2 | ≈ 0 |
| 2 | 1,00 | 1e7 | 0,05 | 1,42912 | 579,2 | ≈ 0 |
| 3 | 1,30 | 1e7 | 0,05 | **1,43835** | 579,2 | ≈ 0 |
| **4** | **1,00** | 1e3 | **0,50** | **1,40998** | **670,7** | **91,3** |
| 5 | 1,30 | 1e3 | 0,50 | 1,42370 | 579,3 | ≈ 0 |
| **6** | **1,00** | 1e7 | **0,50** | 1,41171 | **670,7** | **91,3** |
| 7 | 1,30 | 1e7 | 0,50 | 1,42469 | 579,3 | ≈ 0 |
| 8 | 1,15 | 1e5 | 0,275 | 1,41697 | 579,3 | ≈ 0 |

Payda her köşede aynı (`4,16672e9 kg`; üç seviyeli incelme kütleyi
`+%0,03` içinde koruyor, ölçüldü).

---

## 3. `Y0` **çıkarılamaz** — ölçülmüş bir olgu

`β`'nın köşe farkları:

| parametre | etki |
|---|---|
| `f_boulder` | **−0,01575** |
| `boulder_alpha0` | **+0,01131** |
| `Y0` | **+0,00115** |

`Y0` **dört mertebe** değişiyor (`10³ → 10⁷ Pa`) ve `β` yalnızca `0,001`
oynuyor — diğer ikisinin **onda biri**.

Daha keskin kanıt: nokta **4** ile **6** yalnızca `Y0`'da farklı
(`1e3` vs `1e7`) ve hedef ejektası **`0,1 kg` bile** değişmiyor
(`670,7` / `670,7`).

> **`Y0` bu ileri modelde gözlenebilirlerin hiçbirine yazılmıyor.**
> G4-C'nin *"3/3 parametre kurtarıldı"* ölçütü `Y0` yüzünden düşecek ve
> bu bir **fizik olgusu**, çıkarıcı kusuru değil.

Sebebi makul: `t = 0,2 s`'de olan şey merminin çarpma anındaki eşlenmesi.
O anda basınçlar `GPa` mertebesinde; `Y0 = 10⁷ Pa` bile **üç mertebe**
küçük, yani akış mukavemeti hissetmiyor. Mukavemet krater **geç**
evresinde belirleyici olur — ve o evre `0,2 s`'de yok.

---

## 4. `ejekta_kutle_kesri` **bilgi taşıyor** — ADR-0045 §7 düzeltmesi

§7'de *"tam olarak mermi kütlesi, hiçbir bilgi taşımıyor"* demiştim.
**Tek sahneden aşırı genelleme.** Dokuz köşede:

* yedi köşede kaçan kütle `579,2 kg` = merminin kendisi ✔ (§7 doğru),
* iki köşede `670,7 kg` → **`91,3 kg` gerçek hedef ejektası**.

O iki köşenin ortak yanı: `boulder_alpha0 = 1,0` **ve**
`f_boulder = 0,50` — yani **%50 katı (gözeneksiz) blok**.

> Gözeneklilik düşünce **gerçek ejekta çıkıyor**. `--gozeneksiz` kontrol
> kolunun sorduğu soru, ensemble'ın kendisi tarafından cevaplanmış:
> gözenek çökmesi kazı enerjisini yutuyor.

Gözlenebilir **iki seviyeli** (`ölü` değil ama zayıf): `f_boulder` ve
`boulder_alpha0` birlikte bir eşiği geçince açılıyor. Bir eşik
göstergesi, sürekli bir ölçü değil.

---

## 5. Durum

| gözlenebilir | yargı | gerekçe |
|---|---|---|
| `beta` | **KULLANILABILIR** | `%2,0` yayılım, iki parametreye duyarlı |
| `krater_capi` | **ÖLÜ** | dokuz köşede de `0` |
| `ejekta_kutle_kesri` | **ZAYIF** | eşik göstergesi, iki seviye |
| `krater_derinlik` | ölçülmedi | `kutulama="eksen"` ile yeniden bakılmalı |

**FAZ 4.6 koşabilir** ama `Y0` kurtarılamayacak. İki seçenek var ve
ikisi de ADR gerektiriyor:

1. `Y0`'yı çıkarım uzayından **çıkarmak** (iki parametre, iki
   gözlenebilir — belirlenmiş sistem).
2. `Y0`'ya duyarlı bir gözlenebilir eklemek; bu **daha uzun koşu**
   demek (mukavemet geç evrede belirleyici) ve ADR-0043'ün maliyet
   hesabını yeniden açar.

> Kararı vermeden önce eksik ölçüm: `krater_derinlik`'in yeni kipte
> `Y0`'ya duyarlı olup olmadığı. Derinlik geç evre ürünüdür; `β`'nın
> göremediğini görebilir.
