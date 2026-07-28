```
TÜBİTAK 2204 PROJESİ
MÜHENDİSLİK DEFTERİ — GÜNLÜK ÇALIŞMA KAYDI

Proje Adı   : DART-RIFT
Takım       : kayıt bulunamadı
Danışman    : kayıt bulunamadı
```

============================================================
GÜNLÜK KAYIT NO: 008
============================================================

**Tarih**       : 28.07.2026
**Saat**        : 18:00 – 21:30 UTC+3
**Çalışanlar**  : Yağız Ekrem Dalar (`egitimg16u4`)
**Çalışma Yeri**: Çevrim içi — yerel makine

## BUGÜNKÜ HEDEF

G2 geçildikten sonra FAZ 0, 1 ve 2'yi bütün olarak son kez denetlemek; depoyu
ve belgeleri yayımlanabilir hale getirmek.

## BULGU 1 — `configs/p2_basalt.yaml` hiç geçerli olmamış

FAZ 2'nin örnek config'i şema doğrulamasından **geçmiyordu**. On alan birden
reddediliyordu:

```
physics.tillotson.A / B / u0 / u_iv / u_cv
physics.strength.Y0 / YM / shear_G
physics.porosity.Pe / Ps
  -> Input should be a valid number
```

Kök neden PyYAML'in YAML 1.1 kuralı: **işaretsiz üs sayı değil string olarak
ayrıştırılır.** `2.67e10` → `'2.67e10'`, ama `2.67e+10` → `26700000000.0`.
Şema bilinçli olarak `strict=True` olduğu için string kabul edilmiyor ve
config reddediliyor.

Hata neden bu kadar uzun süre görülmedi? İki nedenden:

1. **CI yalnızca `p0_smoke.yaml`'ı doğruluyordu.** `p1_sod.yaml` ve
   `p2_basalt.yaml` hiç sınanmamıştı. `p0` ve `p1` bilimsel gösterim
   içermediği için sorun yalnızca `p2`'de vardı.
2. **Hata kısmiydi.** `gravity.G: 6.6743e-11` işaretli olduğu için sorunsuz
   ayrışıyordu. Yani dosyanın bir kısmı doğru, bir kısmı bozuktu — göz
   taramasıyla fark edilmesi zor.

Ölçütlerin hiçbiri bu yüzden yanlış geçmedi: kapı senaryoları config'i değil,
doğrudan parametre nesnelerini kuruyor. Ama config yolu kullanılsaydı FAZ 2
hiç başlamazdı.

### Düzeltme

- Değerler `2.67e+10` biçimine çevrildi ve dosyaya **"+ zorunludur, silmeyin"**
  uyarısı yazıldı (birinin "temizleyip" tekrar bozmasını önlemek için).
- `tests/test_configs_valid.py` eklendi: gönderilen **her** config şemadan
  geçmeli, işaretsiz üs içermemeli ve değerleri motora gerçekten ulaşmalı
  (ADR-0006). Testin boş olmadığı doğrulandı — eski içerikle 4 test kalıyor,
  düzeltilmişle 10'u da geçiyor.
- CI artık üç config'i birden doğruluyor.

## BULGU 2 — CI, G1 ve G2 kapılarının GPU'suz korumasını sınamıyordu

`run_g0_gate.py`'nin GPU'suz ortamda "GEÇTİ" demediği CI'da sınanıyordu, ama
aynı koruma `run_g1_gate.py` ve `run_g2_gate.py` için **sınanmıyordu**. Oysa
"test geçilmediyse iddia edilmez" kuralının tamamı bu korumaya dayanıyor;
birinde oluşacak bir gerileme sessizce fark edilmezdi.

CI'ya her iki kapının da GPU'suz koşuda exit 2 döndürdüğünü doğrulayan adım
eklendi. Ucuz bir kontrol: GPU yoksa betikler hemen çıkıyor.

## BULGU 3 — Belgelerde eskimiş iddialar

G1/G2 geçildikten sonra README hâlâ FAZ 0'ı anlatıyordu ve artık **yanlış**
şeyler söylüyordu: "bu depo hiçbir fizik içermez", "SPH/DEM fiziği bu fazda
yasak", "219 test", "5 ADR". `pyproject.toml` ve `CITATION.cff` de yalnızca
FAZ 0'dan söz ediyordu.

README baştan yazıldı: kapı durumu tablosu, doğrulama sonuçları tablosu
(11 senaryonun ölçülen hataları ve eşikleri), üç fazın modül haritası,
kurulum, TRUBA kanıt üretimi, izlenebilirlik ve dürüstlük sınırı. Sürüm
0.1.0 → 0.3.0.

Kapsam iddiası bilinçli olarak dar tutuldu: kapılar **doğrulama
senaryolarının** geçtiğini gösterir; Dimorphos hakkında bilimsel sonuç iddia
edilmez, çarpma koşuları FAZ 3'tedir.

Kanıt dosyalarına (`docs/evidence/`) ve eski defter kayıtlarına
**dokunulmadı** — onlar koşuldukları andaki durumun kaydıdır; sayılarının
güncellenmesi kaydı sahteleştirirdi.

## DEĞERLENDİRME

Bu denetimin iki bulgusu da aynı desenden: **sınanmayan şey bozulur.** Config
doğrulama vardı ama iki config'e uygulanmıyordu; GPU'suz koruma vardı ama iki
kapıda sınanmıyordu. Kod doğruydu, kapsama eksikti.

## SIRADA

- FAZ 3: DART/Dimorphos çarpma koşuları.
