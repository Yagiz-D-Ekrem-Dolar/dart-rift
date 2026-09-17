# ADR-0050 — Literatür paketi: geç evre şeması, ölçüm ve gözlem düzeltmeleri

**Durum:** ÖNERİ (karar kullanıcıda) · **Tarih:** 2026-09-17
**Öncül:** KAYIT-064 (U/V: model gözleme ulaşmıyor),
[`docs/LITERATUR-DART-SIMULASYONLARI.md`](../LITERATUR-DART-SIMULASYONLARI.md)
**Kod:** `warp_core/solver_solid.py`, `inference/forward.py`,
`observables/beta_iki_yontem.py`, `observables/dart_gozlemleri.py`,
`inference/tarih_esleme.py`, `setup/impactor.py`, `setup/blok_cozunurluk.py`

---

## 1. Bağlam

Protokol U (20 koşu, 0,1 s) ve V (10 koşu, 0,2 s) kilitli olarak
**"hiçbir varyant ulaşmıyor"** dedi: en iyi model `β ≈ 2,05`, gözlem
`3,12 ± 0,34`. Literatür taraması (L1–L20) aynı çarpışmayı üreten
çalışmalarda **üç ortak özelliğin** bizde eksik olduğunu gösterdi:

| | onlar | biz (U/V) |
|---|---|---|
| süre | **30 dk – 2 sa** | 0,1–0,2 s |
| geç evre | düşük ses hızlı malzeme şeması | yok |
| kohezyon | en iyi uyum **< birkaç Pa**; taranan 0–500 Pa | önsel `≥ 1e3 Pa` |

Raducan & Jutzi 2022 (L1), 75 m küre, `f = 0,6`: `Y₀ = 50/10/1/0 Pa` →
`β = 3,63 / 4,18 / 4,66 / 4,93`. Bizim `Y₀ = 10 Pa` koşumuz 0,1 s'de
`β ≈ 2,05` verdi. Açığın yönü ve büyüklüğü **süre + önsel kırpmasıyla**
uyumlu — ama bu bir hipotezdir; kendi kodumuzla sınanmadan sonuç değildir.

## 2. Karar (önerilen)

Literatürde **ölçülmüş etkisi olan** değişiklikler koda eklenir; hepsi
**varsayılan kapalı** ve eski yollar **bit-aynı** kalır. Hangisinin üretime
gireceğini **Protokol W** (kıyas sınaması) ve ondan sonraki protokoller
karara bağlar.

| # | değişiklik | kaynak | durum |
|---|---|---|---|
| 1 | **geç evre şeması**: `t_geçiş`'te `P = A_geç·μ`, Tillotson enerji terimleri `0`, `B = 0`, kayma modülü ve `S` aynı oranda küçülür | L1, L3, L8 | eklendi (`gec_evreye_gec`) |
| 2 | **uzak kaçanı dondur**: `r > k·R` ve `v_r > v_esc` parçacık adımı kısıtlamasın | ADR-0050 | eklendi |
| 3 | **β iki yöntem** (kaçan momentum + bağlı kütle merkezi) + **ejekta koni açısı** | L1, L17 | eklendi |
| 4 | **elipsoit kaçış ölçütü** (`(x/a)²+(y/b)²+(z/c)² > 1`) | L1, L2, L11 | eklendi |
| 5 | **üç küre mermi** (%88 gövde + 2 × %6 panel, 2,215 m) | L9, L10 | eklendi |
| 6 | **gözlenen β'ya yeniden şekillenme** düzeltmesi (yan yana) | L16 | eklendi |
| 7 | **ek gözlem sabitleri** (ejekta kütlesi, koni açısı, Cheng bağıntısı) | L4, L17 | eklendi |
| 8 | **tarih eşleme** `I < 3` + model eksikliği terimi | L19 | eklendi (yeni protokoller için) |
| 9 | **blok çözünürlük tanısı** (blok başına ≥ ~30 parçacık) | L8 | eklendi |
| 10 | **çarpma açısı / hedef şekli / mermi kütle-hız-yoğunluğu** CLI | L20, L1, L2 | eklendi |

## 3. Geç evre şeması — neden bu biçim

`compute_dt` boyuna elastik hızdan geliyor: `c_long = √(c_s² + 4G/3ρ)`.
Kohezyonsuz granüler akışta hem `c_s` hem `G` gereksiz yere büyüktür; L1
bunu `A ≈ 0,1 MPa` (L3: `0,027 MPa`) ile küçültüyor. Bizde ölçülen (kafes
sınavı): `A = 1e5 Pa` ile `c_s` `~6 m/s`'e iniyor ve `dt` **50 kattan fazla**
büyüyor. Uygulama Tillotson parametre setini değiştirerek yapıldı; böylece
EOS, P-α ve dayanım çekirdekleri **aynen** kullanılıyor, yeni bir kod yolu
doğmuyor.

**Süreklilik:** `u` ve `v` değişmediği için `e_kin + e_int` geçişte tam
sürekli (sınavla ve gerçek koşuda doğrulandı). `S` aynı oranla ölçeklenir →
elastik **gerinim** sürekli. Hasar modeliyle birlikte **reddedilir** (Young
modülü ayrı kuruluyor; sessizce yanlış çalışmasın).

## 4. Neyi çözmüyor

- Bu ADR `β`'nın gözleme ulaşacağını **söylemiyor**. Yalnız literatürde
  ulaşan modellerin kullandığı araçları bizde kullanılabilir yapıyor.
- Çözünürlük yakınsamazlığını çözmüyor (L1'de de düşük çözünürlük hızlı
  ejektayı `~%15` fazla veriyor; bizde kaba → orta `−%13`).
- β tek başına iç yapıyı belirlemiyor (L2, L11, L15): ejekta kütlesi ve koni
  açısı çıkarıma girmeden `α_b`/`f` ayrışması beklenmemeli.

## 5. Geriye dönüklük

- U ve V'nin **kilitli yargısı değişmez** (kural koşudan önce yazılmıştı).
  Yeni karar kuralı (tarih eşleme) yalnız **yeni** protokollerde kullanılır.
- Gözlenen `β` kilitli değeri (`3,2228` arayüz, protokolde `3,12 ± 0,34`)
  **olduğu gibi** kalır; yeniden şekillenme düzeltmesi **yan yana** alandır.
- Yeni seçeneklerin hepsi koşu kimliğine (`_fizik_ozeti`) girer: eski
  çıktılar yeni koşularla karışamaz.

## 6. Maliyet

Geç evre şeması olmadan saat mertebesi **imkânsız** (0,1 s ≈ 13 dk kaba).
Şemayla adım `~5e-3 s` mertebesine çıkıyor; gerçek maliyet **ölçülecek**
(Protokol W'nin ilk adımı zamanlama koşusudur, bilimsel sonuç değildir).
