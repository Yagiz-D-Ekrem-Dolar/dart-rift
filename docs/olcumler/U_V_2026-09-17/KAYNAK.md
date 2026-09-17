# Protokol U ve V sonuç dosyaları (2026-09-17)

Kaynak: TRUBA `egitimg16u3`, `/arf/scratch/egitimg16u3/driftclaude/kampanya/`.
Kod: `24e513e343cdbccf240a73258cb3909b0fb41340` (`SABIT_COMMIT`).

| dosya | üreten | TRUBA SHA-256 |
|---|---|---|
| `S_U.json` | `U_RAPOR` işi `1565226` → `u_model_raporu.py` (kilitli) | `d67951a387ba7159ec7275159b37702801a8d98c54f56b7403417e16745eaf3f` |
| `S_V_karar.json` | aynı iş → `v_gonderim_karari.py` (kilitli) | `04f9d02319fcb0c04e3aa8368b1c14493973dcdd7762f3b7cfeb7a3dc2f6dbaf` |
| `S_V.json` | giriş düğümünde `u_model_raporu.py --onek V` (kilitli kural, 2026-09-17) | `2cd13beb7b0dc4f246cc1b671edc8676843183ef9091f570be4fd5ab7727a5aa` |

İş kimlikleri: U `1565205_0 … 1565220_15` (kaba), `1565222_16 … 1565225_19` (orta);
V `1565239_0 … 1565248_9` (U_RAPOR tarafından otomatik gönderildi). Hepsi
`COMPLETED 0:0`. Geçerlilik denetimi: U 20/20, V 10/10 `gecerli = True`.
Defter: KAYIT-057 (U), KAYIT-064 (V ve Bitiş 3 yargısı).
