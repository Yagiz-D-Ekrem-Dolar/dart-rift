# A17 — hasar ölçütü (2026-08-21, koşudan **önce** yazıldı)

## Neden bu kol

`configs/p3_dimorphos.yaml` `damage.enabled: true` diyor.
`scripts/faz44_dart_yakinsama.py::_malzeme()` — FAZ 4'ün **bütün**
koşularının malzemesi — `damage=DamageParams(enabled=False)` diyor.
İkisi çelişiyor ve çelişkinin hangi tarafta çözüldüğü hiçbir yerde
yazılı değil.

ADR-0027 (kabul edilmiş) bu kolun sonucunu **2026-08-01'de** yazmıştı:

> *"`D = 0` bırakmak, malzemenin çekmede sınırsız dayanıklı olduğunu
> varsaymak demekti — krater hacmini ve dolayısıyla ejekta kütlesini,
> yani **β'yı** sistematik olarak küçültürdü."*

A17'nin belirtisi tam bu: `β = 1,4112`, gözlem `3,2225`, ve kaçan
kütle **merminin kendisi**; hedef payı tam sıfır.

## Koşulacak iki kol

Yerel RTX 3050 (`cuda:0`), iki aşamalı şema (`λ1 = 19`, `λ2 = 2`),
`t_end = 0,2 s`, üretim tohumu. Tek fark `--hasarli`.

| kol | komut |
|---|---|
| **K** (kontrol) | `faz48_iki_asama.py --t-end 0.2` |
| **H** (hasarlı) | `faz48_iki_asama.py --t-end 0.2 --hasarli` |

## Neden `β` bu koşuda **karar veremez**

`β`'nın ejekta ölçütü `r > 2R = 164 m`. `0,2 s`'de oraya yalnızca
`6,1 km/s` ile gelen mermi ulaşır. Yani `t = 0,2 s`'de `β` **tanım
gereği** merminin geri sekmesidir ve iki kolda da öyle kalacaktır.
Bunu koşudan sonra *"β değişmedi, demek ki hasar da değil"* diye
okumak, ölçütü etkisiz olduğu yerde sınamak olurdu — bu depoda
yerçekimiyle (`t/t_ff = 0,064`) ve `Y0` ile iki kez yapılmış hata.

Bu yüzden karar `0,2 s`'de **yanıt verebilen** büyüklüklere bağlanıyor.

## Ölçüt — **veriye bakılmadan**

### 0. Tesisat sınavı (önce bu)

- `D_max >= 0,999` **ve** `n_tam_kirik > 0` -> hasar modeli gerçekten
  koşuyor.
- Değilse ölçüm **geçersizdir**; bu bir sonuç değil, bir arızadır.

### 0b. Kontrol kolu referansı tutturmalı

- K kolunun `β`'sı `1,4112`'nin `%1`'i içinde olmalı. Değilse yerel
  makine TRUBA referansıyla karşılaştırılabilir değildir ve H kolu
  tek başına okunamaz.

### 1. Birincil — dışarı giden **hedef** momentumu

`r > R` **ve** `v_r > v_kaçış` olan **hedef** parçacıklarının eksenel
momentumu `|p_eksen_hedef|` (hedef maskesi `mermi_kesri < 0,5`).

- `H / K >= 3` -> hasar ejekta üretiminde **birinci mertebe** etkilidir;
  A17'nin kök neden adayı **doğrulanır**.
- `H / K < 1,2` -> hasar sebep **değil**; A17 için başka yere bakılır.
- arası -> kısmi; uzun kol gerekir.

### 2. İkincil — krater derinliği ve balistik `β`

- `krater_derinlik` ve `beta_bal` **aynı yönde** oynamalı. Oynamazsa
  birincil ölçüt tek başına okunmaz.
- `beta_bal` bu depoda bir kez geri alındı (`beta_bal_bandi = -43,8`);
  bu yüzden **ikincil** ve tek başına hiçbir şeye karar vermez.

### 3. Bu koşunun **karar veremeyeceği** şey

Gerçek `β` (yani gözlemin `3,2225`'i) bu kolda ölçülmez. Birincil
ölçüt geçerse gereken şey uzun kol (`t_end >= 20 s`) ve o ayrı bir
koşudur. Bu koşu yalnızca *"hasar ejekta üretimini değiştiriyor mu"*
sorusunu yanıtlar.

---

# EK — ölçüt **tek aşamalı kola** taşındı (2026-08-21, ikinci koşudan önce)

## Neden iki aşamalı kol bu soruyu yanıtlayamıyor

İlk çift koşuldu ve **tesisat sınavı düştü** (`D_max = 0,0000`).
Tanı ölçüldü:

| ölçülen (aşama-1, üretim sahnesi) | değer |
|---|---|
| `t = 4,6e-4 s`'de `P_min` | `-1,37e9 Pa` |
| `t = t₁ = 4,767e-3 s`'de `D_max` | **`0,562`** |
| aktarımdan **sonra** `D_max` | **`0`** |

Yani hasar gerçekten oluşuyordu; **aktarım onu taşımıyordu**. Taşıma
eklendi (`coarsen_to_sites(hasar=...)`, `WarpSolid3D(D0=...)`) ve
defter tam kapanıyor (`Sum m D` hatası `0,000e+00`). Ama taşınan
değer **küçük**: `D_max = 0,0016`, kütle ağırlıklı `7,3e-9` — çünkü
`t₁`'de yalnızca `r < 3 m` bölgesi hasarlı ve o kütle, `3,5 m`'lik
sitelere ortalanınca seyreliyor.

Daha önemlisi, aktarımın **yalnızca** `x, v, m, u, h` taşıdığı
görüldü: aşama-2 çözücüsü

| alan | aşama-2'de ne oluyor |
|---|---|
| `rho` | `rho0_kati / alpha0`'a **sıfırlanıyor** |
| `alpha` (ezilme) | `alpha0`'a **geri dönüyor** (P-α geri dönüşsüzdü) |
| `S` (deviatorik) | **sıfır** |
| `D` | sıfırdı; **artık taşınıyor** |

Yani şoklanmış, ezilmiş, gerilmiş madde aşama-2'ye *"aynı yerde, aynı
hızda, aynı iç enerjide **el değmemiş** madde"* olarak veriliyor. Bu
tek başına ayrı bir kusur ve **hasar kolunu kirletiyor**: iki aşamalı
kolda `β` değişmezse bunun sebebinin hasar mı yoksa durum sıfırlaması
mı olduğu **ayrılamaz**.

## Bu yüzden ölçüt tek aşamalı kola taşınıyor

`--tek-asama` (`λ = 2`, aktarım **yok**) durumu hiç sıfırlamıyor.
Mermi çözülmemiş (`A1 = 0,215`) ve KAYIT-045 bunun **başka bir
rejim** olduğunu ölçtü — ama iki kol da aynı rejimde olduğu için
karşılaştırma **kontrollü**.

Kayıtlı kontrol (`docs/olcumler/faz48_tek_asama.json`):

| | |
|---|---|
| `beta` | **`1,6175832076207557`** |
| `n_ejekta` | `803` |
| `N` | `11183`, `t_end = 0,2 s` |

## Ölçüt — **veriye bakılmadan**

### 0. Tesisat

- `D_max > 0` -> hasar bu çözünürlükte etkinleşiyor.
- `D_max = 0` -> **kendisi bir sonuç**: `3,5 m`'lik parçacıklarda şok
  o kadar yayılıyor ki çekme kusur eşiğine (`~17,5 MPa`) hiç
  ulaşmıyor. O zaman hasar bu çözünürlükte **koşulamaz** ve A17'nin
  cevabı hasar değil **çözünürlük + model-form** olur.

### 0b. Kontrol kolu

- Yerel hasarsız kol `1,6175832`'nin `%1`'i içinde olmalı.

### 1. Birincil — `β`

- `|β_H - β_K| / β_K >= 0,10` -> hasar **birinci mertebe**; A17'nin
  kök nedeni doğrulanır.
- `< 0,01` -> hasar sebep **değil**.
- arası -> kısmi.

### 2. İkincil

- `n_ejekta` ve kaçan hedef kütlesi aynı yönde oynamalı.

---

# EK-2 — kaçan madde **şoklanmış mı**? (2026-08-21, koşudan önce)

## Ölçülen durum

| kol | `β` | `n_ejekta` | kaçan kütle |
|---|---|---|---|
| iki aşamalı | `1,411216` | `28` | `579,40 kg` = merminin **tamamı** |
| tek aşamalı | `1,617583` | `803` | merminin **tamamı** |

Hasar kolu ölçüldü ve `β`'yı `5,9e-6` oynattı — **eleme**. Geriye
şu soru kalıyor: `β`'nın **tamamı** merminin geri sekmesiyse, o
sekme **fiziksel mi**?

DART `6144,9 m/s` ile çarpıyor; özgül kinetik enerji
`0,5 v² = 1,888e7 J/kg`. Tillotson bazaltın eşikleri:
`u_iv = 4,72e6`, `u_cv = 1,82e7 J/kg`. Yani gelen enerji **tam
buharlaşma eşiğinde**. Şok doğru çözülüyorsa mermi maddesi erimiş/
buharlaşmış olarak dağılmalı, katı gibi geri **sekmemeli**.

## Ölçüt — **veriye bakılmadan**

Kaçan parçacıkların (`r > 2R`, `v_r > v_kaçış`) kütle ağırlıklı özgül
iç enerjisi `u_kaçan`:

- `u_kaçan >= u_iv` (`4,72e6 J/kg`) -> kaçan madde **şoklanmış**;
  geri sekme fiziksel ve `β = 1,41` gerçek bir sonuçtur.
- `u_kaçan < 0,1 u_iv` (`4,72e5 J/kg`) -> kaçan madde **hiç
  şoklanmamış**; mermi katı gibi sekiyor ve `β`'nın **tamamı** bir
  ayrıklaştırma yapayıdır.
- arası -> kısmi.

Yan ölçüm (karar vermez): sahnedeki en yüksek `u`, ve merminin
başlangıç kinetik enerjisinin ne kadarının iç enerjiye döndüğü.
