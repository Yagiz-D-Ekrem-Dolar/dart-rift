# ANLIK 2026-09-05 — protokol-v2

> **Değiştirilemez kayıt.** Bu dosya `MANIFEST.sha256` ile
> kilitli; düzenlemek testi düşürür. Sonradan öğrenilen
> her şey **yeni** bir anlık görüntüye yazılır.

| | |
|---|---|
| commit | `bdaa78b6c39b59bac9a5535f0f78697126aa2e97` |
| kısa | `bdaa78b` · dal `main` |
| commit tarihi | `2026-09-03T13:19:58+03:00` |
| çalışma ağacı | **temiz** |

---

## Bu anlık görüntünün konusu

**Protokol v2 donduruldu.** v1 (`44abe54`) `L2` tarafından
çürütüldü; eksik olduğu **bilinen** ölçütle koşmak yerine
versiyonlandı, gerekçelendirildi ve yeniden donduruldu.

> `dondurma ≠ asla değiştirme`
> `dondurma ⇒ değişiklik varsa versiyonla + gerekçelendir + yeniden dondur`

## GEÇERSİZ KILINAN YORUMLAR

| yorum | neden | yerine |
|---|---|---|
| *"şok kapısı yeterli"* (v1) | `L2` düşük AV kolu `%75,65` verdi, kapı `SOK_VAR` dedi | üst sınır **tanı bayrağı** olarak eklendi (`SOK_ASIRI_ADAY`) |
| *"`up > v/2` olanaksız"* | `v/2` yalnızca **aynı malzeme/empedanstaki** simetrik düzlemsel çarpma için | `%74,3` **sezgisel** üst kenar; empedans eşleşmesinden türetilmedi |
| *"üst sınır sert kapı olsun"* (ilk v2 taslağı) | türetimi ampirik; *"neden `1,2`?"* savunulamaz | **tanı bayrağı**; sert kapı yalnızca alt sınır |
| *"düşük AV mekanizma adayı"* | kaçan `33` parçacığın **hepsi kaba seviyeden** | **çözülmüş ejekta kanıtı olarak reddedildi**; dinamikleri etkilemediği anlamına **gelmez** |
| *"`u` hattı elendi"* | tek varyant bütün olasılıkları elemez | *"test edilen pertürbasyon **baskın açıklama olarak desteklenmedi**"* |
| *"`L1`'de aynı parçacıklar kaçıyor"* | kütleler nicemli; farklı küme aynı toplamı verebilir ve kimlik **karşılaştırılamadı** | *"ejekta kütlesi **nicemli**, toplam düzeyinde ayırt edilemiyor"* |
| *"`L1`'in `β`'ları"* | `npz` yok, defter post-hoc uygulanamadı (A37) | **kullanılmıyor** |

## DONDURULAN KURALLAR (v2)

### Sert kapılar

| kapı | ölçüt |
|---|---|
| şok | sıkışma `≥ %4,56` — **yalnız alt sınır** |
| defter | `\|artık\| / p_mermi ≤ 1e-3` |
| zamansal plato | `\|ΔΔβ\| < max(1e-4, 0,05·\|Δβ\|)`, pencere **boyunca** |
| uzamsal yakınsama | `Δβ`, `M_ejekta`, `P_ejekta,∥` **üçü birden** |

### Tanı (kapı **değil**)

`SOK_ASIRI_ADAY` · `n_kaçan` · `θ_ejekta` · `β_mermi` ·
`ejekta_seviyeleri` · `en_agir_1_pay` / `en_agir_5_pay` ·
`m_ej_medyan` / `m_ej_max`

### Eşikler ve `σ_num`

`A1 < 0,20` (aday) · `A2 < 0,10` (nihai) · `A2` sağlanmazsa fark
**posteriora** taşınır. `σ_num`: monoton -> mertebe `p`; monoton
değil -> zarf.

## L1/L2'DEN ÇIKAN — savunulabilir hâliyle

| kanıtlanan | |
|---|---|
| momentum defteri kapanıyor | `~1e-14`, dört kolda |
| eski `β` yanlış fiziksel bileşeni ölçüyordu | hedef katkısı tam `0` |
| `R2`'de hedef ejektası **çözünürlük tabanında** | `16` parçacık × `5,83 kg` |
| `L1`'de toplam ejekta gözlenebiliri **nicemli** | `24` noktada bit düzeyinde aynı |
| test edilen `u` pertürbasyonu **desteklenmedi** | tabanla bit düzeyinde aynı |
| düşük AV'nin kaçış artışı **çözülmüş ejekta değil** | `33` parçacığın hepsi `372,83 kg` |
| krater derinliği parametrelere **duyarlı** | `0,08 – 0,79 m`; fizik kodu `L1`'den beri değişmedi (diff denetlendi) |

| **kanıtlanmayan** | |
|---|---|
| DART `β`'sının yeniden üretildiği | — |
| hedef ejektasının çözünürlükten bağımsız olduğu | — |
| P-α'nın kazı probleminin ana nedeni olduğu | gözeneksiz kol `SOK_YOK`, **okunmadı** |
| krater gözlenebilirinin yakınsadığı | — |
| nihai çıkarımın fiziksel geçerliliği | — |

## KOŞU KİMLİKLERİ

| iş | JOBID | durum |
|---|---|---|
| `L1` ensemble | `1540987` | koştu; özet satırında çöktü (A33), veri sağlam |
| `L2` mekanizma | `1540986` | dört kol tamam |
| `R1/R2/R3` | — | **bu görüntüden sonra gönderilecek** |

## O GÜN NE BİLİNMİYORDU

- `Δβ`, `M_ejekta`, `P_ejekta,∥` üçünün yakınsayıp yakınsamadığı
- `n_kaçan`'ın çözünürlükle gerçekten büyüyüp büyümediği
- Ejekta momentumunun kaç parçacıkta yoğunlaştığı
- Dört kapının aynı koşuda yeşile dönüp dönemeyeceği
