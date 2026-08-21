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
