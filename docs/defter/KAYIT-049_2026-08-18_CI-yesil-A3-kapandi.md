# KAYIT-049 — CI **292 koşu sonra** yeşil, A3 kapandı, A17'de üç eleme (2026-08-18)

**Kapsam:** depo sağlığı · A3 (ADR-0042 yükümlülüğü) · A17 elemeleri
**Öncül:** [KAYIT-048](KAYIT-048_2026-08-11_G4-gecildi.md)
**Koşular:** TRUBA `kolyoz-cuda` (H100) işler `1506765`, `1506779`, `1506785`

---

## 1. `main` 292 koşudur kırmızıydı ve kimse bilmiyordu

Dışarıdan gelen bir denetim şunu gösterdi: son yeşil CI koşusu **#127**
(`2026-08-02`); o günden `#419`'a kadar **292 koşunun hiçbiri**
geçmemiş.

Kök neden tek ve mekanikti: CI **tek bir seri job**'ti.

```
ruff -> config -> pytest+coverage -> determinism -> kapilar -> red-team
```

Ruff düştüğü anda sonraki **bütün** adımlar atlanıyordu.

> İki hafta boyunca *"birim testler geçiyor"*, *"kapsam ≥ %85"*,
> *"determinizm geçiyor"* iddialarının **hiçbiri** doğrulanabilir
> değildi. `183` biçimsel lint hatası, fiziksel doğrulama testlerinin
> durumunu **görünmez** yaptı.

Bu, deponun kendi kuralının (*"test geçilmediyse iddia edilmez"*) tam
tersine dönmüş hâliydi: test **koşulmuyordu** ve bu kimseye
söylenmiyordu.

### Ruff `191 → 0`

Yerelde `0.15.21` ile **191**, CI'da `0.16.x` ile **183** — **aynı
ağaç**. Lint sonucunun araç sürümüne göre değişmesi tek başına araç
zincirinin sabitlenmesi gerektiğinin kanıtı.

| kural | adet | nasıl |
|---|---|---|
| `I001` | 77 | otomatik |
| `F541` | 40 | otomatik |
| `B905` | 29 | `strict=False` — **davranış birebir korundu** |
| `E702` | 20 | elle bölündü |
| `F401` | 10 | otomatik |
| `E501` | 9 | belge satırları **kısaltıldı**, eşik gevşetilmedi |
| `E741` | 2 | `l` → `satir` |
| `E401` | 2 | otomatik |
| `F841` | 1 | `faz48`'de ölü `x0_h` |
| `E402` | 1 | `mass_ratio`: öbekten kopmuş import |

`B905` için `strict=True` çoğu çağrı noktasında daha savunmacı olurdu
(sessiz `zip` kırpması bu depoda gerçek bir hata sınıfı). Ama `29`
çağrının anlamını tek hamlede değiştirmek `RULES.txt`'in yasakladığı
**sessiz davranış değişikliği** olurdu.

### Tam takım **ölmüyormuş**

Daha önce *"yerel takım `%26`'da sessizce ölüyor"* diye kaydetmiştim.
**Yanlıştı** — kendi araç zaman aşımımdı. Ölçüldü:

> `2:40:30`, **1346 geçti / 3 düştü / 14 atlandı**.

---

## 2. Üçüncü test kusuru **benim düzeltmemdi**

`test_KAPANAN_ve_ACIK_sayilari_TABLOLARLA_tutuyor` düşüyordu. Sebep:

Sıkıntı raporunun başlığı `Kapanan: 37` diyordu; ben `23` sanıp
*"düzelttim"*. Bölüm 2 maddeleri **iki biçimde** yazılı — `| N |`
tablo satırı (`23` tane) ve `### N` başlığı (`14` tane) — toplam
**`37`**, numaralar `1..37` kesintisiz. Ben yalnızca tablo satırlarını
saymıştım.

> Testin yorumu tam bu tuzağı anlatıyordu: *"§2'de İKİ biçim var ve
> ikisi de sayılmalı."* **Test haklıydı, ben değildim.**

Rapora not olarak yazıldı, silinmedi.

---

## 3. A3 **kapandı** — ADR-0042 kendi yükümlülüğünü ödedi

ADR-0042 metnine şunu yazmıştı ve yerine getirilmemişti:

> *"Ölçüm FAZ 4.4'te DART geometrisinde **tekrarlanacaktır**."*

Ölçüldü (iş `1506785`, iki aşamada `101` örnek):

| | küp (KAYIT-035) | **DART** |
|---|---|---|
| `N_komşu` aralığı | `268,2 – 551,5` | **`379,1 – 403,5`** |
| salınım | `2,06×` | **`1,064×`** |
| taramanın kapsadığı | `56,1 – 650,5` | — |

DART salınımı kapsamanın **içinde** ve küpün kendi salınımından **daha
dar**. Yargı `kanit_gecerli`; ADR-0042 yeniden açılmıyor.

### İlk ölçüm yanlıştı

İlk koşuda salınım `1,000×` çıktı — `101` örnek, `207 252` değer, hepsi
`379,1`. Sonuç değil **maske hatasıydı**:

| | küp (Sedov) | DART |
|---|---|---|
| enerji nerede | **merkez** | **yüzey** |
| `r ≤ 0,6R` neyi kapsar | şok bölgesini | **hiç şok görmeyen çekirdeği** |

Küpün tarifini küreye doğrulamadan taşımıştım. Maske parçacık başına
destek ölçütüne çevrildi (`r_i + 2h_i ≤ R`) ve iki test hatanın geri
gelmesini engelliyor.

---

## 4. A17 — üç ölçüt koştu, **üçü de hipotezimin aleyhine**

Ölçütler **veriye bakılmadan** yazıldı.

| aday | ölçüm | sonuç |
|---|---|---|
| koşu süresi | `t_end = 600 s` (`3000×`), iş `1506765`, `22:50` duvar | `β = 1,411216` — `t = 0,2 s` ile **bit düzeyinde aynı** |
| mukavemet | `Y0 = 1 / 10 / 100 Pa`, iş `1506779` | üçü de `1,411215` |
| yerçekimi | enerji ölçütü, `t = 100 s` | `1,7167 → 1,9731` |

### İki kez kendi elememi çürüttüm

1. *"Koşu süresi elendi"* demiştim — `t = 100 s`'de karar vermiştim ve
   `2R` varış süresi `~550 s` ölçülünce **erken** olduğu görüldü.
   `600 s` koşuldu; süre gerçekten sebep değilmiş ama **gerekçem
   yanlıştı**.
2. *"Yerçekimi elendi"* — sınav `t/t_ff = 0,064`'te yapılmıştı, yani
   yerçekiminin **etkisiz olmak zorunda olduğu** yerde
   (`t_ff = 1562 s`).

### Mukavemet rejimi: doğru soru, yanlış cevap

`Y0/ρ ≈ GM/R` geçişi **`Y0 ≈ 6,14 Pa`**'da. FAZ 4.12 `3513 → 2,15e6 Pa`
taramıştı — geçişin `572` ile `350 000` katı arasında, **baştan sona
aynı rejimde**. *"β `Y0`'a duyarsız"* bulgusu *"`Y0` önemsiz"* demiyor,
**"aralık tek rejimde"** diyordu.

Geçişin iki yanı sınandı (`1 / 10 / 100 Pa`) ve `β` yine **bit
düzeyinde** aynı çıktı. Yani `Y0` da değil — ama bu kez **doğru
aralıkta** ölçüldü.

### Hepsi ADR-0028'in yazdığı yere çıkıyor

`n_ejekta = 28`, kaçan kütle `579,40 kg` — **her koşuda**. `579,4 kg`
DART'ın kütlesi.

> **Hedef parametreleri `β`'yı değiştiremez çünkü `β` hedefi
> ölçmüyor.** Etki eden iki şey (gözeneklilik `+%7,5`, çözünürlük
> `−%17`) merminin ayrıklaştırmasını veya çarptığı yüzeyin sertliğini
> değiştiriyor.

Bu, ADR-0028'in ve A12'nin zaten yazdığı sonuç. Bu turda **üçüncü** kez
aynı yere geldim; farkı, bu kez ölçmüş olmam.

### Yapılan: kimlik artık taşınıyor

Kusur ölçülebilir değildi çünkü kabalaştırmadan sonra `is_impactor`
hiçbir parçacıkta korunmuyordu ve `hedef = ~is_impactor` **her yerde
`True`** oluyordu — kaçan `28` parçacık *"hedef ejektası"* etiketiyle
sayılıyordu.

`coarsen_to_sites` artık `mermi_kesri` taşıyor: bayrak değil **kesir**,
çünkü kabalaştırma mermi ve hedefi aynı siteye karıştırabiliyor. Kütle
ağırlıklı taşındığı için `Σ m_k f_k = Σ m_i f_i` (`< 1e-14`).

> A17 **kapanmadı**. Kapanan şey: bundan sonra *"ejekta mı, sekme mi"*
> sorusu tahminle değil **ölçümle** yanıtlanacak.

---

## 5. Depo artık dışarıdan okunabilir

| | |
|---|---|
| CI | `lint` / `tests` / `determinism` / `gates` **ayrı** job |
| araç zinciri | `constraints-ci.txt` — üst sınıra sabit |
| action'lar | commit SHA'sına sabit (v4/v5 → v7, Node 20 uyarısı da gitti) |
| runner | `ubuntu-24.04` (`ubuntu-latest` kayan hedefti) |
| sürüm | `v0.3.0` geriye dönük `ce9ed93`'e, `v0.4.0` yayında |
| açık sıkıntılar | issue [#6](https://github.com/Yagiz-D-Ekrem-Dolar/dart-rift/issues/6), [#7](https://github.com/Yagiz-D-Ekrem-Dolar/dart-rift/issues/7) |

Bir gerileme de ben ürettim: `on: push` filtresiz kalınca her dal **iki
kez** koştu ve Dependabot'un açtığı `5` PR ile birlikte `60` job kuyruğu
doldurdu. Ayrıca `cancel-in-progress: ${{ github.ref != 'refs/heads/main' }}`
`main`'i **korumadı** (koşu `#433` iptal oldu); ifadeye güvenmek yerine
grup `main`'de SHA ile ayrıldı.
