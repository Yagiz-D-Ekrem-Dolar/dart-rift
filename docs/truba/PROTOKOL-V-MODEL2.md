# Protokol V — ikinci model yeterliliği adımı (KOŞULLU)

**Yazıldı:** 2026-09-14, **U sonucundan ÖNCE**. Yalnız Protokol U'nun kilitli
genel yargısı **HİÇBİR VARYANT ULAŞMIYOR** olursa gönderilir; U'da en az bir
varyant banda ulaşırsa V **gönderilmez** ve bu belge "koşulmadı" diye kalır.
Yargı kuralı U ile **aynı** (`scripts/u_model_raporu.py --onek V`).

## 1. Neden

U, önsel ve malzeme parametrelerini (Y₀ < 1e3, μ_f, P-α, yığın yoğunluğu)
tarıyor. Hiçbiri `β`'yı gözlem bandına taşımazsa, eksik olan bir **fizik
bileşeni** ya da **süre**dir. Üretim modelinde üçü kapalı/kısa:

| bileşen | üretim | gerekçe |
|---|---|---|
| öz-yerçekimi | kapalı | ADR-0028 maliyet (`~15,7×`) |
| Grady-Kipp hasar | kapalı | FAZ 4 boyunca kapalı; `configs/p3_dimorphos.yaml` açık diyor (ADR-0027) |
| süre | 0,1 s | T: `β` platosu 0,1–0,2 s |

## 2. Tasarım

Merkez θ `(1,15 ; 1e5 ; 0,275)`, kaba, kesme + taban, matris sahası, iki tohum.

| varyant | değişiklik | `t_end` |
|---|---|---|
| V0 | yok (taban, U0 ile aynı) | 0,2 s |
| V1 | `--yercekimi` | 0,2 s |
| V2 | `--hasar` | 0,2 s |
| V3 | `--yercekimi --hasar` | 0,2 s |
| V4 | U'nun **en yakın** varyantı + `--yercekimi --hasar` | 0,2 s |

V4'ün ek bayrakları gönderim anında U raporundaki en küçük `|z|` satırından
alınır ve iş betiğine yazılır (kural önceden kilitli, değer U'dan).

## 3. Yargı

U §3 aynen: `|z| ≤ 2` BANDA ULAŞIYOR; genel **MODEL GÖZLEME ULAŞABİLİYOR** /
**HİÇBİR VARYANT ULAŞMIYOR**.

## 4. Yorum tablosu

| sonuç | anlamı |
|---|---|
| V1 / V3 ulaşıyor | yerçekimsiz model DART `β`'sını sistematik olarak düşük veriyor → üretime yerçekimi (maliyet ADR'si), N/P yeniden |
| V2 ulaşıyor | hasar modeli üretime alınmalı (ADR-0027 yeniden) |
| yalnız V4 | parametre + fizik birleşimi gerekiyor |
| hiçbiri | bu SPH ileri modeli (0,2 s) DART `β`'sını üretmiyor → Bitiş 3 sonucu **"model gözleme ulaşmıyor"** olarak yazılır; iç yapı çıkarımı gerçek veriyle yapılamaz |
