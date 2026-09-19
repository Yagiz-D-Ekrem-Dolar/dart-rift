# Protokol W2 ve UA sonuçları (2026-09-19)

TRUBA `egitimg16u3`, `/arf/scratch/egitimg16u3/driftclaude/kampanya/`.

| dosya | üreten | TRUBA SHA-256 (girintili kaynak) |
|---|---|---|
| `S_W2.json` | `scripts/w_kiyas_raporu.py --onek W2` (kod `a877269`) | `e2b072e7e96cab8b6f9250ac615f8553ecb7d049ebcd83d4dd014e2ffe0aba0e` |
| `S_UA.json` | `scripts/ua_uzak_alan_raporu.py` (kod `a877269`) | `87fa7c9d1b26d751f91867b2d111903dfaecc1efdca60ee479105a4ea7b40e21` |
| `S_W2_UA_beta_t_ozet.csv` | `S_W2_UA_beta_t.csv`'nin (8 koşu × 50 log-zaman satırı) seçili anlarda log-zaman aradeğeri | kaynak CSV: `ede77e04fdde4f8d60ba8324bc8e956a29063de423e48b54626c1db8baa471be` |

Bu dizindeki JSON'lar aynı içeriğin **sıkıştırılmış yazımıdır** (alanlar ve
değerler aynı). Özet CSV bir **tanıdır** (keşif), kilitli yargı değildir.

İşler: W2 `1567714_0 … _5` (hepsi `COMPLETED`, 2:05 – 3:58; kod `b7c27af`),
UA `1567770_0 … _1` (`COMPLETED`, 3:12 ve 6:50; kod `a877269`). İki commit
arasında `src` farkı **boş** (TRUBA'da `git diff --stat` ile doğrulandı).

Durum dosyaları (`nokta_0000_*.npz`) SHA-256:

| koşu | SHA-256 |
|---|---|
| W2_Y1_g0p2 | `a8f5f71eeec197453485785a1a123b214a4c6c3319d4986d3015d324399130cc` |
| W2_Y10_g0p2 | `77eddc7e24b910bf9c79a96b15dce3e7d166375dca8050454a0c927bf4e07a33` |
| W2_Y50_g0p2 | `beae0519258ced608c0bec478ac2a7936afd1815387d20a6f3deb9d6037d2be0` |
| W2_Y1_g1p0 | `78ec8279aa46314542f002cf626066108a51e8f0210115da214f40e024d80ab9` |
| W2_Y10_g1p0 | `8daa72709cd1175f5853a0a3e00aea080490abbd8eb120d2942c5acf7c9b232b` |
| W2_Y50_g1p0 | `8eec40dd448cea995f5f053129cda13bab6c4a7f0c375ef5669b3e2c29015447` |
| UA_s5p0 | `8a6fa75eb4a5faa7ad5fc8f69d7d3c25e651497e6556b985eccaf3a25773ab12` |
| UA_s3p5 | `d71926d49495d246fc980b2349bb8a03d25c70adca6359f5346c46e824d15aeb` |

Kilitli yargılar: **W2 `KIYAS TUTTU`** (kapsam TAM, 6/6 geçerli),
**UA `UZAK ALAN YAKINSAMIŞ`** (3/3 geçerli). Defter: KAYIT-067.
