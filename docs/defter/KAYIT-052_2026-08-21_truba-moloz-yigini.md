# KAYIT-052 — TRUBA sıfırdan kuruldu; moloz yığını rejimi de `β`'yı oynatmadı (2026-08-21)

**Kapsam:** A17 · TRUBA erişimi · ADR-0047
**Öncül:** [KAYIT-051](KAYIT-051_2026-08-21_beta-cozunurluk-artigi.md)
**Koşular:** TRUBA `kolyoz13` (H100), işler **`1515196`**, `1515233`

---

## 1. Çalışma alanı **yeniden kuruldu**

Eski alan (`/arf/scratch/egitimg16/driftclaude`, `egitimg16u4`)
erişilemez: MCP bağlantısı `egitimg16u1` olarak açılıyor ve
`u4` scratch'i `Permission denied` veriyor. Etrafından dolaşmak
yerine yenisi kuruldu:

| | |
|---|---|
| yol | `/arf/scratch/egitimg16u1/driftclaude` |
| depo | GitHub'dan klon (`main`) |
| ortam | `apps/truba-ai/gpu-2024.0` -> Python `3.10.15`, numpy `1.26.4` |
| warp | login node'da **internet var**; `pip --target=pylib` ile `1.15.0` |

Bir tuzak kaydediliyor: `pip` numpy `2.x`'i de kurmaya kalktı ve
**dosya kotasına** takılıp yarım bıraktı. Yarım `pylib/numpy`
silindi; modülün `1.26.4`'ü kullanılıyor ve `import` doğrulandı.
Yarım bırakılsaydı sessizce yanlış numpy'ı gölgeleyebilirdi.

---

## 2. Ortam sınavı — **birebir**

Ölçüt gereği kol B, ortam sınavı geçmeden koşmadı:

| | beklenen | ölçülen |
|---|---|---|
| `β` | `1,4112162721355217` | **aynı** |
| `A1` | `2,0390593305845943` | **aynı** |

Duvar `55 s`; aynı koşu yerel RTX 3050'de `14` dakika (`~15×`).

---

## 3. Kol B — gerçek moloz yığını rejimi

Geriye kalan tek fiziksel açıklama buydu: modelin hedefi moloz yığını
değil **kaya**. Rejim geçişi `Y0 ≈ 6,14 Pa`; model matrisi `1e4`
(geçişin `1 636` katı), **blokları `1e7 Pa`** (`1,6e6` katı) ve blok
mukavemeti FAZ 4 boyunca **hiç taranmamıştı**.

`--boulder-Y0` bayrağı eklendi (`_sahne_Y0` yalnızca matrisi
eziyordu). Kol: `matrix_Y0 = 1 Pa`, `boulder_Y0 = 1 Pa`, yerçekimi
**açık**, `t_end = 5 s`.

| | üretim | **B** |
|---|---|---|
| `β` | `1,411216272` | `1,411231044` |
| bağıl fark | — | **`1,05e-5`** |
| `n_ejekta` | `28` | `28` (mermi) |
| **kaçan hedef kütlesi** | `0` | **`0`** |
| `bekleyen` | `17` | **`0`** |
| momentum kapanışı | `1,31e-14` | `3,10e-13` |

Koruyucu ölçüt geçti: cisim **dağılmadı**. Yerçekimi açıkken dışarı
giden madde **daha da azaldı** (`17 -> 0`).

> Birincil dal düştü: *"kaçan hedef kütlesi `= 0` -> sebep parametre
> değil **mekanizma**."*

### Kendi ölçütümde kusur

`β` için *"`1,3 <= β < 2,0` -> kısmi"* bandını yazmıştım. **Kötü
eşikti:** taban değerin kendisi (`1,4112`) o bandın içinde, yani hiç
oynamayan bir sonuç *"kısmi"* okunurdu. Bandı sonradan
değiştirmiyorum; sonucu **oynamadı** diye okuyorum ve karar zaten
birincil ölçütte veriliyor.

---

## 4. Sırada: çözünürlük mü, mekanizma mı

Parametre tarafı kapandığı için kalan iki açıklamayı ayıran koşu
gönderildi (iş `1515233`, ölçüt `OLCUT-krater-cozunurlugu.md`,
koşudan önce): `λ₂ = 2 -> 4`, yani krater bölgesinde aralık
`3,5 -> 1,75 m`.

Karar `β`'ya **değil** hedef göstergelerine bağlandı (`bekleyen`,
`beta_bal`), çünkü `λ₂` büyüyünce `A1` de artıyor ve o `β`'yı
`1`'e doğru iter — yani `β` bu kolda karışık bir sinyal.

---

## 5. ADR-0047 **öneri olarak** yazıldı

Ölçüm tarafı kapandığı için karar belgeye taşındı: `β`'yı gözlenebilir
olmaktan çıkarmak (S3), krater bölgesini inceltmek (S1), model-form
değişikliği (S2), dış ölçekleme (S4). Eğilimim **S3**, ama S1'in
sonucu onu geri alabilir. **Karar kullanıcının.**

Ayrıca ADR-0047 kapı sonucunu da yazıyor: **`G4-B1` düşüyor** —
yakınsama `λ₂`'de ölçülmüştü, `λ₁`'de `268` kat eşik dışı.
