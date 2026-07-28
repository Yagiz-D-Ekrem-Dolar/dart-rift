# G0 + G1 + G2 — güncel kod üzerinde kanıt (commit `9ffe342`)

Bu dosya, üç kapının **aynı commit** üzerinde arka arkaya koşulduğu kapanış
kanıtıdır. Önceki kanıt raporları (`G0_..._1425656`, `G1_..._1426162`,
`G2_..._1426596`) kendi koşularının doğru kaydıdır ama daha eski commit'lere
aittir; bu koşu, o tarihten sonraki tüm düzeltme ve optimizasyonları içerir.

## Künye

| | |
|---|---|
| Depo commit | **`9ffe342`**, temiz git ağacı |
| SLURM işleri | G0: **1427564** · G1+G2: **1427565** |
| Düğüm | `kolyoz23` (NVIDIA H100 80GB HBM3) |
| Sistem | Linux 5.14.0-427.13.1.el9_4, glibc 2.34 |
| Ortam | Python 3.10.15, NumPy 1.26.4, warp 1.15.0, CUDA Toolkit 12.9 |
| pytest | **376 geçti / 0 kaldı** (16:44) |
| Kapsam | **%97,6** (eşik %85; tüm paket, GPU dahil) |
| Kırmızı takım (§12) | 6/6 temiz |
| Çıkış kodları | G0: 0 · G1: 0 · G2: 0 |

## Sonuçlar

| Kapı | Sonuç | Karar |
|---|---|---|
| **G0** — Zemin sağlam | **GEÇTİ** 8/8 | FAZ 1 başlayabilir |
| **G1** — Şok motoru çalışıyor | **GEÇTİ** 8/8 | FAZ 2 başlayabilir |
| **G2** — Gerçek malzeme fiziği | **GEÇTİ** 7/7 | **FAZ 3 başlayabilir** |

## G1 — bu koşuda eklenen iki kanıt

**C3 (enerji korunumu):**

```
maks enerji goreli hatasi 0.432%;
dt yarilaninca hata/2.45 (~2 = birinci mertebe KESME hatasi, sizinti DEGIL)
```

Bu oran ADR-0020 ile eklendi. Ölçüt artık "hata < %0,5"ten keskindir: gerçek
bir sızıntı girerse oran 2'den 1'e düşer ve eşik hâlâ geçiliyor olsa bile
kanıt metninde görünür.

**C5 (Sedov):**

```
n=64^3: r=0.2387 vs 0.2499 (4.46%);
KE/E=0.182 (sonlu enjeksiyonda ~0.19 beklenir; nokta patlamasi 0.28)
```

ADR-0011 §4 bu göstergenin raporlanacağını söylüyordu ama iki faz boyunca
raporlanmıyordu; denetimde yakalandı ve eklendi.

## G2 — bu koşuda değişen iki sayı

| Ölçüt | Önceki kanıt (1426596) | Bu koşu | Neden |
|---|---|---|---|
| Elastik dalga | %2,96 | **%2,83** | ADR-0019: gradyan düzeltmesi 1B'de hiç uygulanmıyordu |
| Kabuk hatası | %4,65 | **%1,90** | ADR-0017: metrik örnekleme gürültüsü ölçüyordu |

Her ikisi de **eşik değişikliği değildir**; eşikler (%3 ve %5) aynı kaldı.
Değişen şey, ölçünün neyi ölçtüğü ve düzeltmenin gerçekten uygulanmasıdır.

## Kapsam sınırı

Kapılar motorun **doğrulama senaryolarını** geçtiğini gösterir. Dimorphos
hakkında hiçbir bilimsel sonuç iddia edilmemektedir; çarpma koşuları
FAZ 3'tedir.

> Görsel olarak makul bir krater kanıt DEĞİLDİR; kanıt test ve sayıdır.
