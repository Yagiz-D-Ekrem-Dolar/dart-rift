# Protokol M — üç çözünürlükte yakınsama pilotu

**Yazıldı:** 2026-09-13, **koşudan ÖNCE**. Tasarım, toleranslar ve yargı
kuralı `scripts/m_yakinsama_raporu.py`'de kilitli, sınavlarıyla
(`tests/test_m_yakinsama_raporu.py`) commit'lendi.

## 1. Neden

Bitiş 3'ün ikinci halkası **sayısal yakınsama**. Şimdiye kadar
yapılamadı: üçüncü seviye `224` saat istiyordu (A52). İş K (H200) ölçtü:
destek kutulu BVH orta merdivende `8,13×`; ince merdiven (`N = 487 358`)
nokta başına `~1–2 saat`e iniyor.

Uzman: *"Üçüncü nokta araya değil daha inceye"*, *"4–6 temsilî θ'da
eşleşmiş üç çözünürlük"*, *"bilimsel tolerans önceden seçilmeli;
sayısal farkın belirsizlik aralığı bu toleransın içine girmeli"*,
*"2 sigma altında yakınsama kanıtı değildir"*.

## 2. Tasarım

| | |
|---|---|
| θ (6) | `(1,15 ; 1e5 ; 0,275)`, `(1,15 ; 1e3 ; 0,275)`, `(1,15 ; 3e6 ; 0,275)`, `(1,05 ; 1e5 ; 0,10)`, `(1,25 ; 1e5 ; 0,45)`, `(1,15 ; 1e4 ; 0,45)` |
| tohum (2) | `20260906`, `99991111` (iç yapı gerçekleşmesi) |
| merdiven (3) | kaba (`s_min = 0,35`), orta (`0,175`), ince (`0,0875`) — oran 2 |
| çarpma sahası | **matris** (`3 m` küresinde blok yok) — L'nin ikili anahtarını dışarıda tutar |
| fizik | `--akma-kipi ara --matris-cekme-yok --blok-uretici v2 --malzeme-kaynagi geometri --blok-rmin 1.7 --blok-rmax 6.5 --mermi-h-kipi kendi --mermi-eos aluminyum --ilk-dt-duzelt --komsu-arama bvh` |
| süre | `t = 24 ms` |

**Neden `--mermi-h-kipi kendi` burada özellikle önemli:** mermi `h`'si
(`0,144 m`) üç merdivende **aynı** ve en küçük `h` ondan geliyor; bu
yüzden `Δt` üç çözünürlükte yaklaşık **eşit**. Uzamsal etki zamansal
etkiden (A72/A77) böylece ayrılıyor.

36 koşu, her biri ayrı görev.

## 3. Yargı

Her `(θ, gözlem)` için seviye başına iki tohum ortalaması `x` ve
ortalamanın sapması `σ = |a − b| / 2`. `richardson_raporu.py`:

- Farklar aynı işaretli değilse → `SALINIMLI ya da DUZ`;
- iki farktan biri `2σ` içindeyse → `GURULTU ICINDE`;
- `p ∉ [0,5 ; 4]` → `ASIMPTOTIK DEGIL`;
- aksi halde **tolerans kapısı**: `|x_f − x_*| + 2 σ_f ≤ δ · |x_f|` →
  `YAKINSAMIS`, değilse `YAKINSAMAMIS`.

Toleranslar (`δ`, ince değere göre bağıl):

| gözlem | tolerans |
|---|---|
| `d_merkez` | `0,10` |
| `R_krater` | `0,15` |
| `V_krater` | `0,20` |
| `beta_eksi_1` | `0,25` |
| `M_ejekta` | `0,30` |

Gerekçe (proje seçimi, evrensel değil): krater derinliği `Y₀` çıkarımının
ana taşıyıcısı → en sıkı; hacim ve ejekta nicelikleri ağır kuyruklu ve
az parçacıkla temsil ediliyor → gevşek.

Gözlem başına (6 θ üzerinden): `YAKINSAMIS` sayısı `≥ 4` →
**YAKINSIYOR**; `≤ 1` → **YAKINSAMIYOR**; arası → **KISMİ**.
`GURULTU ICINDE` ve `OKUNMAZ` ayrıca sayılır; YAKINSAMIŞ sayılmaz.

## 4. Yorum tablosu (koşudan önce)

| sonuç | anlamı |
|---|---|
| `d_merkez` ve `V_krater` YAKINSIYOR | krater gözlenebilirleri ince seviyede tolerans içinde → Bitiş 3 vekil modeli ince (ya da Richardson-düzeltilmiş) değerlerle kurulabilir |
| krater YAKINSIYOR, `β` KISMİ/YAKINSAMIYOR | `β` için dördüncü seviye ya da uzun zaman gerekli; çıkarım önce krater gözlemiyle |
| krater YAKINSAMIYOR | gözlenebilir ya da fizik çözünürlüğe duyarlı → dördüncü seviye seçilmiş θ'da; A69 açık kalır |
| çoğu `GURULTU ICINDE` | seviyeler arası fark gerçekleşme gürültüsünden küçük → daha çok tohum gerekir, yakınsama iddia edilmez |

## 5. Bilinen sınırlar

- İki tohum: `σ` kestirimi zayıf (serbestlik derecesi 1).
- `24 ms` anlık görüntü; zamanda plato Protokol T'de ayrıca bakılıyor.
- İdealleştirilmiş matris sahası; gerçek DRACO sahası değil.
- Merdivenin yalnız çarpma bölgesi incelir; uzak alan kaba kalır.

## 6. Maliyet

H200 + bvh: kaba `~6 dk`, orta `~11 dk`, ince `~1–2 sa` nokta başına
(`~16 bin` adım). Toplam `~20` GPU-saat.
