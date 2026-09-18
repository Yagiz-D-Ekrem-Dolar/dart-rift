# KAYIT-066 — Protokol W: OKUNMAZ; sebep benim dondurma hatam (A92); W2 hazırlandı (2026-09-18)

**Kapsam:** kıyas sınaması · **Durum:** W kilitli sonuç (OKUNMAZ) + düzeltme +
tekrar protokolü · **Kaynak:** `docs/olcumler/W_2026-09-18/`,
[PROTOKOL-W](../truba/PROTOKOL-W-KIYAS.md), [PROTOKOL-W2](../truba/PROTOKOL-W2-KIYAS-TEKRAR.md),
FAZ4-SIKINTI-RAPORU A91–A93 · **Öncül:** [KAYIT-065](KAYIT-065_2026-09-17_literatur-paketi-ve-protokol-W.md)

---

## 1. Koşular

W0 zamanlama (`1566860`, 30:27): geçişte `dt` **219×** büyüdü (`4,19e-6 →
9,17e-4 s`), adım maliyeti `0,037 s`; `w_sure_karari.py` kuralı `t_end = 600 s`
seçti (koşu başı `~7,2` GPU-saat, 6 koşu `~43`).

W (`1566866_0…5`): altısı `COMPLETED 0:0`, süreler 1:58 – 4:10 (geçiş anı
1,0 s olanlar ~2 kat uzun). Bir koşuda (`Y50/g1,0`) krater operatörü düştü
(A93) — `npz` krater ölçümünden önce yazıldığı için durum korundu.

## 2. Kilitli yargı: **OKUNMAZ**

Rapor ilk denemede **A91** ile çöktü (desen dizin adındaki noktayı sayıya
katıyordu; hiçbir `β` okunmadan). Düzeltmeden sonra: altı koşunun **altısı**
`gecerli = False`, genel **OKUNMAZ**.

| denetim | sonuç |
|---|---|
| sonlu, tamamlandı, `ρ > 0`, kurucu sınır | geçti (6/6) |
| enerji | geçti: sapma `−%0,88 … −%0,91` (eşik %5) |
| **momentum defteri** | **düştü**: artık `2,2e-3 – 5,0e-3` (eşik `1e-3`) |

## 3. Sebep (A92) — β'ya bakılmadan bulundu

Dondurma parçacığın hareketini durduruyordu ama **etkileşimden çıkarmıyordu**.
Uzakta duran ejekta kütlesi (`7–13 × 10⁶ kg`, `r ≈ 230 m`) gövdeyi çekmeye
devam etti; tepkisi yoktu.

| koşu | defter artığı (ê) | çekim itmesi üst kestirimi (ê) |
|---|---|---|
| Y10 / 0,2 | +3,6e-3 | −4,7e-3 |
| Y10 / 1,0 | +5,0e-3 | −5,4e-3 |
| Y1 / 0,2 | +2,7e-3 | −4,9e-3 |
| Y1 / 1,0 | +2,2e-3 | −6,4e-3 |
| Y50 / 0,2 | +3,8e-3 | −3,5e-3 |
| Y50 / 1,0 | +3,5e-3 | −3,6e-3 |

İşaret tutarlı (gövde ejektaya çekiliyor → artık pozitif), büyüklük aynı
mertebe. **Düzeltme:** ayrı etkileşim kütlesi; donmuş parçacığınki `0`.
CPU sınavında dondurmayla toplam momentum `< 1e-10` bağıl korunuyor.

## 4. Dürüst değerlendirme

- Hata **benim**: dondurmayı yazarken yalnız hareketi düşündüm, etkileşimi
  değil. Sınavlarım yerçekimsiz kafeste olduğu için görmedi. Kilitli defter
  denetimi yakaladı — kuralın işe yaradığının kanıtı.
- Bedel: W'nin ~43 GPU-saati **yargı üretmedi**. Ama W bize üç şey verdi:
  geç evre şeması 600 s boyunca kararlı (6/6 sonlu, enerji `%0,9`), maliyet
  kestirimi doğru çıktı ve dondurma kusuru bulundu.
- W'nin `β` değerleri **okunmadı**; W2 kararı onlara bakılmadan verildi.

## 5. Sıradaki

1. **W2 duman** (`1567704`, 5 s): kabul `donmuş ≥ 1` ve `artık ≤ 1e-4`.
2. Tutarsa **W2** (6 koşu, `ONEK=W2`, `T_END=600`), aynı kilitli kural.
3. Tutmazsa W2 gönderilmez; artığın kalan kaynağı aranır.

## 6. Ek (2026-09-18 15:15): duman geçti, W2 gönderildi

**W2 duman** `1567704` (kolyoz33, 32:45, `COMPLETED 0:0`), kod `9ab7b36`
(A92 düzeltmeli). `scripts/w2_duman_kontrol.py` (β yazdırmaz):

| | değer | ölçüt |
|---|---|---|
| donmuş parçacık | **326** | `≥ 1` |
| momentum defteri artığı | **5,7 × 10⁻¹⁵** | `≤ 1e-4` |
| geçerlilik denetimleri | 6/6 `True` | — |

A92'den önce aynı tür koşuda artık `2,2e-4` (2 s) ve `2–5e-3` (600 s) idi; şimdi
**makine hassasiyeti**. Etkileşim kütlesi ayrımı momentumu tam koruyor.

**W2 gönderildi:** iş `1567714_0…5`, `T_END=600`, `ONEK=W2`, kod `b7c27af`
(duman sonrası eklenenler yalnız tanı/çıkarım: A94 plastik iş tanısı, gerinim
yumuşaması **kapalı**, çok doğruluklu vekil, koni kenar açısı — momentuma ve
W kuralına dokunmuyor). Altı görev hemen başladı (kolyoz33/37/38).

