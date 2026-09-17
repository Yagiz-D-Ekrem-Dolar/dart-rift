# KAYIT-064 — Protokol V da ulaşmadı: bu SPH modeli (0,2 s) DART'ın β'sını üretmiyor (2026-09-17)

**Kapsam:** Bitiş 3 yargısı · **Durum:** kilitli sonuç + yorum ·
**Kaynak:** `docs/olcumler/U_V_2026-09-17/` (`S_U.json`, `S_V.json`,
`S_V_karar.json`), [`PROTOKOL-V-MODEL2.md`](../truba/PROTOKOL-V-MODEL2.md) ·
**Öncül:** [KAYIT-057](KAYIT-057_2026-09-16_protokol-U-kampanyasi.md)

---

## 0. Nasıl gönderildi

U bitince `U_RAPOR` (`1565226`) kilitli U raporunu yazdı (HİÇBİR VARYANT
ULAŞMIYOR, kapsam TAM) → kilitli `v_gonderim_karari.py` `gonder = true`
(en yakın U6, `V4_EK = --yigin-yogunlugu 1500`, `V4_U = U6`) → sıralı gönderici
10 görevi gönderdi (`1565239_0 … 1565248_9`, 2026-09-17 00:20). Hepsi
`COMPLETED 0:0`; süreler 27–53 dk (yerçekimli koşular ~2 ×; 24 sa sınırının çok
altında).

## 1. Geçerlilik (10/10)

Her koşu `t = 0,200 s`, `gecerli = True`, enerji sapması `−%0,37 … −%0,45`;
`malzeme_ek` kayıtta doğru (V1 `yercekimi`, V2 `hasar`, V3–V4 ikisi).

**"Yerçekimi β'yı hiç değiştirmedi — açık mı?"** sınandı: V1'in enerji sapması
V0'dan farklı (`−0,00447` vs `−0,00370`), yani yerçekimi **etkin** ve çözücü
farklı koştu; β ise 4. ondalığa kadar aynı. Dimorphos'un yüzey çekimiyle
0,2 s'de hız değişimi `~1e-5 m/s` mertebesi — β'da görünmemesi beklenen
(KAYIT-049'da da "yerçekimi bit düzeyinde aynı β").

## 2. Kilitli yargı

| varyant | değişiklik (0,2 s) | sim β−1 | gözlem β−1 ± σ_β | z |
|---|---|---:|---|---:|
| V0 | taban | 0,9045 | 2,121 ± 0,341 | +3,57 |
| V1 | yerçekimi | 0,9045 | 2,121 ± 0,341 | +3,57 |
| V2 | hasar | 0,9047 | 2,121 ± 0,341 | +3,57 |
| V3 | yerçekimi + hasar | 0,9047 | 2,121 ± 0,341 | +3,57 |
| V4 | U6 (`ρ 1500`) + yerçekimi + hasar | 0,7621 | 1,600 ± 0,284 | +2,95 |

**GENEL: HİÇBİR VARYANT ULAŞMIYOR (en yakın V4:kaba, z = +2,9) · KAPSAM: TAM.**

PROTOKOL-V yorum tablosu (koşudan önce yazıldı), "hiçbiri" satırı:
> *bu SPH ileri modeli (0,2 s) DART `β`'sını üretmiyor → Bitiş 3 sonucu **"model
> gözleme ulaşmıyor"** olarak yazılır; iç yapı çıkarımı gerçek veriyle yapılamaz.*

## 3. U + V birlikte ne söylüyor

| soru | cevap | kanıt |
|---|---|---|
| parametre ayarı yetiyor mu | **hayır** — en büyük artış `+0,10` (Y₀ düşük); açık `~1,1` | U1–U5 |
| süre mi eksik | **0,2 s'ye kadar hayır** — `0,1 → 0,2 s` β−1 `0,946 → 0,904` (hafif düşüş) | U0 vs V0 |
| yerçekimi / hasar mı | **hayır** — etkileri `~1e-4` | V1–V3 |
| çözünürlük kapatır mı | **hayır, tersine** — orta daha düşük (`0,946 → 0,820`) | U0/U8 orta |
| en umutlu kol | kütle/yoğunluk: gözlenen β kütleyle ölçekleniyor, `z` en küçük (`+2,8`) ama yetmiyor | U6, U8, V4 |

Model tarafında en iyi durumda `β ≈ 2,05` (U1 kaba), gözlem `3,12 ± 0,34`.
Sayı olarak: hedeften kaçan eksenel momentum ~**2 kat** eksik; çözünürlük
arttıkça fark büyüyor.

## 4. Bundan sonrası için hipotezler (DOĞRULANMADI — yargı değil)

1. **Zaman ölçeği:** çok zayıf bir moloz yığınında krater büyümesi yerçekimi
   rejiminde saniyelerden dakikalara sürebilir; 0,2 s yalnız erken ejektayı
   kapsıyor olabilir. `0,1 → 0,2 s` düşüşü "plato" gibi okunuyor ama A60'taki
   "ölü plato" dersi akılda tutulmalı. Literatürle (DART ejekta/krater zaman
   ölçekleri) karşılaştırılıp ölçülmeli.
2. **Gözlenen β'nın girdileri:** kütle ölçülmedi (Hera ölçecek); iki-cisim
   arayüzü `3,12`, yayımlanmış tam analiz `~3,6` (teyit edilmeli) → açık daha da
   büyük olabilir.
3. **Model sınıfı:** granüler akış reolojisi, yüzey/blok geometrisi, mermi
   biçimi (gerçek uzay aracı), yakınsamayan çözünürlük.

## 5. Proje için anlamı

- Bitiş 3 **negatif dalda**: gerçek DART verisiyle iç yapı posterioru bu
  modelle kurulamaz. Sentetik çıkarım zinciri (Y₀ ve f çözülüyor, α_b çözülmüyor)
  ve bu teşhis ayrı ayrı sonuçlardır.
- Kalan Bitiş 3 işi: teşhis raporu, koşulsuz Hera öngörüsü, literatür
  karşılaştırması; asıl hedef için ayrı bir **model geliştirme fazı** gerekir.
- 30 koşu, en fazla ~20 GPU-saat (kaba 13–15 dk × 16, orta ~27 dk × 4,
  V 27–53 dk × 10).
