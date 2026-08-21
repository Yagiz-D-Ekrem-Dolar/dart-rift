# A17 — "gerçek moloz yığını" kolu (2026-08-21, koşudan **önce**)

## Neden bu kol

Ölçülenler (yerel, KAYIT-051): `β`'nın tamamı merminin sekmesi,
hedef payı **tam sıfır**, ve sekme çözünürlükle küçülüyor
(`λ₁ 19→38` ile `β 1,4112 → 1,1851`). Yani hedef **hiç ejekta
üretmiyor**.

Sebebi model parametrelerinde aranırsa şu çıkıyor: hedefin
mukavemeti gerçek Dimorphos'un rejiminde **değil**.

| | değer | `Y0/rho` / `GM/R` |
|---|---|---|
| yerçekimsel bağlanma `GM/R` | `3,394e-3 J/kg` | `1` |
| rejim geçişi | **`Y0 ≈ 6,14 Pa`** | `1` |
| modelin matrisi | `1e4 Pa` | **`1 636`** |
| modelin **blokları** | `1e7 Pa` | **`1,6e6`** |

Gerçek Dimorphos kohezyonu **~Pa** mertebesinde kestiriliyor. Model
hedefi bir moloz yığını değil **kaya**: çekmede sınırsız (hasar
kapalı), kesmede `1e4`–`1e7 Pa`, ve yerçekimi kapalı olduğu için
"kaçış" tanımsız.

Blok mukavemeti FAZ 4 boyunca **hiç taranmadı** (KAYIT-050).

## Koşulacak

| kol | ayar |
|---|---|
| **S** (duman) | üretim, `t_end = 0,2 s` — **ortam sınavı** |
| **B** | `matrix_Y0 = 1 Pa`, `boulder_Y0 = 1 Pa`, **yerçekimi AÇIK**, `t_end = 5 s` |

`λ₁ = 19`, `λ₂ = 2`, tohum ve geri kalan her şey aynı.

## Ölçüt — **veriye bakılmadan**

### 0. Ortam sınavı (S)

- `β = 1,411216 ± 1e-5` **ve** `A1 = 2,0391` -> yeni TRUBA ortamı
  yerel/eski koşularla karşılaştırılabilir.
- Tutmazsa **hiçbir şey okunmaz**; önce ortam düzeltilir.

### 1. Birincil (B) — hedef ejektası **var mı**

Bugüne kadar **her** koşuda kaçan hedef kütlesi tam `0`.

- kaçan hedef kütlesi `> 0` -> hedef ejektası mekanizması ilk kez
  çalışıyor; A17'nin sebebi **mukavemet rejimi**.
- `= 0` -> zayıf hedef de yetmiyor; sebep parametre değil
  **mekanizma** (model-form) ve bu bir ADR kararıdır.

### 2. `β` ne kadar hareket etti

- `β >= 2,0` -> gözleme (`3,2225`) doğru **anlamlı** hareket.
- `1,3 <= β < 2,0` -> kısmi.
- `β < 1,3` -> yok sayılır.

### 3. Koruyucu — cisim kendi kendine dağılmasın

`Y0 = 1 Pa`'da cisim yalnızca yerçekimiyle duruyor. Koşu **geçersiz**
sayılır eğer:

- momentum kapanışı `> 1e-10`, **veya**
- çarpma bölgesinden uzaktaki (`r > R/2`, mermi ekseninden `> 45 deg`)
  hedef parçacıklarının medyan hızı `> 0,082 m/s` (kaçış hızı) —
  yani cisim çarpmadan bağımsız olarak dağılıyor.

Bu koruyucu olmadan *"ejekta çıktı"* ile *"cisim patladı"* ayırt
edilemez ve `β` yapay biçimde büyür.
