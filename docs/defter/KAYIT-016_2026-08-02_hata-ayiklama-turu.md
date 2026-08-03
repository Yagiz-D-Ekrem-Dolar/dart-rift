# KAYIT-016 — Hata ayıklama turu: "0 hata" iddiası yanlıştı

**Tarih:** 2026-08-02
**Bağlam:** FAZ 3 tamamlandı diye sunulmuştu; aktif hata ayıklama istendi.
**İlgili:** ADR-0029, `docs/EKSIKLER.md` §0

---

## Ne oldu

FAZ 3 şöyle sunulmuştu: 627 test geçiyor, G3 kapısı 7/7, 14 kırmızı-takım
maddesi temiz, "0 hata". Bu sunum reddedildi.

Tur **dört kusur** buldu. İkisi bilimsel sonucu birinci mertebede bozuyordu.
Sayılar ADR-0029'da; burada **nasıl bulunduğu** duruyor.

## Nasıl bulundu — yöntem notu

Tur, "en yeni ve en az sınanmış kod yolu" ile başladı: hasar modelinin
**çözücüye bağlanması**. Modülün kendi testleri (32 tane) formülleri
sınıyordu; hiçbiri döngüyü sınamıyordu.

Yapılan şey basitti ve tekrarlanabilir: **fiziği dondur, davranışa bak.**
TRUBA'da `D = 0.5` sabitlendi, hiçbir gerinim üretilmeyecek şekilde kurulum
yapıldı ve `_eval()` art arda çağrıldı. Fizik durduğuna göre `S` sabit
kalmalıydı:

```
S[0,0,1] başlangıç : 1.000000e+07
1. _eval() sonrası : 5.000000e+06     <-- beklenen SABIT 5.0e+06
2. _eval() sonrası : 2.500000e+06
3. _eval() sonrası : 1.250000e+06
4. _eval() sonrası : 6.250000e+05
--- step() ile, D sabit, gerinim yok ---
adım 1: S[0,0,1] = 1.250000e+06
adım 5: S[0,0,1] = 4.882812e+03
```

**Hiçbir fizik yokken S 1000 kat düştü.** Sebep: `apply_damage_k` durum
değişkenini yerinde çarpıyordu ve `_eval()` adım başına iki kez çağrılıyor.

Bu yöntem — *evrimi durdur, değişmemesi gerekeni ölç* — kalan üç kusurun
üçünde de işe yaradı:

- **Krater:** kratersiz bir cisme krater çıkarıcıyı uygula. Küre için 0
  veriyordu (o yüzden tüm testler geçiyordu); **Dimorphos elipsoidi** için
  9,04 m verdi.
- **Duyarlılık taraması:** yayılımı eksen başına ayır. Toplam pozitifti ama
  hız ekseni **tam sıfır** çıktı.
- **Yarıçap kestirimi:** düzgün dolu kürede analitik cevabı bilinen bir
  büyüklüğü ölç. `median(dist)` = 0,794 R çıktı, R değil.

## Kanıt koşuları

| iş | commit | ne | sonuç |
|---|---|---|---|
| 1446269 | 515b1d4 | kusur ölçümü (düzeltme öncesi) | S 1,0e7 → 4,88e3 |
| 1446277 | 9e2d3e1 | düzeltme kanıtı + tam takım + G3 | dbg **DÜZELDİ**, 5 idempotence testi geçti, 34 hasar testi geçti, **627 test geçti**, **G3 rc=0 (7/7)** |

Düzeltme sonrası aynı ölçüm (H100, kolyoz14):

```
1. _eval(): S(DURUM)=1.000000e+07   S_eff(TAŞINAN)=5.000000e+06
2. _eval(): S(DURUM)=1.000000e+07   S_eff(TAŞINAN)=5.000000e+06
3. _eval(): S(DURUM)=1.000000e+07   S_eff(TAŞINAN)=5.000000e+06
4. _eval(): S(DURUM)=1.000000e+07   S_eff(TAŞINAN)=5.000000e+06
adım 1..5: S(DURUM)=1.000000e+07 (sabit)
SONUÇ: DÜZELDİ
```

## Ders — kaydın asıl sebebi

Dört kusur da aynı kör noktadan geldi: **testler parçaların doğruluğunu
sınıyordu, bütünün davranışını değil.**

Daha keskin hali: *bir kriter geçtiğinde, geçme SEBEBİNİN de ölçülmüş olması
gerekir.* "Hasar sonucu değiştiriyor", "yayılım pozitif", "derinlik makul" —
üçü de doğru sebeple **ve** yanlış sebeple sağlanabilir. Bu turdan önce
hangisi olduğu ölçülmüyordu.

Bu yüzden eklenen her şey artık **neyin iş gördüğünü** ayrı ayrı raporluyor:
`radius_axis_active`, `speed_axis_active`, `reference_is_spherical`,
`target_radius_estimated`, ve `_eval()` saflık değişmezi.

## Turun kendi hatası — GPU testinin tahmini ölçülmeden yazıldı

Tur sırasında eklediğim `test_parcacik_basina_Y0_SONUCU_degistiriyor` **kaldı**
ve **dört kapıyı birden düşürdü** (her kapı tam pytest paketini koşuyor).

Kusur kodda değildi, **benim tahminimdeydi**: *"zayıf kohezyon daha çok
plastik iş üretir"* yazmıştım. Ölçülen tam tersi.

Ters çevirmeden önce ilişkiyi ölçtüm (iş 1448928, H100, testin kendi kurulumu):

| kol | Y0_ort | plastik iş |
|---|---|---|
| hepsi-zayıf | 1,0000e+04 | 1,459238e+07 J |
| heterojen | 2,3565e+06 | 1,890912e+09 J |
| hepsi-güçlü | 1,0000e+07 | 1,264309e+10 J |

`hepsi-güçlü / hepsi-zayıf = 866,42` (Y0 oranı 1000).

**Fizik:** tam plastik rejimde dağılım hızı `σ_akma · ε̇_p`, yani iş yield
gerilmesiyle **artar**. Akmanın *başlangıcı* ile *büyüklüğünü* karıştırmışım:
düşük Y0'da akma erken başlar ama her adımda az enerji atar; yüksek Y0'da geç
başlar ve çok atar — ikincisi baskın.

Yeni test öncekinden **güçlü**: üç kol ve **kuşatma**. Heterojen değer iki
homojen sınırın tam arasında olmalı; çekirdek herhangi bir skaler kullansaydı
sınırlardan birine otururdu.

**İki ders:**

1. **GPU-only testler yerelde SKIP oluyor.** Yerel takım 528/0 geçerken bu
   test hiç koşmadı. Yerel yeşil, GPU testi için kanıt değildir.
2. **Bir GPU testinin tahmini önce ÖLÇÜLMELİ, sonra yazılmalı.** Bu turun
   tamamı "ölçmeden iddia etme" üzerineydi; aynı hatayı testi yazarken
   yaptım.

## Süreç notu

- `squeue -u egitimg16` boş dönüyor: işler `egitimg16u4` altında koşuyor.
  Doğru komut `squeue -u $USER` ya da `sacct -j <id>`. Bu, bir işi bitmiş
  sanmaya yol açtı; iş aslında koşuyordu.
- PowerShell heredoc (`<<'EOF'`) desteklemiyor; çok satırlı commit mesajları
  Bash aracıyla yazılmalı. Bu daha önce de bir commit'i atlatmıştı
  (DEVAM.md'de kayıtlı).
