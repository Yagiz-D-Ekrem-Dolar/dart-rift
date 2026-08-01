# ADR-0027 — Grady-Kipp hasar modeli: P2 §1.3 STRETCH kapatıldı

- **Durum:** Kabul edildi
- **Tarih:** 2026-08-01
- **Bağlam:** P2 §1.3 hasar/kırılma modelini **STRETCH** olarak bırakmış, kod
  `D = 0` sabitlemişti. Bu ADR o boşluğu kapatır.
- **İlgili:** ADR-0012 (plastik iş çift sayılmaz), ADR-0004 (deterministik RNG)

## Neden gerekliydi

Dimorphos gibi zayıf, gözenekli bir cisimde krater oluşumu **çekme kırılmasıyla**
yürür: şok geçtikten sonra serbest yüzeyden yansıyan seyrelme dalgası malzemeyi
çekmeye sokar ve orada koparır (spallasyon). `D = 0` bırakmak, malzemenin
çekmede sınırsız dayanıklı olduğunu varsaymak demekti — krater hacmini ve
dolayısıyla ejekta kütlesini, yani **β'yı** sistematik olarak küçültürdü.

## Model

Benz & Asphaug (1995) formülasyonu.

**Weibull kusur dağılımı.** Birim hacimde aktivasyon gerinimi ε'dan küçük
mikro-çatlak sayısı `n(ε) = k ε^m`. Ters dönüşümle j'inci kusurun gerinimi
`ε_j = (j / (k V_toplam))^(1/m)`; kusurlar parçacıklara **deterministik**
olarak dağıtılır (`dartrift.rng` akışı `damage_flaws`).

**Aktivasyon ölçüsü.** Yerel skaler gerinim `ε = max(σ_max, 0) / E`, burada
σ_max, σ = −P·I + S tensörünün **en büyük özdeğeri** (bu depoda P > 0 basmadır,
dolayısıyla pozitif özdeğer çekmedir) ve `E = 9KG/(3K+G)`.

> Yalnızca `−P`'ye bakmak (hacimsel çekme) **kesme kaynaklı kırılmayı tamamen
> kaçırırdı.** Özdeğer, GPU'da simetrik 3×3 için kapalı formla (Smith 1961)
> hesaplanır — iteratif çözücü yok, sabit işlem sayısı, determinizm korunur.

**Hasar evrimi.** `d(D^(1/3))/dt = n_aktif · c_g / R_s`, `c_g = 0,4 c_s`.
D ∈ [0,1] ve **monoton**: kırılan kaya kendini onarmaz. Monotonluk kernel'de
zorlanır.

**Uygulama — kritik ayrım.** Hasar **yalnızca çekmeyi** zayıflatır:

| durum | etki |
|---|---|
| P < 0 (çekme) | P → (1−D)·P |
| P ≥ 0 (basma) | **değişmez** |
| S (deviatorik) | S → (1−D)·S |

Basmayı da zayıflatmak kraterlenmeyi tamamen yanlış yapardı: şok önünde
malzeme basma altındadır ve orada dayanım kaybı fiziksel değildir.

## Çözücüdeki yer — ölçülerek belirlendi

Hasar bloğu, gerilme hızından **sonra**, kuvvetlerden **önce** çalışır:

- `dSdt` **ham** S'den hesaplanmalı — hasar elastik evrimi değil, taşınan
  gerilmeyi zayıflatır.
- Kuvvetler **zayıflatılmış** P ve S'yi görmeli; yoksa hasarın dinamiğe hiçbir
  etkisi olmaz (modül "eklenmiş ama bağlanmamış" olur).
- Hasar **hızı** ham gerilmeden hesaplanır, **sonra** uygulama yapılır. Ters
  sırada hasar kendi tetiğini zayıflatır ve büyüme yapay olarak yavaşlar.
- Birikim **tam adımda** yapılır, yarım adımlarda değil: D monoton ve [0,1]'e
  kısık olduğu için trapez yolunun anlamı yok, üstelik iki yarım adım
  monotonluk kısıtıyla birleşince tekrarlanabilir olmayan bir sıra doğururdu.

## Doğrulama

32 test. Analitik/fiziksel olarak bilinen durumlar:

- σ_max köşegen, saf kesme ve **dönme altında değişmezlik** (özdeğerler dönme
  değişmezidir) — CPU.
- GPU kapalı-form özdeğer, CPU `eigvalsh` ile bağıl < 1e-10 uyuşuyor.
- Basmada gerinim tam 0; çekmede ε = σ/E.
- Eşik altında hiç kusur açılmaz; üstünde açılır ve kusur sayısında **sınırlanır**.
- Hasar basmayı **değiştirmez**, çekmeyi (1−D) ile çarpar.
- D = 0 iken P ve S **bit-aynı** kalır (ablasyon).
- GPU: D ∈ [0,1] ve **monoton** (geri dönüş yok); dayanım kapalıyken model
  **reddedilir**; hasar açık/kapalı sonuçlar **farklı** (bağlanmadığını yakalar).

**Dış kaynak kontrolü.** Varsayılan k = 1e29 1/m³, m = 9 ile tek parçacık
hacminde ilk kusur gerinimi 6,0e-4; E = 5,31e10 Pa ile çekme dayanımı
**≈ 32 MPa** — bazalt için literatür bandı (10–30 MPa) ile uyumlu. Bu, uydurma
parametre olmadığının kontrolüdür; değerler FAZ 5'te posterior olarak
**sınanır**, varsayılmaz.

## Ölçme tuzağı — kayda geçiriliyor

"Basmada hasar oluşmaz" testini önce 40 adım koşturdum ve iç bölgede D = 1,0
buldum. **Kusur modelde değildi:** h = 1 m, c_uzun ≈ 3348 m/s → küp boyu ses
geçişi ≈ 1,2e-3 s, 40 adım ise ≈ 3,0e-3 s. Sıkışma dalgası serbest yüzeyden
yansıyıp çekmeye dönmüştü — **gerçek spallasyon fiziği** ve model doğru
davranıyordu. Test yanlış **ana** bakıyordu.

Test artık ses geçiş süresinin dörtte birinde ölçüyor. Ayrıca serbest yüzeyde
SPH çekirdek eksikliği küçük bir deviatorik gerilme doğurduğu için ölçüm **iç
bölgeyle** sınırlı — yoksa test, ölçmek istediği şeyi değil yüzey yapayını
ölçerdi.

## RNG akışına ekleme

`STREAMS` sözlüğüne `damage_flaws: 3` eklendi. ADR-0004'ün yasakladığı şey var
olan bir akışın kimliğini/sırasını oynatmaktır; **sona ekleme** mevcut 0/1/2
kimliklerini değiştirmez ve hiçbir altın hash etkilenmez. Yeni akışlar daima
sona eklenir.

## Bilinen sınır

Hasar **enerji defterine ayrı bir kalem olarak girmez**. Kırılma yüzey enerjisi
(Griffith) modellenmiyor; hasar yalnızca gerilme taşıma kapasitesini düşürüyor.
Bu, Benz & Asphaug formülasyonunun kendi sınırıdır ve enerji hatası olarak
görünmez (zayıflatma iş yapmaz, sadece kuvveti azaltır). FAZ 4'te enerji
defteri hasarla birlikte yeniden ölçülmeli.
