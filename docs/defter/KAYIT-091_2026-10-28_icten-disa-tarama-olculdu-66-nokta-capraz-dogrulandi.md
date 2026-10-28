# KAYIT-091 — İçten dışa tarama ölçüldü: **66 nokta çapraz doğrulandı**, 13'ü doğrulanmadı

**Tarih:** 2026-10-28 · **Sıfır GPU** (kullanıcı kararı: *"gpu kullanma"*)
**İşler:** `6864679` (`arama_derinligi` taraması), `6864736` (yön
karşılaştırması) · 96/96 nokta
**Öncül:** [ADR-0062](../adr/ADR-0062-ortulu-krater-olculemez-sayi-yerine-red.md) §3
(*"içten dışa çevirmek … sırayı koruyor"*), [KAYIT-090](KAYIT-090_2026-10-28_havuzda-krater-yeniden-okundu-ve-geri-alma-kapisi.md)
**Sonuç:** [ADR-0063](../adr/ADR-0063-yuzey-icten-disa-taranir.md)
**Veri:** [`havuz_krater_tarama_96.csv`](../sonuclar/havuz_krater_tarama_96.csv)

---

## 1. Tek cümle

İçten dışa tarama, kilitli 46 ölçümü **makine hassasiyetinde** yeniden
üretiyor ve 20 noktayı bağımsız bir tanıyla **uyuşarak** kurtarıyor —
ama 13 noktada tek başına kalıyor ve orada savunulamayan sayılar
üretiyor (`+36,49 m` krater derinliği). Bu yüzden **varsayılan
değiştirilmedi**.

## 2. Niçin denendi

ADR-0062 krateri örtülü noktalarda reddediyor, ama reddin kendisi bir
ölçüm değil: havuzun `50/96` noktası okunamıyor ve `Y₀` ortancaları
`9,3` Pa, yani tam posteriorun işaret ettiği yer. ADR-0062 §3 asıl
çözümü adıyla saymış, "sırayı koruyor" diyerek açık bırakmıştı.
Kullanıcı *"Evet, ölç ve ADR yaz"* dedi. **Önce ölçüldü.**

## 3. Sentetikte — bir ayar değil, bir tanım

Levha, `1 m` derin paraboloit çukur, eksen üstünde **bağlı** örtü:

| örtü | `distan` | `icten` |
|---|---|---|
| yok | +0,9216 | **+0,9216** |
| 2 m | RED | **+0,9216** |
| 12 m | RED | **+0,9216** |
| 30 m | RED | **+0,9216** |
| 50 m | RED | **+0,9216** |
| 0 m (yüzeye değiyor) | −0,9134 | **+0,9161** |

`distan`'da eğim `−1,000` (örtüyü okuyor), `icten`'de **`0`**. Ve örtü
çukuru gerçekten doldurduğunda `icten` bunu görüyor — kör değil.

## 4. İkinci, bağımsız tanı: `arama_derinligi` taraması

ADR-0062 §3 derinliği büyütmeyi *düzeltme olarak* reddetmişti; burada
yalnız **ikinci bir ölçüm aracı** olarak kullanıldı.

| `arama_derinligi` | ÖLÇÜLDÜ | ÖRTÜLÜ | YÜZEY_YOK |
|---:|---:|---:|---:|
| 10 m (kilitli) | 46 | 25 | 25 |
| 20 m | 51 | 28 | 17 |
| 40 m | 59 | 30 | 7 |
| 60 m | 66 | 30 | **0** |

Kritik kontrol: pencereyi uzatmak **hiçbir ölçülen değeri
değiştirmiyor** — 46 noktada `10 m` ile `60 m` arasında en büyük
mutlak fark `1,4e-14` m. Yani pencere makinesi sağlam; değişen yalnız
hangi noktaların okunabildiği.

## 5. Yön karşılaştırması — havuzda

| | ÖLÇÜLDÜ | ÖRTÜLÜ | YÜZEY_YOK |
|---|---:|---:|---:|
| `distan` (kilitli) | 46 | 25 | 25 |
| `icten` | **79** | 17 | **0** |

Geçişler: `OLCULDU→OLCULDU 46` · `ORTULU→OLCULDU 11` ·
`ORTULU→ORTULU 14` · `YUZEY_YOK→OLCULDU 22` · `YUZEY_YOK→ORTULU 3`.

**46 ortak noktada bağıl fark: ortanca `0,000e+00`, en büyük
`1,868e-14`.** Yeni tanım hiçbir yayımlanmış sayıyı değiştirmiyor.

## 6. Çapraz doğrulama — sıfır çelişki

`icten`'in kurtardığı 33 noktanın 20'sini `distan@60m` de ölçüyor:

| | n |
|---|---:|
| iki tanı da ölçüyor, **`%1` içinde uyuyor** | **20** |
| iki tanı da ölçüyor, **çelişiyor** | **0** |
| yalnız `icten` ölçüyor | 13 |

Örnek (idx, `Y₀`, `icten`, `distan@60m`): `7, 54,2, +2,217, +2,217` ·
`8, 688,8, +0,684, +0,684` · `9, 52,0, −0,651, −0,651` ·
`18, 4100,8, +0,772, +0,772`. Dört basamağa kadar aynı.

Toplam **66** nokta çapraz doğrulandı (46 + 20).

## 7. Ve doğrulanmayan 13 — niçin güvenilmiyor

`icten` bu 13'te sayı veriyor, `distan@60m` ÖRTÜLÜ diyor. Değerler:

| idx | `Y₀` (Pa) | `icten` `d_merkez` (m) |
|---:|---:|---:|
| 87 | 1,35 | **+36,490** |
| 6 | 5,76 | **+28,609** |
| 19 | 1,78 | +4,968 |
| 16 | 1,15 | +4,434 |
| 14 | 13,46 | +4,356 |
| 45 | 433,31 | +0,707 |
| 52 | 17,23 | −0,724 |
| 25 | 73,46 | −0,793 |
| 85 | 98,68 | −1,436 |
| 84 | 18,57 | −3,028 |
| 49 | 43,12 | −5,399 |
| 24 | 29,90 | −5,560 |
| 0 | 28,30 | −5,587 |

Hedefin yarı eksenleri `58 – 88,5` m. `+36,49 m` derinlik (ve
`V = 3 043 m³`) gövdenin yarısı kadar bir çukur demek — fiziksel değil.

**Sebep:** `icten`, `taban`'dan dışa çıkarken `phi`'nin eşik altına
**ilk** düştüğü yeri alıyor. Çarpma gövde içinde bir boşluk bıraktıysa
(hasar, gözeneklilik, ayrılmış katman) tarama dış yüzeye varmadan orada
duruyor.

> **İki yön de aynı sınıfın hatasını yapıyor:** doğru kesişimi
> *doğrultuya bakarak* seçmek. `distan` yukarıdaki yığına takılıyor,
> `icten` içerideki boşluğa. Asıl çözüm **bağlantılılık** ölçütüdür —
> `taban`'ı içeren bağlantılı bileşenin dış yüzeyi. Yazılmadı; önü de
> kapatılmadı.

**Ayrım sayıya vuruyor:** çapraz doğrulanan 66 noktanın aralığı
`−4,930 … +4,428` m; doğrulanmayan 13'ünki `−5,587 … +36,490` m. İki
absürt değer de doğrulanmayan kümede.

## 8. Karar — varsayılan **değişmedi**

Bugün düzeltilen kusurun özü *savunulamayan bir sayıyı sessizce
döndürmekti*. `icten`'i varsayılan yapmak, 13 noktada aynı şeyi
yapardı. Bu yüzden ADR-0063:

- `tarama` **yan yana alan** olarak eklendi, varsayılan `"distan"` ve
  **bit-aynı** (24 mevcut krater sınavı aynen geçti; açıkça
  `tarama="distan"` vermek ile vermemek aynı sonucu veriyor — sınavlı).
- `icten`, **tanı ve Hera ön kaydı için tercih edilen tanım**, ama
  yalnız çapraz doğrulanmış 66 noktada.
- Varsayılanın değişmesi 13 noktanın çözülmesine bağlı.

11 yeni sınav: `tests/test_krater_tarama_yonu.py`.

## 9. Kazanç

Krater gözlemlisi **46 → 66** okunabilir noktaya çıktı ve hepsi iki
bağımsız tanımla doğrulanmış durumda. Hera ön kaydı için kullanılabilir
taban `%48`'den **`%69`**'a çıktı.

## 10. Kilitli yargılara etkisi — YOK

`krater_derinlik` ADR-0055 ile isteğe bağlı; posteriora girmiyor.
`n_yön = 1` (KAYIT-079), tarih eşlemesi (KAYIT-080), SBC (KAYIT-081),
çözünürlük yanlılığı (KAYIT-085), `n_yön` dayanıklılığı (KAYIT-087)
**etkilenmez**.

## 11. Commit mesajı düzeltmesi

`1ac1ddd` commit'inin gövdesinde ters tırnaklı sözcükler (`icten`,
`taban`, `arama_derinligi`) kabuk tarafından yutuldu ve mesajda boşluk
olarak göründü. İçerik burada tam hâliyle duruyor. (Aynı tuzağın bir
önceki örneği: `e73aaa7`.)
