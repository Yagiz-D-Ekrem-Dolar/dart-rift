# Değişiklik günlüğü

Sürümler [Semantic Versioning](https://semver.org/lang/tr/)'e uyar.

> Bu bir **kanıt** deposu. Her sürüm notu "ne eklendi"nin yanında
> "hangi ölçüm hangi koşulda yapıldı" ve **hangi iddia yanlış çıktı**
> sorularını da yanıtlar (`RULES.txt`: yanlış iddia silinmez, notla
> düzeltilir).

## [0.4.0] — 2026-08-18

FAZ 4: iki aşamalı çözünürlük ve Bayesçi çıkarım hattı. **G4 geçildi
(10/10).**

### Eklendi

- **İki aşamalı koşu** (ADR-0043): `λ₁ = 19` çekirdek → Lagrange'cı
  kabalaştırma → `λ₂ = 2`. Üç seviyeli; iki seviyelide `t₁`'de
  momentumun **`%69`**'u atılıyordu (`momentum_kapanis = 0,690`
  ölçüldü).
- **Parçacık başına `h`** (A′ yaklaşımı, ADR-0041). Beş seçenek
  ölçümle ikiye indi; her eleme bir sayıya dayanıyor.
- **Çıkarım hattı**: tasarım → ikinci derece vekil (kapalı formda LOO
  `q2`) → ızgara posterior'u → G4-C yargısı (C1/C2/C3).
- `setup/coarsen`: kütle/momentum/enerji `~1e-15` korunumlu aktarım.
  Kaybolan kinetik enerji iç enerjiye yazılır; açısal momentumun
  **korunmadığı** açıkça iddia ve test edilir.
- `mermi_kesri`: mermi kimliği kabalaştırmadan **kesir olarak** geçer.
  Bayrak yetmiyor çünkü kabalaştırma mermi ve hedefi aynı siteye
  karıştırabiliyor; kütle ağırlıklı taşındığı için toplam mermi
  kütlesi tam korunur (`< 1e-14`).
- `validation/h_policy`: sabit `h` yeterliliği **DART geometrisinde**
  ölçülür (ADR-0042'nin kendi yükümlülüğü).
- Depo altyapısı: `constraints-ci.txt`, `.pre-commit-config.yaml`,
  Dependabot, PR/issue şablonları, `CONTRIBUTING.md`, `SECURITY.md`.

### Değişti

- **`ADR-0042`**: `h` zamanla sabit, dolayısıyla `Ω ≡ 1` — bir
  yaklaşım değil, cebirsel sonuç (`∂h/∂ρ = 0` çarpanı terimi kapatır).
  ADR-0041 §5b madde 2 bununla **değiştirildi**.
- **`ADR-0046`**: çıkarım uzayı üç parametreden **bire** indirildi.
  `C2` `0,907 → 0,221`. **Bedeli:** iddia *"iç yapıyı çıkardık"*tan
  *"matris gözenekliliğini çıkardık"*a daraldı; `f_boulder` artık
  serbest değil ve Hera onu görüntüleyecek.
- Krater gözlenebiliri **çap** yerine **derinlik** (ADR-0045): çap
  gerçek 40 noktalı ensemble'da tek değer veriyordu.
- CI tek seri job'tan **dört ayrı job**'a (`lint`, `tests`,
  `determinism`, `gates`). Öncesinde lint düştüğü anda bütün fiziksel
  doğrulama atlanıyordu ve kanıt üretilemiyordu.
- `requires-python` `">=3.10"` → `">=3.10,<3.13"`. Üst sınır gerçek:
  hedef ortam NumPy 1.26.4 sağlıyor (ADR-0005) ve o sürüm 3.13'ü
  desteklemiyor.

### Düzeltildi

- `faz47_g4_kapi.py` ham koşu çıktısını özetlemiyordu; `A1`–`B4`'ün
  **yedisi birden** *"koşulmadı"* çıkıyordu. Ölçümler vardı,
  dönüşmüyorlardı.
- `A1` yanlış kaynaktan okunuyordu (`faz44` yakınsama kollarını
  ölçüyor, oysa `A1` çıkarımın kullandığı **sahneyi** sormalı):
  `0,2146` → **`2,0391`**.
- `B1`/`B3`: FAZ 4.4 `--steps` ile koşmuştu ve kollar `0,2155`–`0,6940 s`
  arasına dağılmıştı. Koruma doğru davranıp ölçütleri **yazmamıştı**;
  eşit `t_sim` ile yeniden koşuldu.
- Gözeneksiz kol cismi `t = 0`'da gerilmede başlatıyordu
  (`m/V = 1537` iken `ρ = 2700`, `%76` hacim uyuşmazlığı).
- Ruff `191 → 0`. Aynı ağaç ruff 0.15 ile 191, 0.16 ile 183 hata
  veriyordu; CI araç zinciri bu yüzden artık sabit.

### Bilinen açık

- **A17** — motor `β ≈ 1,41` üretiyor, ölçülen periyot değişimi
  `3,2225` istiyor. Ölçümle elenen adaylar: koşu süresi
  (`0,2 → 600 s`, `3000×`, `β` **bit düzeyinde** aynı), mukavemet
  (`Y0` `1 → 2,15e6 Pa`, altı mertebe, `β` bit düzeyinde aynı),
  yerçekimi, gözeneklilik (`+%7,5`), çözünürlük (`−%17`). Hepsi
  ADR-0028'in zaten yazdığı yere çıkıyor: kontrol yüzeyini geçen madde
  hedef ejektası değil **merminin geri sekmesi**.
- **A11** — krater çapı gerçek ensemble'da hâlâ tek değer.
- **A12** — A17 ile örtüşüyor.

### Kendi düzeltmelerim

Bu turda üç kez kendi çıkarımımı çürüttüm ve üçü de kayıtlı:

1. *"Koşu süresi elendi"* — `t = 100 s`'de karar vermiştim; `2R` varış
   süresi `~550 s` ölçülünce erken olduğu görüldü. `600 s` koşuldu.
2. *"Yerçekimi elendi"* — sınav `t/t_ff = 0,064`'te yapılmıştı, yani
   yerçekiminin **etkisiz olmak zorunda olduğu** yerde.
3. Sıkıntı raporu sayacını `37 → 23` diye *"düzelttim"*; yanlıştı.
   Bölüm 2 maddeleri iki biçimde yazılı (`23` tablo satırı + `14`
   başlık = `37`) ve testi düşüren şey benim düzeltmemdi.

## [0.3.0] — 2026-07-28

FAZ 0–2: deterministik altyapı, SPH şok çekirdeği, malzeme fiziği.
**G0/G1/G2 geçildi.**

> Bu sürüm o tarihte ilan edilmiş ama **etiketlenmemişti**; etiket
> geriye dönük olarak `ce9ed93`'e konuldu — `2026-07-28`'in `0.3.0`
> sürümünü taşıyan son commit'i.
