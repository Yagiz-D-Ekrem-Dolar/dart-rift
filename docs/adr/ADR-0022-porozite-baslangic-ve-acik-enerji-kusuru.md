# ADR-0022: Gözenekli başlangıç durumu düzeltildi; P-α sıkışma enerjisi **açık kusur**

- **Durum:** Kısmen çözüldü — kalan kusur **FAZ 3 ENGELLEYİCİSİ**
- **Tarih:** 2026-07-29
- **Bağlam:** P2-FR-04, P2-VR-06; gerçek çarpma senaryosu
- **İlgili:** [ADR-0008](ADR-0008-porozite-enerji-muhasebesi.md), [ADR-0015](ADR-0015-sureklilik-yogunlugu.md), [ADR-0020](ADR-0020-enerji-hatasi-kesme-hatasidir.md)

## Nasıl bulundu

FAZ 3 öncesi ölçülmemiş tek şey **uzun koşu kararlılığı**ydı: tüm kapı
senaryoları birkaç yüz adım, gerçek bir DART koşusu ~10⁵ adım. Bunun için
tam fizikli (Tillotson + dayanım + gözeneklilik + öz-yerçekimi) bir çarpma
senaryosu kuruldu ve TRUBA'da uzun koşuya sokuldu.

İlk rapor beklenmedikti: **enerji hatası %44,8**. Ama adım sayısıyla
**birikmiyordu** (2000 adımda %44,815 → 4000 adımda %44,803), yani çarpma
anına ait tek seferlik bir kayıptı.

Modül ablasyonu kaynağı gösterdi:

| Kurulum | Enerji hatası |
|---|---|
| Tam fizik | %92,85 |
| **Gözeneklilik KAPALI** | **%0,56** |

## Bulgu 1 (ÇÖZÜLDÜ) — süreklilik + gözeneklilik tutarsız başlangıç kuruyordu

Süreklilik modunda başlangıç yoğunluğu `rho = rho0_katı` olarak
veriliyordu — **alpha0'dan bağımsız**. Oysa P-α modelinde
`P = P_katı(rho·alpha, u)/alpha` olduğundan gerilmesiz başlangıç
`rho·alpha = rho0_katı`, yani `rho = rho0_katı/alpha0` gerektirir.

Ölçülen başlangıç basıncı (durgun cisim, u=0):

| alpha0 | eski kod | düzeltilmiş |
|---|---|---|
| 1,0 | 0 Pa | 0 Pa |
| 1,5 | **1,335e10 Pa** | 0 Pa |
| 2,5 | **2,670e10 Pa** | 0 Pa |

13 GPa'lık hayali basınç, çarpmanın kendi şok basıncıyla kıyaslanabilir.

**Neden görülmedi:** *süreklilik + gözeneklilik* kombinasyonu hiçbir testte
koşulmuyordu — `test_solid_cross.py` gözenekliliği açıyor ama **toplama**
yoğunluğu kullanıyor; `test_taylor_bar.py` süreklilik kullanıyor ama
gözenekliliği **kapatıyor**. İki modül ayrı ayrı doğruydu; birlikte
kullanıldıklarında bozuluyorlardı.

**Düzeltme:** hem GPU çözücüsünde hem CPU referansında başlangıç yoğunluğu
`rho0/alpha` olarak kuruluyor. Çarpma senaryosunda enerji hatası
**%92,85 → %6,74**.

## Bulgu 2 (AÇIK KUSUR) — sıkışma enerjisi defterde yok

Düzeltmeden sonra kalan hata **çözünürlükle büyüyor**:

| nside | gözenekli | gözenekliksiz |
|---|---|---|
| 32 | %6,74 | %0,244 |
| 44 | **%15,81** | %0,264 |

Bu belirleyicidir. ADR-0020'de kurulan ayırt edici mantığın **tersi**:
kesme hatası ayrıklaştırma inceldikçe **küçülür**; burada **büyüyor**.
Gözenekliksiz durum ise çözünürlükten bağımsız ve sıkı (%0,24–0,26), yani
şemanın kendisi sağlamdır. Kusur gözenekliliğe özgüdür.

Mekanizma ölçüldü (nside=32, 150 adım):

```
E0    = +2.0503e13 J   (tamami kinetik)
E_son = +1.9121e13 J   (-%6.74)
  KE  : 2.0503e13 -> 1.9718e13
  U_ic:      0    -> -5.9733e11 J      <- NEGATIF ic enerji
alpha : 1.5 -> 1.0 (756 parcacik tamamen ezilmis)
```

Gözenek çökmesi malzemeyi **ısıtmalıdır**; ölçümde iç enerji **negatife**
düşüyor. Bu fiziksel değildir.

### Denenen ve REDDEDİLEN çözüm

Şartname §5.3 sözde-kodu sıkışma işini doğrudan `u`'ya ekler; ADR-0008 bunu
"PdV zaten kapsıyor, çifte sayım olur" gerekçesiyle bilinçli olarak
uygulamamıştı. Bu düzeltmenin işe yarayıp yaramadığı **ölçüldü**:

| Yaklaşım | Enerji hatası | u_min |
|---|---|---|
| ADR-0008 (iş eklenmez) | %1,88 | −9,97e3 |
| Şartname (iş `u`'ya eklenir) | **%20,33** | +8,24e3 |

İşi eklemek defteri **on kat kötüleştiriyor**. Yani ADR-0008'in çifte sayım
gerekçesi geçerlidir ve basit "sözde-kodu uygula" düzeltmesi **yanlıştır**.
Kusur başka bir yerdedir ve P-α termodinamiğinin tam gözden geçirilmesini
gerektirir.

## Karar

1. Başlangıç durumu düzeltmesi **uygulandı** ve testlerle sabitlendi.
2. Kalan kusur **açık** bırakıldı ve `pytest.mark.xfail(strict=True)` ile
   izleniyor (`tests/test_porous_continuity.py`). Böylece çözüldüğü an test
   "beklenmedik başarı" ile uyarır.
3. Eşikler **gevşetilmedi**, kusur gizlenmedi.
4. **FAZ 3'e gözenekli hedefle geçilmez.** Dimorphos bir moloz yığınıdır ve
   gözeneklilik çıkarımın **asıl parametresidir**; bu kusurla üretilecek her
   posterior yanlı olur.

## Neden bu kapılardan geçti?

G2 C3 gözenekliliği *nokta modeli* olarak sınıyor (crush curve monotonluğu,
geri genleşme yok, iş ≥ 0) ve SPH tarafında yalnızca **şok basıncı oranına**
bakıyor. G2 C5 enerji korunumunu soğuk çöküşte ölçüyor — o senaryoda
gözeneklilik **kapalı**. Yani gözenekliliğin dinamik bir koşudaki **enerji
davranışı** hiçbir ölçütte yoktu.

Ders, bu oturumun diğer bulgularıyla aynı: **iki modül ayrı ayrı doğru
olabilir ve birlikte bozuk olabilir.** Kapsama, modül başına değil
**kombinasyon başına** düşünülmelidir.

## Doğrulama

- `tests/test_porous_continuity.py::TestPorousContinuityInitialState` (5 test)
- `...::TestPorousImpactEnergyLedger::test_initial_state_regression_fixed`
- `...::test_nonporous_ledger_is_tight_and_resolution_stable`
- `...::test_porous_ledger_matches_solid_ledger` — **xfail(strict)**, hedef
  davranışı tarif eder
