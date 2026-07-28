# ADR-0018: CPU referansında performans — skaler ağaç gezinmesi ve seçici `einsum` optimizasyonu

- **Durum:** Kabul edildi
- **Tarih:** 2026-07-28
- **Bağlam:** `cpu_reference/gravity_ref.py`, `cpu_reference/solid_ref.py`
- **İlgili:** [ADR-0002](ADR-0002-hassasiyet-politikasi.md), [ADR-0009](ADR-0009-kernel-gradyan-duzeltmesi.md)

## Bağlam

CPU referansının işi **doğruluk**tur, hız değil: Warp'tan bağımsız, okunabilir
ve denetlenebilir olması gerekir. Bu ADR o ilkeyi değiştirmez. Ancak referans
yalnızca küçük-N çapraz kontrollerinde değil, **kapı senaryolarında** da
kullanılıyor (elastik dalga, rijit dönme, düzgün küre alanı), ve orada N
birkaç bine çıkıyor. Ölçüldüğünde iki yerde maliyetin işle ilgisi olmadığı
görüldü.

## Bulgu 1 — Barnes-Hut gezinmesi, hızlandırdığı yöntemden 27 kat yavaştı

`bh_accel` ağaç gezinmesi, 3 elemanlık NumPy dizileri üzerinde çalışıyordu:
`tree.com[node] - p`, `d @ d`, `np.sqrt(dist2)`. Her düğüm ziyareti birkaç
kayan nokta işlemi için ~4 µs NumPy dispatch/ayırma yükü ödetiyordu.

n = 4000, aynı alan:

| Yöntem | Süre |
|---|---|
| Doğrudan O(N²) toplam | 0,566 s |
| Ağaç kurulumu | 0,021 s |
| **Barnes-Hut gezinmesi** | **15,044 s** |

Barnes-Hut'ın varlık nedeni doğrudan toplamdan hızlı olmaktır. Ölçekleme
doğruydu (~O(N log N) — n^1,0…1,5), sorun sabit çarpandı: **Barnes-Hut ancak
~290 000 parçacık üzerinde doğrudan toplamı geçiyordu.**

### Karar

Gezinme skaler Python `float` aritmetiğiyle yapılır: ağaç dizileri bir kez
`.tolist()` ile Python listelerine çevrilir, `math.sqrt` kullanılır, ara
3-vektörler için dizi ayrılmaz. Gezinme sırası ve toplama sırası **aynen**
korunur.

| n | eski | yeni | hızlanma | doğrudan |
|---|---|---|---|---|
| 1 000 | 2,748 s | 0,194 s | 14,1× | 0,042 s |
| 2 000 | 7,434 s | 0,530 s | 14,0× | 0,145 s |
| 4 000 | 14,272 s | 1,266 s | 11,3× | 0,549 s |
| 8 000 | 39,606 s | 4,031 s | 9,8× | 2,411 s |

Kesişim noktası ~290 000 → **~15 000 parçacık**.

**Sayısal etki:** sapma 5,0e-16 (~1 ULP). Bit-eşit **değildir**, çünkü
NumPy'nin `d @ d` nokta çarpımı ile açık `dx*dx+dy*dy+dz*dz` ifadesinin
ilişkilendirmesi farklı olabiliyor. Sapma tüm toleransların çok altında
(çapraz kontrol 1e-8, `theta=0` özdeşlik testi 1e-10) ve koşudan koşuya
deterministiktir — ADR-0002'nin gerektirdiği şey budur; bitwise
değişmezlik önceki sürüme karşı değil, **aynı sürümün tekrarlarına** karşı
istenir.

## Bulgu 2 — `einsum` çağrılarının bir kısmı BLAS yoluna düşmüyordu

Elastik dalga profilinde zamanın **%69'u** `c_einsum`'daydı. NumPy'de
`np.einsum` varsayılan olarak `optimize=False`, yani çok-operandlı
kasılmalarda naif C döngüsü kullanılır.

Ancak `optimize=True` **her yerde kazanç değildir**. `solid_ref`'teki 15
imzanın tamamı ölçüldü (N=700):

| İmza | naif | optimize | oran |
|---|---|---|---|
| `nab,njb->nja` | 0,0254 s | 0,0039 s | **6,5×** |
| `j,nja,njb->nab` | 0,0165 s | 0,0058 s | 2,9× |
| `jab,njb->nja` | 0,0256 s | 0,0090 s | 2,8× |
| `nj,njb->nb` | 0,0014 s | 0,0006 s | 2,4× |
| `j,jab,njb->na` | 0,0240 s | 0,0127 s | 1,9× |
| `nj,nja,nja->n` | 0,0037 s | 0,0057 s | **0,6×** |
| `nja,nja->nj` | 0,0020 s | 0,0049 s | **0,4×** |
| `j,nja->na` | 0,0018 s | 0,0028 s | 0,7× |

### Karar

`optimize=True` **yalnızca kazandığı ölçülen çağrılara** eklenir (7 çağrı).
Kalan 8 çağrıya dokunulmaz; eklenirse 1,5–2,5 kat yavaşlarlar.

Koda bu gerekçe yazıldı ki biri "tutarlılık olsun" diye hepsine eklemesin —
bu, testleri yavaşlatan ama hiçbir uyarı üretmeyen bir değişiklik olurdu.

**Sayısal etki:** kasılma sırası değiştiği için sonuçlar ~1e-15 kayar.
Ölçülen doğrulama değerleri değişmedi (elastik dalga hatası %5,4898 ve
%4,3185 — dört ondalık basamağa kadar aynı) ve CPU↔GPU çapraz kontrolleri
1e-8 toleransıyla geçmeye devam ediyor.

## Bulgu 3 — `W(q)` hiç kullanılmadan hesaplanıyor, bir kez de tekrar ediliyordu

`evaluate_solid` içinde `w = kernel_w(q, h, dim)` **koşulsuz** hesaplanıyordu,
oysa yalnızca iki yerde gerekir: summation yoğunluğu ve yapay gerilme. Yani
`density_method="continuity"` modunda (N,N) boyutunda pahalı bir dizi tamamen
boşa üretiliyordu. Ayrıca yapay gerilme bloğu **aynı ifadeyi ikinci kez**
hesaplıyordu.

`W(q)` artık tembel hesaplanıp paylaşılıyor. Rijit dönme profilinde `kernel_w`
toplam sürenin %6'sıydı; süreklilik modunda bu tamamen kazanç, summation +
yapay gerilme durumunda tekrar ortadan kalkıyor.

## Ölçülüp vazgeçilen: GPU hash-grid yeniden kurulumu

`step()` içinde `_eval()` iki kez çağrılır ve ikincisinde **konumlar
değişmemiştir** (aradaki tek işlem bir hız tekmesidir), yine de
`gridman.build()` çalışır. Mantıken gereksiz bir iş.

Ölçüldü:

| nx | N | grid kurulumu | tam eval | oran |
|---|---|---|---|---|
| 7 | 2 590 | 0,08 ms | 12,64 ms | %0,6 |
| 9 | 6 348 | 0,15 ms | 31,15 ms | %0,5 |

Yeniden kurulum eval maliyetinin **binde beşi**. Bunu atlamak için "x değişti
mi" durumu taşımak, %0,5 için kalıcı bir karmaşıklık ve yeni bir hata yüzeyi
demekti. **Değişiklik yapılmadı.** Kayda geçiriliyor ki aynı hipotez tekrar
araştırılmasın.

Taylor koşusunun yerel yavaşlığı algoritmik değildir: RTX 3050'de FP64 hızı
FP32'nin 1/32'sidir. Aynı koşu TRUBA H100'de kat kat hızlıdır ve kapı
kanıtları zaten orada üretilir.

## Sonuç

| Senaryo | önce | sonra |
|---|---|---|
| Elastik dalga res=300 | 26,1 s | 14,0 s |
| Elastik dalga res=400 | 66,5 s | 38,2 s |
| Yerçekimi test grubu (14 test) | 297 s | 97 s |
| **Tam test paketi (374 test)** | **27:28** | **19:25** |

- (+) Kapı koşuları ve test paketi belirgin biçimde hızlandı.
- (+) Barnes-Hut artık gerçekten bir hızlandırma yapısı.
- (−) `bh_accel` artık NumPy vektör ifadeleriyle değil skaler döngüyle
  yazılmış; okunabilirlik bir miktar düştü. Karşılığında gezinme mantığı
  (halat dizileri, açıklık kriteri) birebir aynı kaldı ve GPU çekirdeğiyle
  satır satır karşılaştırılabilir durumda.
- (−) Sonuçlar önceki sürüme göre ~1 ULP kaydı; kanıt raporlarındaki eski
  sayılarla birebir karşılaştırma yapılırken bu akılda tutulmalı.

## GPU yolu: yapısal olarak asgari (ölçüldü)

İkinci turda GPU çekirdek dağılımı ölçüldü (Taylor nx=9, N=6348, ~268 komşu):

| Çekirdek | süre | eval payı |
|---|---|---|
| `velocity_gradient_3d` | 12,16 ms | %39,0 |
| `forces_solid_3d` | 19,74 ms | %63,3 |
| tam `_eval()` | 31,19 ms | %100 |

İki komşu-gezinme çekirdeği eval'in tamamını oluşturuyor. Akla gelen
optimizasyon, ikisini **tek gezinmede** birleştirmekti — bu, komşu döngüsünü
yarıya indirirdi.

**Mümkün değil.** `forces_solid_3d`, `velocity_gradient_3d`'nin ürettiği
Balsara faktörünü `fbal` hem `i` hem `j` için okur (`0.5*(fbal_i + fbal_j)`).
Yani *herhangi bir* kuvvet hesaplanmadan önce *tüm* parçacıkların `fbal`'ı
hazır olmalıdır. Bu küresel bağımlılık iki ayrı geçişi zorunlu kılar.

Aynı şekilde `forces_solid_3d`, EOS'tan gelen `P`/`cs` ve `stress_rate`'ten
gelen `dSdt`'ye bağlıdır. Çekirdek zinciri (yoğunluk → EOS → hız gradyanı →
gerilme hızı → kuvvetler) veri bağımlılıklarının izin verdiği en kısa
sıradır.

Komşu sayısı da düşürülemez: `h/dx = 2,0` (~268 komşu) Wendland C2'nin Sedov
doğruluğu için gereklidir (ADR-0013). FP64 ise ADR-0002 ile kilitlidir.

Sonuç: **GPU tarafında algoritmik bir kazanç kalmamıştır.** Yerel yavaşlık
donanımsaldır (RTX 3050'de FP64 = FP32/32); kanıt koşuları H100'de yapılır.

## Değerlendirilen alternatifler

- **`bh_accel`'i hedefler üzerinde vektörleştirmek** — muhtemelen bir 10×
  daha verirdi, ama gezinme mantığını GPU çekirdeğiyle karşılaştırılamaz
  hale getirirdi; referansın asıl işi budur.
- **Referansı Warp CPU cihazına devretmek** — referansın Warp'tan bağımsız
  olma şartını ihlal ederdi (çapraz kontrolün anlamı kalmazdı).
- **Yoğun N×N çift matrisini seyrekleştirmek** (`solid_ref`) — 1B'de ~80×
  israf var (her parçacığın ~9 komşusu varken 720 çift hesaplanıyor). Kazanç
  büyük olurdu ama referansın en kolay denetlenen özelliği olan "her çifti
  açıkça hesapla" yapısını bozardı. Ayrı bir karar olarak açık bırakıldı.

## Doğrulama

- `tests/test_uniform_sphere.py` (14 test dahil `theta=0` özdeşliği, 1e-10)
- `tests/test_solid_cross.py`, `tests/test_sph_cross.py` — CPU↔GPU 1e-8
- `tests/test_elastic_wave.py`, `tests/test_ablation.py`, `tests/test_crush_curve.py`
