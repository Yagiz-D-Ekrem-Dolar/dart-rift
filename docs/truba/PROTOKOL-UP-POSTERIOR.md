# Protokol UP — **gözemli seçimi, önsel duyarlılığı, tarih eşleme** (KİLİTLİ)

**Yazıldı:** 2026-10-08, **havuz verisi okunmadan ÖNCE.** Havuz
(`1592569`) o an koşuyordu, TRUBA erişimi kapalıydı: **hiçbir nokta
görülmedi.**
**Öncül:** [PLAN-90-GUN](../PLAN-90-GUN.md) §1 (1. kuşak 7-8),
[PROTOKOL-HAVUZ](PROTOKOL-HAVUZ-URETIM.md), KAYIT-075 (beş karar),
KAYIT-077 §4 (üç parametre iddiası), ADR-0058.
**Kod:** `src/dartrift/observables/aday_gozlemliler.py`,
`src/dartrift/inference/gozlemli_secimi.py`,
`src/dartrift/inference/tanimlanabilirlik.py`,
`src/dartrift/inference/tarih_esleme.py`.

---

## 1. Üç ayrı soru

| § | soru | niçin burada |
|---|---|---|
| 2-4 | `θ`'nın **kaç** bileşenini öğrenebiliyoruz ve **hangi gözemlilerle**? | KAYIT-077'de "3 parametre" iddiasını ben açtım, kuralını yazmam gerek |
| 5 | Sonuç **önselden mi geliyor** veriden mi? | `Y₀` önseli kilitli ama tek seçimdi |
| 6 | Posterior **aşırı kendinden emin** mi? | kalibrasyonun ikinci bağımsız sınavı |

Üçü de **sıfır GPU**. Üçünün yargı kuralları aşağıda, veriden önce.

---

## 2. Aday havuzu ve iki dürüstlük kapısı

`aday_gozlemliler.py` kaydedilmiş `npz`'den `10` aday hesaplıyor.
Posteriora girmek için **iki** kapı:

### Kapı A — `gozlenen`

Adayın **DART karşılığı** olmak zorunda. Yoksa posteriora giremez; yalnız
öngörü olarak raporlanır. `bagli_kutle` böyle: hesaplanıyor, girmiyor.

### Kapı B — `karsilik_grubu`

**Aynı ölçümün iki özeti bağımsız gözemli değildir.** `v_ort` ile `v_p50`
aynı hız dağılımının iki özeti; ikisini birden olabilirliğe koymak
belirsizliği sahte biçimde küçültür. Her gruptan **en çok bir** aday
seçilir.

Kütükteki gruplar: `periyot_degisimi` (`beta`), `ejekta_kutlesi`
(`M_kacan`), `ejekta_hiz_dagilimi` (`v_ort, e_hiz, v_p50, v_p90`),
`ejekta_konisi` (A95 yüzünden **kapalı**), `gozlenemez` (`bagli_kutle`).

> **Yapısal bulgu, veriden önce biliniyor:** DART karşılığı olan **açık**
> grup sayısı **üç** (`periyot_degisimi`, `ejekta_kutlesi`,
> `ejekta_hiz_dagilimi`). A95 düzelmezse dördüncü yok. `k = 3` gözemli
> ile `d = 3` parametre, **en iyi durumda** tam belirli — pay yok.
> Bu, sınavla kilitli (`test_GERCEK_kutukte_uc_acik_grup_var`).

### Tutarlılık kapısı

Her adayın kendi koşusunun `ejekta_ayrismasi` kaydıyla tutarlılığı
`1e-6` toleransla sınanır. Tutarsız koşu **atılır**, sessizce
düzeltilmez.

---

## 3. Seçim yargısı — KİLİTLİ

### Ölçüm

`grup_kisitli_secim`: her gruptan en çok bir aday, `gozlenen=True`,
E-optimal ölçüt (`alt_kume_degeri` → mevcut `fisher_yonleri`,
`FISHER_ESIGI`). Yeni ölçüt **uydurulmadı**: tanımlanabilirlik modülünün
zaten kilitli eşiği kullanılıyor.

Çıktı: seçilen `k` gözemli ve **öğrenilen yön sayısı** `n_yon`
(Fisher eşiğini geçen özdeğer sayısı).

### Yargı

| yargı | koşul | sonucu |
|---|---|---|
| **UC YON DA OGRENILIYOR** | `n_yon = 3` | `θ`'nın üç bileşeni için posterior **yayımlanır** |
| **N YON OGRENILIYOR (YETMIYOR)** | `n_yon` 1 ya da 2 | **yalnız o kadar birleşim** için posterior; kalan bileşenler "önselden ayırt edilemez" yazılır. Başlık `n_yon` parametreli olur. |
| **HICBIR YON OGRENILMIYOR** | `n_yon = 0` | posterior yayımlanmaz; tarih eşleme (§6) tek sonuç olur |

**Değiştirilmesi yasak:** `FISHER_ESIGI`'ni `n_yon` büyüsün diye
indirmek. Eşik ADR'de kilitli; indirilirse yargı **geçersiz** sayılır.
(PROTOKOL-HAVUZ §6'daki "paydayı büyüterek geçme yasağı"nın eşi.)

### Beklenti — şimdi yazıyorum ki sonra ayarlamayayım

`n_yon = 2` bekliyorum. Gerekçe: `β` ile `M_ejekta` fiziksel olarak güçlü
bağıntılı (ikisi de kazılan kütleyle sürülüyor), hız dağılımı eğimi
üçüncü ve **zayıf** bir kısıt. `n_yon = 3` çıkarsa KAYIT-077'de açtığım
iddia doğrulanmış olur; `2` çıkarsa iddia **kapanır** ve öyle yazılır.

---

## 4. Yerellik — bu yargının en zayıf yeri

Jakobyen **tek noktada** ve **doğrusallaştırılmış** alınıyor.
`rank(F) ≤ min(k,d)` yerel bir ifadedir; küresel bir yasa **değil**
(bunu daha önce fazla genel söyledim, KAYIT-077 §4'te düzeltildi).
Dolayısıyla:

### Çok noktalı denetim — zorunlu

Jakobyen **en az 5** `θ` noktasında alınır: posterior kipi + önselin
`4` köşe bölgesinden birer nokta.

| yargı | koşul |
|---|---|
| **YON SAYISI KARARLI** | `n_yon` beş noktanın hepsinde aynı |
| **YON SAYISI NOKTAYA BAGLI** | değişiyor → raporda **en küçük** `n_yon` kullanılır ve dağılım tablo olarak verilir |

En küçüğü almak kasten muhafazakâr: en iyi noktayı seçip onu raporlamak
kiraz toplamaktır.

### Kovaryans varsayımı

`kosegen_kovaryans` **köşegen** — bu bir **varsayım**, ölçüm değil.
ADR-0058 §3'te ölçüldü: `ρ: 0 → 0,8`, `α_b`'nin büzülmesi
`0,372 → 0,708`. Yani varsayım sonucu **iki kata yakın** değiştiriyor.

**Kural:** seçim raporu `ρ ∈ {0; 0,4; 0,8}` için **üç kez** koşulur.
`n_yon` üçünde aynı değilse yargı **YON SAYISI KOVARYANSA BAGLI** olur ve
en küçüğü alınır. Her seçim raporunda `secim_raporu`'nun yazdığı yerellik
uyarısı **silinmez**.

---

## 5. Önsel duyarlılık analizi

### Niçin

`Y₀` önseli DO ile seçildi (`ÖNSEL GÖZLEMİ İÇERMİYOR`, `p = −0,1791`) ve
KAYIT-075'te kilitlendi. Ama o **bir** seçimdi. Sonucun önselden mi
veriden mi geldiğini ölçmezsek, jüride cevabı olmayan soru kalır.

### Ölçüm

Posterior, **aynı** olabilirlik ve **aynı** vekille, üç önselle yeniden
hesaplanır:

| ad | `Y₀` önseli | niçin |
|---|---|---|
| `KILITLI` | kilitli seçim (ADR / KAYIT-075) | referans |
| `DUZ_LOG` | `log10 Y₀ ~ Düzgün[0, 5]` | bilgisiz uç |
| `KAYDIRILMIS` | kilitli önselin kipi `×3` kaydırılmış | yanlı uç |

`α_b` ve `f` önselleri sabit tutulur (tek seferde tek şey değişir).

Her biri için: posterior kipi, `%68` aralığı ve **büzülme**
(`1 − Var_posterior / Var_onsel`) her eksende.

**`σ_onsel`** = üç önsel arasında posterior kipinin en büyük kayması
(`Y₀` için `log10` biriminde = dex, `α_b` ve `f` için bağıl).

### Yargı — KİLİTLİ

| yargı | koşul | sonucu |
|---|---|---|
| **SONUC VERIDEN GELIYOR** | `σ_onsel ≤ 0,15 dex` (`Y₀`) ve `≤ 0,10` (diğerleri) | posterior önselden bağımsız sayılır |
| **ONSEL ETKILI** | `0,15 < σ_onsel ≤ 0,50 dex` | posterior yayımlanır ama **üç önselin tablosu zorunlu ek** olur ve özet cümlede yazılır |
| **SONUC ONSELDEN GELIYOR** | `σ_onsel > 0,50 dex` | `Y₀` için **tek sayı verilmez**; yalnız üst/alt sınır ve "veri `Y₀`'yı belirlemiyor" yazılır |

`0,50 dex` eşiği şimdi seçildi: `Y₀` önseli `5 dex` genişliğinde; kipin
`%10`'undan fazla kayması, verinin önseli yenemediği anlamına gelir.

---

## 6. Tarih eşleme (Vernon) — posteriorun **yanında**

### Niçin ayrı

Posterior bir **olabilirlik** varsayımı taşıyor (Gauss artık, köşegen
kovaryans, vekil hatasının ihmali). Tarih eşleme bunların çoğunu
taşımıyor: yalnız "bu `θ` gözlemle **bağdaşmaz** mı?" diye sorar. İkisi
aynı bölgeyi veriyorsa güven artar; vermiyorsa posterior fazla kendinden
emindir.

### Ölçüm

Seçilen gözemliler üzerinden, her `θ` için:

    I(θ) = maks_j |E_j(θ) − z_j| / sqrt( Var_j(θ) + sigma_j^2 )

`E`, `Var` vekilden; `z` DART ölçümü; `sigma_j^2` = gözlem hatası + model
eksikliği bütçesi (`tarih_esleme.py`'deki **ölçülmüş** terimler; `~0`
çekme dayanımı ve mermi geometrisi terimleri **paydaya girmez**, orada
işaretli).

Kesme **`I > 3`** → `bagdasmaz`. Bu Vernon'un `3σ` kuralı; bizim
seçimimiz **değil**, alanın kuralı — bu yüzden ayarlanmaz.

`V_bagdasir` = önsel hacmin bağdaşır kalan oranı.
`V_post68` = posteriorun `%68` hacminin önsele oranı.

### Yargı — KİLİTLİ

| yargı | koşul | sonucu |
|---|---|---|
| **IKI YONTEM UYUSUYOR** | posterior `%68` kütlesinin `≥ %90`'ı bağdaşır bölgede **ve** `V_bagdasir / V_post68 ≤ 10` | posterior yayımlanır, tarih eşleme doğrulayıcı ek olur |
| **POSTERIOR DAR** | `V_bagdasir / V_post68 > 10` | posterior yayımlanır ama **tarih eşleme bölgesi ana sonuç** olarak verilir; posterior "olabilirlik varsayımına koşullu" etiketiyle |
| **CELISKI** | posterior `%68` kütlesinin `< %90`'ı bağdaşır bölgede | **ikisi de yayımlanmaz**; çelişkinin kaynağı aranır ve KAYIT'a yazılır |

### SBC düşerse

PROTOKOL-HAVUZ §6: SBC `YANLI` ise posterior yayımlanmaz. O durumda
**tarih eşleme tek sonuç** olur ve proje "kalibre posterior" değil
"eleme ile daraltılmış parametre bölgesi" sunar. Bu bir başarısızlık
değil, daha zayıf ama dürüst bir sonuçtur — ve PLAN-90-GUN'da riski
`~%25` yazılı.

---

## 7. Bu protokolün yapmadığı şey

- **Beş kilitli kararı değiştirmiyor** (KAYIT-075). `Y₀` önseli §5'te
  *sınanıyor*, değiştirilmiyor.
- **Eşik indirmiyor.** `FISHER_ESIGI`, `I > 3`, SBC kapısı: üçü de
  dışarıdan ve önceden.
- **Yeni ölçüt uydurmuyor.** Seçim, var olan `fisher_yonleri`'ni çağırıyor.
- **A95'i çözmüyor.** Koni grubu kapalı kalırsa `k = 3`'te kalınır;
  A95 düzeltmesi 3. kuşak işi (PLAN-90-GUN 14).
