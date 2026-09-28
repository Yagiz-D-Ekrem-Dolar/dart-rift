# KAYIT-068 — Bu numara bir **boşluktur**: özgün kayıt bu depoda yok (2026-09-28)

**Kapsam:** izlenebilirlik · **Durum:** kayıp belge notu ·
**İlgili:** FAZ4-SIKINTI-RAPORU **A107**,
[KAYIT-069](KAYIT-069_2026-09-28_cozunurluk-bilancosu-ve-standartlastirma.md)

---

## Ne biliyoruz

`docs/truba/PROTOKOL-A98-GEC-EVRE-AV.md` ve `PROTOKOL-A98K-KAZI-AKISI.md`
öncül olarak **KAYIT-068**'i ve `docs/COZUNURLUK-DENETIMI.md`'yi gösteriyor.
Bu iki belge:

- deponun hiçbir commit'inde yok (`git log --all -- <yol>` boş),
- TRUBA'daki hiçbir çalışma ağacında yok (`p1-*`, `agac_*`, `dart-rift`),
- muhtemelen o protokolleri yazan oturumun **yerel kopyasında** kaldı.

Yani A98 ve A98K'nın **kilitli kuralları depoda, gerekçelerinin bir kısmı
dışarıda**. Protokollerin kendisi geçerli ve okunabilir (§1 "Neden"
bölümleri hipotezi ve CPU ölçümünü özetliyor), ama bir okuyucu öncül kaydı
bu depodan takip edemiyor.

## Neden dosya olarak duruyor

Defter numaraları kesintisiz olmalı (`test_defter_index.py`); bir numarayı
sessizce atlamak, kaydın hiç var olmadığını düşündürür. Bu dosya boşluğun
**ne olduğunu** söylüyor. Kural gereği hiçbir satır silinmez: özgün kayıt
bulunursa bu dosyaya **ek** olarak yazılır, bu not yerinde kalır.

## Bu boşluk hangi sonuçları etkiler

Hiçbir kilitli yargıyı etkilemez. A98/A98K/A103/A104/A105'in sonuçları
JSON'larıyla birlikte arşivde (`S_A98.json`, `S_A98K.json`, `S_A103.json`,
`S_A104.json`, `S_A105.json`) ve KAYIT-069 §1'de özetli. Etkilenen tek şey
**izlenebilirlik**: "bu protokol neden yazıldı" sorusunun tam cevabı eksik.
