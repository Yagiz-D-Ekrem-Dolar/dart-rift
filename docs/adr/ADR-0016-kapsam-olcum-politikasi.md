# ADR-0016: Kapsam ölçümü — Warp çekirdek gövdeleri hariç, tek `.coveragerc`

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-28
- **Bağlam:** P0-QR-04 (kapsam eşiği %85), G0 kapısı C1 ölçütü, CI
- **İlgili:** [ADR-0002](ADR-0002-hassasiyet-politikasi.md), [ADR-0005](ADR-0005-python-surumu-truba.md)

## Sorun

İki ayrı belirti aynı köke çıktı.

**1. CI birkaç koşudur kırmızıydı.** Düşen adım, G0 kapısının GPU'suz
ortamda "GEÇTİ" demediğini doğrulayan adımdı:

```
| C1 | Depo derleniyor; CI katmani yesil | KALDI | pytest cikis kodu=0;
      KAPSAM YETERSIZ: kapsam=81.6% (esik 85.0%) |
```

Kod doğruydu; kapı yine de kalıyordu.

**2. GPU'lu ölçümde oran %85,1 idi** — eşiğin (%85) 0,1 puan üstünde.
Bu kadar dar bir marj, kapsamın ölçtüğü şeyin anlamlı olmadığına işaretti.

## Kök neden

**coverage.py, Warp çekirdek gövdelerini ölçemez.** `@wp.kernel` ve
`@wp.func` ile bezenmiş fonksiyonlar Warp tarafından derlenir (CUDA'ya veya
CPU'da yerel koda); Python'un satır izleyicisi gövde satırlarını hiçbir zaman
görmez. Bu satırlar "eksik" sayılır.

Ölçüm dosyası üzerinde doğrudan gösterildi — `density_3d`, projenin **en çok
çalışan** çekirdeğidir (her SPH adımında çağrılır), yine de:

```
E  13| @wp.kernel          <- yalnizca dekorator "calisti" (import aninda)
E  14| def density_3d(
M  23|     i = wp.tid()     <- govdenin TAMAMI "eksik"
M  33|     rho[i] = acc
```

Yani `warp_core/` için raporlanan %17–65 arası oranlar, o dosyalardaki
çekirdek-dışı Python'un payından ibaretti. Toplam oran da bu yüzden eşiğin
etrafında tesadüfen salınıyordu.

Eski `.coveragerc-ci` bunu `warp_core/` dizinini tamamen dışlayarak
çözüyordu, ama iki kusuru vardı:

- Dizindeki **gerçek Python**'u da gizliyordu: `GridManager`, çözücü
  orkestrasyonu, zaman adımı hesabı — 657 satır, ölçüldüğünde %96,8 kapsamlı.
- Yalnızca `--cov-config` bayrağı **elle verildiğinde** devreye giriyordu.
  Kapı koşucusu bu bayrağı vermiyordu; CI'nın kırmızı kalmasının doğrudan
  nedeni buydu.

## Karar

Tek bir **`.coveragerc`** dosyası. Adı bilinçli seçildi: coverage.py'nin
varsayılan yapılandırma adıdır, dolayısıyla CI, kapı koşucuları ve yerel
`pytest` çağrıları için **bayraksız** uygulanır.

```ini
[report]
exclude_also =
    @wp\.kernel
    @wp\.func
```

Dekoratör satırı eşleştiğinde coverage.py fonksiyonun tamamını dışlar; bu
davranış ölçülerek doğrulandı (`density.py` 50 → 5 ifade, `solid_stress.py`
98 → 7, `hash_grid.py` 30'da kaldı — yani gerçek Python ölçülmeye devam
ediyor).

Üç seçeneğin karşılaştırması (aynı koşu verisi üzerinden):

| Seçenek | Kapsam | Ölçülen satır |
|---|---|---|
| Her şey dahil (eski kapı ölçümü) | %85,1 | 3214 — 412'si ölçülemeyen gövde |
| `warp_core/` tamamen hariç (eski `.coveragerc-ci`) | %97,8 | 2145 |
| **Yalnızca çekirdek gövdeleri hariç (seçilen)** | **%97,6** | **2802** |

Seçilen yöntem, dizini dışlayan yönteme göre **657 satır daha fazla** kod
ölçer ve ölçülemeyen hiçbir şeyi orana katmaz.

## GPU çekirdekleri nasıl doğrulanıyor?

Satır kapsamıyla değil — **CPU↔GPU çapraz kontrolleriyle**. Her çekirdeğin
Warp'tan bağımsız bir NumPy FP64 referansı vardır ve ikisi < 1e-8 sapmayla
eşleşir (`tests/test_sph_cross.py`, `tests/test_solid_cross.py`).

Bu ayrım önemli: satır kapsamı bir çekirdeğin *çalıştığını* gösterir,
*doğru olduğunu* değil. Çapraz kontrol ise yanlış ayrıklaştırmayı yakalar —
nitekim [ADR-0015](ADR-0015-sureklilik-yogunlugu.md), tam da bu kontrolün
yakaladığı gerçek bir çekirdek hatasını kaydeder. Satır kapsamı o hatayı
asla göremezdi: satırlar zaten çalışıyordu, sonuç yanlıştı.

Dolayısıyla eski `.coveragerc-ci` içindeki "Kapı → tüm kodun (GPU dahil)
≥ %85'i" ifadesi **yanlıştı** ve kaldırıldı. Ölçülemeyen bir şey için eşik
koymak, ölçüyormuş gibi görünmekten başka işe yaramıyordu.

## Sonuçlar

- (+) Kapsam oranı artık anlamlı: yalnızca Python'un gerçekten çalıştırdığı
  kod sayılıyor.
- (+) Tek dosya, bayrak yok — unutulamaz.
- (+) `warp_core/` içindeki gerçek Python görünür oldu (657 satır).
- (−) Çekirdek gövdeleri için satır kapsamı **yok**; bu bir eksiklik olarak
  kabul edilir ve çapraz kontrollerle karşılanır. Yeni bir çekirdek
  eklendiğinde, kapsam raporu uyarı vermeyeceği için **çapraz kontrolünün de
  yazıldığı elle doğrulanmalıdır**.
- (−) Eşik %85 (şartname P0-QR-04) artık gerçek orana (%97,6) göre çok
  gevşek. Eşik şartnameden geldiği için düşürülmedi/yükseltilmedi; gerçek
  oran her kapı raporunda ayrıca yazılıyor.

## Doğrulama

- CI: `pytest tests -m "not gpu" --cov=dartrift --cov-fail-under=85`
  (bayraksız; `.coveragerc` otomatik uygulanır).
- G0 kapısı C1 ölçütü, hem GPU'lu hem GPU'suz ortamda aynı yapılandırmayı
  kullanır; kanıt metni hangi ortamda ölçüldüğünü yazar.
