# ADR-0025 — Sahnenin makineler arası determinizmi: ışın dejenereliği ve toplama sırası

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-01
- **Bağlam:** FAZ 3, P3-FR-07 (çarpma geometrisi), G3 C6 (determinizm)
- **İlgili:** ADR-0002 (hassasiyet politikası), ADR-0004 (deterministik RNG),
  ADR-0017 (örneklem gürültüsünü ölçmek), `tests/golden/p3_scene_v1.json`

## Nasıl bulundu

G3 kapısı iki makinede koşuldu ve **sahne karması tutmadı**:

| | karma |
|---|---|
| TRUBA — Linux, CPython 3.10.15, numpy 1.26.4 | `d0ab08bf91ae041c…` |
| yerel — Windows, CPython 3.12.10, numpy 2.5.1 | `39637758a2dabf89…` |

Aynı kod, aynı tohum. `Scene.digest`'i G3 C6'ya "determinizm kanıtı" diye
bağlamıştım, ama karmanın bir **referansı yoktu**: yalnızca "aynı makinede iki
kez aynı" sınanıyordu. Bu boşluk iki ayrı kusuru gizledi.

Dizi dizi ayrıştırınca mesh, moloz yığını, kütleler, malzeme alanları,
`is_boulder`, `is_impactor` ve **hızlar bit-aynı** çıktı; ayrışan yalnızca
sahne konumlarıydı.

## Kusur 1 — ışın-yüzey kesişimi mesh köşesinde dejenere (FİZİKSEL OLARAK ÖNEMLİ)

`impactor._ray_surface`, merkezden çarpma yönüne ışın atıp en uzak üçgeni
seçiyor ve o **fasetin normalini** yüzey normali sayıyordu.

İkosfer(4, 82 m) merkezinden atılan +z ışını, kutup **köşesinden** geçer.
Orada 6 üçgen buluşur ve baryzentrik test sınırdadır (`u`, `w` sıfıra ya da
bire yuvarlanır). Hangi üçgenin noktayı sahiplendiğini kayan-nokta gürültüsü
belirliyordu:

| makine | seçilen üçgen | yüzey normali |
|---|---|---|
| Windows / numpy 2.5.1 | #4064 | (0,0441 · 0 · 0,9990) |
| Linux / numpy 1.26.4 | #3984 | (0,0203 · 0,0385 · 0,9991) |

Aradaki fark ≈ **2,5°**. İkisi de "1 kesişim" raporluyordu — tolerans
olmadığı için diğer 5 üçgen elenmiş ve dejenerelik **görünmez** olmuştu.

P3-FR-07 çarpma açısını **yüzey normaline göre** tanımlar. Yani bu, kozmetik
bir hash farkı değil: senaryonun geometrisi makineye bağımlıydı.

**Bu, `shape_mesh.inside_points`'te sol-üst kenar kuralıyla çözülmüş hata
sınıfının aynısı.** O düzeltmeyi ışın-yüzey kesişimine uygulamamıştım.

### Karar

Tek üçgen seçmek yerine, **aynı `t`'de buluşan bütün üçgenler toplanır** ve
normal, onların **alan ağırlıklı ortalaması** olarak hesaplanır. Toplama yüz
indeksi sırasında yapılır → deterministik. Baryzentrik teste bağıl `1e-12`
tolerans eklendi ki köşeyi paylaşan fasetler elenmesin.

Bu hem makineden bağımsızdır **hem de fiziksel olarak daha doğrudur**:
köşedeki faset normali zaten bir ayrıklaştırma yapısıdır. Ölçülen sonuç —
küre kutbunda normal artık **tam (0, 0, 1)** (bileşenler < 1e-15), simetrinin
gerektirdiği değer.

## Kusur 2 — `TriMesh.centroid`'de toplama sırası (fiziksel olarak ihmal edilebilir)

`centroid` `np.sum` kullanıyordu. NumPy çiftli (pairwise) toplama yapar ve
blok boyu sürüme/SIMD genişliğine göre değişir; sonuç 1–2 ULP oynar.

Simetrik bir ikosferin centroid'i **tam 0** olmalı. Ölçülen:

| makine | centroid |
|---|---|
| Windows / numpy 2.5.1 | (8,0e-15 · 2,1e-15 · −9,0e-15) |
| Linux / numpy 1.26.4 | (5,6e-15 · 2,0e-14 · …) |

82 m'lik bir cisimde bu **2e-16 bağıl** — fiziksel olarak sıfır. Ama çarpma
noktası centroid'den türediği için merminin x,y'si ~1e-14 m kayıyor ve
"aynı tohum aynı sahne" iddiası makineler arası bozuluyordu.

### Karar

`centroid` toplamları `math.fsum` ile yapılır: doğru yuvarlanmış ve
**sıra-bağımsız**. Centroid mesh başına bir kez hesaplandığı için maliyeti
önemsizdir.

> Bu kararı bütün toplamlara genellemedim. `math.fsum` sıcak döngüde pahalıdır
> ve gereksizdir; yalnızca **sonucu aşağı akışta bir karara sokan, seyrek
> hesaplanan** indirgemeler için uygundur. Nerede kullanılacağı ölçümle
> belirlenir, alışkanlıkla değil.

### Latent risk — SONRADAN KAPATILDI (2026-08-01)

Aşağıdaki not, `volume`/`area`'yı fsum'a çevirmemek gerekçesiyle yazılmıştı.
Gerekçe **ölçümle çürüdü**: değişiklik yapıldığında altın karma
`1c6f2a10…` **hiç değişmedi**, çünkü `np.sum` bu veri için zaten doğru
yuvarlanmış sonucu veriyormuş. Yani "altın referansı bozar" endişesi
gerçekleşmedi ve riski kapatmak bedava çıktı.

`TriMesh.volume` ve `TriMesh.area` artık `math.fsum` kullanıyor. Aşağıdaki
bölüm, kararın **neden ertelendiğinin** kaydı olarak duruyor — silinmiyor.

### (Tarihsel) Bilinen latent risk — kapatılmamıştı, izleniyordu

`TriMesh.volume` ve `TriMesh.area` de `np.sum` kullanır ve **aynı sınıftandır**:
mesh başına bir kez hesaplanır, sonuç aşağı akışta karara girer (`volume`,
`place_boulders`'daki hedef blok hacmini ve `pile.mesh_volume` tanısını
belirler).

Ölçüldü: iki makinede **birebir aynı** çıktılar
(`hacim = 2304564.6670879088`). Yani şu an bir sorun **yok**.

Yine de fsum'a çevirmedim, gerekçesi:

- Değişiklik `v_target`'ı son bitlerde oynatabilir; bu, kabul edilen blok
  sayısını değiştirip **altın karmayı geçersizleştirir**. Ölçülmemiş bir
  riski kapatmak için ölçülmüş bir referansı bozmak doğru takas değil.
- Risk artık **sessiz değil**: `tests/test_scene_golden.py` bütün sahne
  karmasını iki platformda sınıyor. `volume` bir gün ayrışırsa test kırılır
  ve düzeltme tek satırdır.

Kayda geçiriliyor ki "unutuldu" ile "bilinçli bırakıldı" karışmasın.

## Sonuç — ölçüldü

Düzeltmelerden sonra iki makinede **birebir aynı**:

```
digest  1c6f2a100ae4a8668556c9798d9bf4436a57ce2bb792cde4811554002347827d
x       fsum=+3.37244559473357804e+04   max|.|=8.28043024302566835e+01
v       fsum=-2.45181509999999963e+06   max|.|=6.14489999999999964e+03
m       fsum=+4.14396762647453928e+09
```

(`math.fsum` sıra-bağımsız ve tam yuvarlar: iki makinede eşitse diziler
bit-aynıdır.)

## Yapısal düzeltme — asıl mesele

Kusurların ikisi de teknikti; **onları gizleyen şey yapısaldı**: `Scene.digest`
G3'te "determinizm kanıtı" olarak sunuluyordu ama bir referansı yoktu.
"Aynı makinede iki kez aynı" sınamak, makineler arası determinizmi
**kanıtlamaz**.

Bu yüzden FAZ 0'daki altın-hash mekanizmasının aynısı sahne için de kuruldu:

- `tests/golden/p3_scene_v1.json` — karma + parametreler + **`verified_on`**
  platform listesi.
- `tests/test_scene_golden.py` — karma eşleşmesi, tohum duyarlılığı, **en az
  iki işletim sistemi ve iki numpy sürümü** şartı, ve iki kusurun doğrudan
  regresyon testleri (kutup normali tam +z; simetrik centroid ~0).

Altın dosya yalnızca **bilinçli değişiklik + ADR** sonrası güncellenir.

## Alınan ders

Bir karmayı "determinizm kanıtı" diye sunmak, o karmanın **neye karşı**
sınandığını söylemeden anlamsızdır. Aynı makinede tekrar ≠ makineler arası
determinizm. Bu proje FAZ 0'da doğru mekanizmayı kurmuştu; FAZ 3'te yeni bir
artefakt (`Scene`) eklerken aynı mekanizmayı ona uygulamayı atladım — ve
boşluk iki gerçek kusuru taşıdı.
