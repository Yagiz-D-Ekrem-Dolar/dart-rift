# `R` kampanyası sonucu — uzamsal yakınsama **DÜŞTÜ**

**Tarih:** 2026-09-06 · **Ölçüt:** Protokol v2/v2.1, koşudan **önce**
commit'lendi (`scripts/yakinsama_raporu.py`, `c94d74e`)

---

## Sonuç

```
       kol         N              sok    defter   plato
     Rb_R1     17201            KISMI    KAPALI   GECTI
     Rb_R2     69886            KISMI    KAPALI   GECTI

             nicelik         Rb_R1         Rb_R2      A1      A2
    delta_beta_hedef             0     0.0331017   DUSTU   DUSTU
            M_ejekta             0       93.2086   DUSTU   DUSTU
    P_ejekta_eksenel             0       -117854   DUSTU   DUSTU

UZAMSAL YAKINSAMA (A1, uc nicelik BIRDEN): DUSTU
```

Dört kapıdan **üçü yeşil** (şok `KISMI`, defter `1,1e-14` /
`1,2e-14` ile kapalı, zamansal plato geçti), **uzamsal yakınsama
kırmızı**.

## Neden kırmızı — sayı yok, *nicelik* yok

`R1`'de gözlenebilir **var olmuyor**:

| `Rb_R1` (`N = 17 201`) | değer |
|---|---:|
| `n_kacan_hedef` | **`0`** |
| `M_ejekta` | **`0,0` kg** |
| `beta_hedef` | **`1,000000`** |
| `beta_mermi` | `0,21861` |
| `kutle_kacan_mermi` | **`579,4 kg` = merminin TAMAMI** |

Yani `R1`'de hedeften **hiç** madde kaçmıyor ve `β_bal = 1,2186`'nın
**tamamı merminin geri sekmesi**. Defter `1,14e-14` ile kapalı —
sıfırlar eksik anahtar değil, **ölçülmüş sıfır**.

`R2`'de (`4×` parçacık) gözlenebilir `16` parçacıkla doğuyor.

**İki nokta arasındaki bağıl fark tanımsız** (`0`'a bölme). Bu bir
yakınsama dizisi değil; gözlenebilirin **ortaya çıkışı**.

## `R3` neden yok

`R3` (`N = 493 330`) `48` saatlik sınırda bitemiyor: ölçülen
`0,062` adım/s ile `t_end = 0,1 s` için **`224` saat** gerekiyor.
Sebebi komşu arama yarıçapının `2·h_max` olması (rapor **A52**).
`5:16`'da iptal edildi.

Üç noktalı Richardson **şimdilik mümkün değil**; `σ_num` bu yüzden
`nan` (hesaplanamadı) — kural gereği, uydurulmadı.

## Protokolün dediği

> *Dört kapı birden yeşil değilse `beta_hedef` gözlenebilir olarak
> **KULLANILMAZ**.*

Kural koşudan önce yazılmıştı ve **uygulanıyor**: `β_hedef` şu an
çıkarıma verilebilecek bir gözlenebilir **değil**.

## Bu, projenin durduğu anlamına gelmiyor

Kırmızının sebebi ölçülmüş ve adı konmuş: gözlenebilir `16`
parçacıkla, yani ayrıklaştırma tabanında yaşıyor. Bunun **nedeni**
artık iki adaya inmiş durumda ve ikisi de sınanıyor:

| aday | kayıt | deney |
|---|---|---|
| geri dönüşsüz kompaksiyon şoku yutuyor | A45 | **E1** |
| matris çekmede bağlı kalıyor (`−15,19 MPa`) | **A51** | **E2** |

Ayrıca `R` kampanyasının kendisi, uzman incelemesinden (A46–A50)
**etkilenmedi**: `R` kolları `faz48_iki_asama.py` üzerinden koşuyor
ve defteri doğrudan hesaplıyor; kusurlar ensemble/çıkarım yolundaydı.

## Ne yapılmalı — yakınsamayı kurtarmanın üç yolu

1. **Yarıçapı parçacık başına yap** (A52'nin asıl çaresi). `R3`'ü
   mümkün kılar; tasarım işi.
2. `t_end`'i `~0,01 s`'ye indirip **üç kolu da** yeniden koş.
3. Gözlenebiliri değiştir: tek `β` yerine `M(>v)` dağılımı
   (`docs/BETA-HEDEFI.md`, `scripts/hiz_tanisi.py`).

Üçü de E1/E2 sonuçlanmadan başlatılmamalı — uzmanın uyarısı:
*"Bu üç adım sonuçlanmadan pahalı parametre taraması yapmak,
mevcut belirsizlikleri çoğaltır."*
