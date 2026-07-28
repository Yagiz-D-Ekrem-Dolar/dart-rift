```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 010
============================================================

**Tarih**       : 28.07.2026
**Saat**        : 02:00 – 06:30 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Çevrim içi — yerel makine (RTX 3050)

## BUGÜNKÜ HEDEF

Karmaşıklık ve hız denetimi: "10 saniyede bitmesi gerekirken 1 saat süren"
yerleri bulmak. Ölçmeden hiçbir şeye dokunmamak.

## BULGU 1 — Barnes-Hut, hızlandırdığı yöntemden 27 kat yavaştı

Yerçekimi ölçekleme taraması, n=4000 için aynı alanı üç yolla hesapladı:

| Yöntem | Süre |
|---|---|
| Doğrudan O(N²) toplam | 0,566 s |
| Ağaç kurulumu | 0,021 s |
| **Barnes-Hut gezinmesi** | **15,044 s** |

Barnes-Hut'ın tek varlık nedeni doğrudan toplamdan hızlı olmaktır. Ölçekleme
doğruydu (~O(N log N)) — sorun sabit çarpandı ve o kadar büyüktü ki BH ancak
**~290 000 parçacık** üzerinde doğrudan toplamı geçiyordu.

Profil kesin söyledi: 18,1 s'nin tamamı `bh_accel`'in kendi `tottime`ında,
alt çağrı yok. Yani saf yorumlayıcı yükü. Sebep, gezinmenin 3 elemanlık NumPy
dizileriyle yapılmasıydı: `tree.com[node] - p`, `d @ d`, `np.sqrt(dist2)`.
Her düğüm ziyareti birkaç kayan nokta işlemi için ~4 µs dispatch/ayırma
maliyeti ödetiyordu. n=4000'de ~4M ziyaret × 4 µs ≈ 16 s — ölçülenle birebir.

Gezinme skaler Python `float` aritmetiğine çevrildi (diziler bir kez
`.tolist()`, `math.sqrt`, ara vektör ayırma yok). Gezinme ve toplama sırası
aynen korundu.

| n | eski | yeni | hızlanma |
|---|---|---|---|
| 1 000 | 2,748 s | 0,194 s | 14,1× |
| 4 000 | 14,272 s | 1,266 s | 11,3× |
| 8 000 | 39,606 s | 4,031 s | 9,8× |

Kesişim noktası ~290 000 → **~15 000** parçacık.

Sayısal etki ölçüldü: sapma 5,0e-16 (~1 ULP), bit-eşit **değil** — NumPy'nin
`d @ d` çarpımıyla açık `dx*dx+dy*dy+dz*dz` ifadesinin ilişkilendirmesi farklı
olabiliyor. Tüm toleransların çok altında ve koşudan koşuya deterministik.

## BULGU 2 — `einsum` çağrılarının yarısı BLAS yoluna düşmüyordu

Elastik dalga profilinde zamanın **%69'u** `c_einsum`'daydı. NumPy'de
`np.einsum` varsayılan olarak `optimize=False`.

Ama körlemesine `optimize=True` eklemek **yanlış olurdu**. 15 imzanın tamamı
ölçüldü (N=700) ve sonuç ikiye ayrıldı:

| İmza | oran | karar |
|---|---|---|
| `nab,njb->nja` | 6,5× | uygula |
| `j,nja,njb->nab` | 2,9× | uygula |
| `jab,njb->nja` | 2,8× | uygula |
| `nj,njb->nb` | 2,4× | uygula |
| `j,jab,njb->na` | 1,9× | uygula |
| `j,nja->na` | **0,7×** | dokunma |
| `nj,nja,nja->n` | **0,6×** | dokunma |
| `nja,nja->nj` | **0,4×** | dokunma |

Üçü `optimize=True` ile 1,5–2,5 kat **yavaşlıyor**. Yalnızca kazandığı ölçülen
7 çağrıya eklendi ve koda gerekçe yazıldı — biri "tutarlılık olsun" diye
hepsine eklerse testler yavaşlar ama hiçbir uyarı çıkmaz.

Elastik dalga: res=300 26,1 → 14,0 s; res=400 66,5 → 38,2 s. Hata değerleri
dört ondalık basamağa kadar aynı (%5,4898 / %4,3185).

## BULGU 3 — Hiç kullanılmayan (N,N) dizisi

`evaluate_solid`, `w = kernel_w(q, h, dim)` dizisini **koşulsuz**
hesaplıyordu; oysa yalnızca summation yoğunluğunda ve yapay gerilmede
gerekiyor. Süreklilik modunda tamamen boşaydı. Üstelik yapay gerilme bloğu
aynı ifadeyi **ikinci kez** hesaplıyordu. Tembel hesaplama + paylaşım
eklendi.

## ÖLÇÜLDÜ, VAZGEÇİLDİ — GPU hash-grid yeniden kurulumu

`step()` içinde `_eval()` iki kez çağrılıyor ve ikincisinde konumlar
değişmemiş oluyor (aradaki tek işlem bir hız tekmesi), yine de
`gridman.build()` çalışıyor. Mantıken gereksiz.

Ölçünce: grid kurulumu eval maliyetinin **binde beşi** (nx=9, N=6348:
0,15 ms / 31,15 ms). Bunu atlamak için "x değişti mi" durumu taşımak %0,5 için
kalıcı karmaşıklık ve yeni bir hata yüzeyi demekti. **Dokunulmadı**, ama
kayda geçirildi ki aynı hipotez tekrar araştırılmasın.

Taylor koşusunun yerel yavaşlığı da algoritmik değil: RTX 3050'de FP64 hızı
FP32'nin 1/32'si. Kapı kanıtları zaten H100'de üretiliyor.

## SONUÇ

| | önce | sonra |
|---|---|---|
| Yerçekimi test grubu (14 test) | 297 s | 97 s |
| Elastik dalga res=400 | 66,5 s | 38,2 s |
| **Tam test paketi (374 test)** | **27:28** | **19:25** |

## DEĞERLENDİRME

Üç bulgunun ortak noktası: **maliyetin yapılan işle ilgisi yoktu.** Barnes-Hut
birkaç çarpma için mikrosaniyelerce dispatch yükü ödüyordu; einsum kasılmaları
BLAS yerine naif döngüdeydi; bir dizi hiç okunmadan üretiliyordu. Hiçbiri
"algoritma yanlış" değildi — hepsi "doğru algoritma yanlış maliyetle" idi.

Bir de tersi: en makul görünen optimizasyon fikri (gereksiz grid kurulumunu
atlamak) ölçülünce binde beş çıktı. Ölçmeden yapılsaydı, karmaşıklık karşılığı
hiçbir şey kazanılmayacaktı.

## SIRADA

- `solid_ref`'te yoğun N×N çift matrisi: 1B'de ~80× israf var (her parçacığın
  ~9 komşusu varken 720 çift hesaplanıyor). Kazanç büyük ama referansın en
  kolay denetlenen özelliğini bozar; ayrı bir karar olarak açık.
