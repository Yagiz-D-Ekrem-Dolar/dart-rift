# ÖLÇÜT — A24 çaresi işliyor mu? (koşudan **önce** yazıldı)

**Tarih:** 2026-08-29 · **Öncül:** rapor A24 · **Kol:** `--rho-tasima-yok`

---

## 1. Soru

A24 kök sebebi **kodda** buldu: aktarım `u`'yu taşıyıp `ρ`'yu
`ρ₀/α₀`'a sıfırlıyordu. Çare yazıldı (hacim korunumlu aktarım) ve
birim testlerle kilitlendi. Ama birim testi *"fonksiyon doğru
ortalamayı hesaplıyor"* der; **koşuda şokun aktarımdan sağ çıktığını**
söylemez.

## 2. Düzenek — tek değişken

| | |
|---|---|
| ortak | `λ₁ = 19`, `r_ince1 = 3`, `λ₂ = 8`, `t_end = 6e-3 s` |
| **A kolu** | varsayılan (`ρ` **taşınıyor**) |
| **B kolu** | `--rho-tasima-yok` (A24 öncesi davranış) |

`t_end` bilerek `t₁ = 4,767e-3`'ün hemen ötesinde: ölçülen şey
aktarımın **kendisi**, sonraki evrim değil.

Aşama-1'in ürettiği bilinen: `%26` sıkışma, `73 t`, `r < 3,4 m`.
Aşama-2 `s = 0,875 m` olduğu için şoklanmış `82 m³` orada `~174`
parçacığa düşüyor — kabalaşma **kaçınılmaz**, soru onun **sıfır**
olup olmadığı.

## 3. Yargı (kilitli)

**Çare işliyor** ⟺ `A_max ≥ 5 × B_max` **ve** `A_max ≥ %5`.

**Çare işlemiyor** ⟺ `A_max < 2 × B_max` (aktarım hâlâ yutuyor).

Arada kalırsa: kısmi — kabalaştırma sıkışmayı seyreltiyor demektir ve
`λ₂` de yükseltilmelidir; bu **ayrı** bir karar olur.

## 4. Ek defter

`hacim_hatasi` (`< 1e-12` beklenir), `rho_max`, `rho_tasindi` sonuç
dosyasında görünmeli. `rho_tasindi = false` gelen bir A kolu, çarenin
**bağlanmadığı** anlamına gelir ve sonucu geçersiz kılar.

## 5. Ne **ölçmüyor**

`β`, krater. `t = 6e-3 s`'de kazı akışı başlamamıştır. Bu ölçüt
yalnızca **aktarımın şoku geçirip geçirmediğini** sorar.
