# Protokol W2 — kıyas sınamasının A92 düzeltmesiyle **tekrarı**

**Yazıldı:** 2026-09-18, **W2 koşusundan ÖNCE**. **Öncül:** PROTOKOL-W,
FAZ4-SIKINTI-RAPORU A92.

---

## 1. Neden tekrar

Protokol W'nin kilitli yargısı **OKUNMAZ** oldu (`S_W.json`): altı koşunun
altısı yalnız `momentum_defteri` denetiminden düştü (artık `2,2e-3 – 5,0e-3`,
eşik `1e-3`). Sebep **kodda** bulundu (A92): dondurulan parçacık etkileşimden
çıkarılmadığı için gövdeyi tek yönlü çekiyordu. Kanıt yalnız geçerlilik
alanları, enerji ve çekim itmesi kestiriminden geldi.

> **W'nin β değerlerine bu karar verilmeden ÖNCE bakılmadı.** Rapor her satırı
> `OKUNMAZ` yazdı; tanı betikleri `β` yazdırmadı. Yani tekrar kararı sonuca
> göre değil, **geçersizliğin sebebine** göre verildi.

W'nin yargısı **değişmez** ve kayıtta `OKUNMAZ` olarak kalır.

## 2. Ne aynı, ne farklı

| | W | W2 |
|---|---|---|
| kural (§5: bant `0,5–2,0`, eğilim, sağlamlık `≤ 0,20`) | **aynı** | **aynı** (`w_kiyas_raporu.py`, `--onek W2`) |
| sahne, malzeme, `A_geç`, `t_geçiş ∈ {0,2; 1,0}`, `Y₀ ∈ {50, 10, 1}` | — | **aynı** |
| `t_end` | 600 s (§3.2, W0'dan) | **aynı** (600 s; W0 hızı değişmedi) |
| kod | `f193083` / `df1c5a0` | A92 düzeltmeli commit (gönderimde `SABIT_COMMIT`) |
| çıktı öneki | `W_` | **`W2_`** (W'nin kanıtı üzerine yazılmaz) |
| geçerlilik (§4) | `gecerli = True` + defter | **aynı** |

Krater operatörünün düşmesi (A93) geçerliliğe girmez: W'nin gözlenebiliri
`β`'dır ve `npz` krater ölçümünden önce yazılıyor.

## 3. Ön koşul: duman koşusu (bilimsel sonuç değil)

W2'nin altı koşusu gönderilmeden önce **tek** kısa koşu:
`is_W2_duman.slurm` (`Y₀ = 10 Pa`, `t_geçiş = 0,2 s`, `t_end = 5 s`,
dondurma açık). Kabul:

- donmuş parçacık sayısı `≥ 1` (dondurma gerçekten çalışmış olmalı) **ve**
- `momentum_artik_bagil ≤ 1e-4` (eşiğin 10'da biri).

Tutmazsa W2 **gönderilmez**; artığın kalan kaynağı aranır. Duman koşusunun
`β`'sı yargıya girmez ve raporlanmaz.

## 4. Yorum

W §6'daki yorum tablosu aynen geçerlidir.
