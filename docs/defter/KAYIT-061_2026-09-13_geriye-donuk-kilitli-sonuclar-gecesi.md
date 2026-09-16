# KAYIT-061 — Kilitli sonuçlar gecesi: M yakınsamıyor, P2 kalibrasyon düştü, patlamalar düzeldi, kaba P-v4b İKİ EKSEN (2026-09-13)

**Kapsam:** Bitiş 3 · **Durum:** GERİYE DÖNÜK yazıldı (2026-09-16) ·
**Kaynak:** [`SONUC-M-N-P-J-T.md`](../SONUC-M-N-P-J-T.md) §1–§2d,
[`FAZ4-SIKINTI-RAPORU.md`](../FAZ4-SIKINTI-RAPORU.md) A80–A83; TRUBA `egitimg16u4`,
H200; sayılar aynen aktarıldı · **Öncül:** [KAYIT-060](KAYIT-060_2026-09-10_geriye-donuk-uzman-bulgulari-akma-yuzey-mermi.md)

---

## 0. Tek paragraf

Koşudan önce kilitlenen protokoller aynı gece okundu. **Zaman adımı yolu
gösterildi ve `ara` kipi kaldırdı (J1).** Mutlak gözlenebilirler **üç
çözünürlükte yakınsamıyor (M)**, ama `Y₀` **kontrastı** dayanıklı (M2). İlk
posterior **dış örneklemde kalibrasyonu kaybetti (P2, A82)**. İki ayrı patlama
mekanizması bulundu ve kilitli doğrulamayla üretime alındı (A80 dayanım
kesmesi, A83 yoğunluk tabanı). Sabaha karşı, üretim fiziğiyle kurulan 48 θ'lık
havuzda zaman örnekli vektör **`Y₀` ve `f`'yi kalibre biçimde çözdü**.

## 1. Kilitli yargılar

| protokol | yargı | sayı |
|---|---|---|
| **J1** | **Y1: ZAMAN ADIMI YOLU GÖSTERİLDİ** · **Y2: ARA KALDIRIYOR** | `son`: `Δ = −0,343` (`2,27σ`); `ara`: `0,04σ`; I'daki kaymanın `%25`'i `Δt`'den |
| J2 | OKUNMAZ | sigmoid geçersiz |
| I2 | DAYANIKLI (`ara` kipinde) | `kat 0,44` — yakınsama kanıtı değil |
| T blok | `β` platosu GEÇTİ | `β−1 = 0,0532`, 12 ms → 0,2 s sabit |
| T matris | KOŞULAMADI | iki tohum da patladı → A80 |
| **M** | **YAKINSAMIYOR** — 5/5 gözlenebilir (`YAKINSAMIŞ` 1/30) | t0 `β−1` kaba/orta/ince `0,743 / 0,642 / 0,459`; `V_krater 23,9 / 35,7 / 52,6 m³` — farklar inceldikçe büyüyor |
| L2o | ÜÇ EKSEN, `boulder_alpha0` OKUNMAZ | — |
| **N** (kaba, 23 θ) | **TEK EKSEN (`log10 Y₀`)** | `β−1` `F = 821`; `α_b`, `f` Bonferroni `0,00238`'i kıl payı kaçırıyor |
| P kapalı döngü | kuadratik TEK, GP ÜÇ EKSEN | GP kapsama95 yalnız `0,74` |
| **P2 dış örneklem** | **KALİBRASYON DÜŞTÜ** (iki yol) → **A82** | kuadratik `Y₀` kapsama68 `0,48 < 0,50`; GP `0,26` |

## 2. Keşif → yeni kilitli protokoller (aynı gece)

- **Kontrast, mutlak değerden kararlı** (M verisi): `β−1` `Y₀ 3e6 − 1e5`
  kontrastı `−0,242 / −0,237 / −0,215` iken mutlak `β−1` `%62` kayıyor → **M2**.
- **A82 tanısı**: sınama `z` sapması `1,04–1,55` (kalibre modelde ~1); en kötü
  noktalar `α_b ≈ 1,0`, `Y₀ ≈ 9e6` köşesi; korelasyon küçültmesi etkisiz.
  Havuz (N + N2, 47 θ): N **ÜÇ EKSEN GÖRÜNÜR** (24 θ güç yetersizmiş); P-v4
  kalibre ama genişlik `≥ 0,34` → kesmeli veri gelmeden **P-v4 (§4d)** ve
  zaman örnekli **P-v4b (§4e)** kilitlendi.

## 3. Patlamalar ve düzeltmeleri

| kayıt | mekanizma | tanı | düzeltme ve kilitli doğrulama |
|---|---|---|---|
| **A80** | buharlaşmış/genleşmiş madde tam dayanım taşıyor → `dt → 0` | parçacık `1339`: `v = 1722 m/s`, `u = 6,0e6 J/kg` (`u_iv 4,72e6`), `ρ 77 → 0,001` 175 adımda, `\|S\| = √(2/3)·Y₀` sabit; `PatlamaGozlemcisi` 25 adımda bir | `--dayanim-kesme` (`u ≥ u_iv` ya da `ρα/ρ₀ < 0,5` → `S = 0`); V1 **KARARLI 12/12**, V2 **FİZİĞİ DEĞİŞTİRİYOR** (`β−1` medyan `+4,8σ ≈ %1,7`) → üretimde; kesmesiz kampanyalar (M, N, N2, L2, L2o, Z) **betimleyici** |
| **A83** | kesme açıkken bile boşluğa dağılan gözenekli matrisin süreklilik yoğunluğu `0` → `divv ∝ 1/ρ` → `dt → 0` | Nk kaba 48 noktanın 5'i, hep yüksek `f` (`0,45–0,48`) + `α_b 1,02–1,08` köşesi (matris `α ≈ 2,2`) | `--yogunluk-tabani` (`ρ ≥ 0,01 ρ₀/α`); V1 12/12 + dolgu 6/6, **V2 NÖTR** (`60/60`, en büyük `1,09σ`) → üretimde. Kendi hatalarım: tanı sayacı yarım adımda sıfırlanıyordu (sınav yakaladı); dolgu aynı (θ, tohum)'u iki kez sayacaktı (rapor durduruldu, tekrar eleme eklendi) |

## 4. Kilitli: M2, Z ve kaba P-v4 / P-v4b

| protokol | yargı |
|---|---|
| **M2** | **H_Y DAYANIKLI** (`β−1` `Y₀ 1e6 − 3e4`: `−0,071 / −0,105 / −0,101`; `ln M_ej` `−0,021 / −0,278 / −0,244`), H_a ve H_f DAYANIKSIZ (işaret değiştiriyor). `V_krater`, `d_merkez` OKUNMAZ: ince `99991111`'de krater `nan` (sonradan **A86**) |
| Z | KISMİ — ince bölge 2 ×: kabada `β−1 +%12–13`, ortada `−%0,3…+%3,9`; M'nin orta → ince farkını açıklamıyor |

**Kaba P-v4 / P-v4b** (Nk + N2k + Nkd dolgusu, 96 koşu, 48 θ, θ-gruplu 4 kat):

| yol | `α_b` | `log Y₀` | `f` | genel |
|---|---|---|---|---|
| P-v4 GP | BİLGİ YOK | BİLGİ YOK | **0,31 ÇÖZÜLÜYOR** | TEK |
| **P-v4b kuadratik** (+ 8/16 ms) | BİLGİ YOK | **0,33 ÇÖZÜLÜYOR** | **0,32 ÇÖZÜLÜYOR** | **İKİ EKSEN** |
| P-v4b GP | **0,44 AŞIRI GÜVENLİ** | | | KALİBRASYON DÜŞTÜ |

§4e kuralıyla P-v4b girer: **kaba çözünürlükte, üretim fiziğiyle, zaman
örnekli vektörle posterior dış doğrulamada kalibre, `Y₀` ve `f` çözülüyor,
`α_b` çözülmüyor** (`%95` kapsama `0,82 / 0,96 / 0,96`). Sınırlar kayıtlı:
kaba çözünürlük, `Y₀` genişliği `0,334` eşiğin hemen altında, sentetik gözlem.

## 5. Açık kalanlar (o gece)

- **A81**: orta merdivende iki θ'da `d_merkez` yarıya düşüyor; tanı: orta
  merdivende yüzey profili azimutta `0,54–0,85 m` gürültülü → `d_merkez` tek
  başına gözlenebilir olarak kullanılmamalı.
- **A82**: kalibrasyon (P-v4/P-v4b ile yol açıldı).
- `f`'nin çözünürlüğe dayanıklılığı (M2 H_f DAYANIKSIZ) → orta P-v4b ertesi gün.
