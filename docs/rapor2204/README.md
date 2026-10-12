# TÜBİTAK 2204-A proje raporu — Türkçe

`rapor.tex`, 2204-A başvurusu için Türkçe proje raporudur. Ön baskının
(`../preprint`, DOI [10.5281/zenodo.23284193](https://doi.org/10.5281/zenodo.23284193))
çevirisi değildir: aynı ölçümleri 2204'ün istediği bölüm yapısında
(Giriş / Yöntem / Bulgular / Sonuç ve Tartışma / Öneriler / Kaynaklar),
Türkçe ve tek kolon olarak sunar.

## Derleme

```
make          # yedi şekil, sonra rapor (iki kez, çapraz başvurular için)
make temiz    # ara dosyaları sil
```

`make` kurulu değilse (Windows'ta çoğu zaman değil) aynı iş Git Bash'ten:

```bash
cd docs/rapor2204
for f in hedef kaskad tasarim kapilar bulgular atlas duyarlilik; do
  lualatex -interaction=nonstopmode -halt-on-error sekil/$f.tex
done
lualatex -interaction=nonstopmode rapor.tex
lualatex -interaction=nonstopmode rapor.tex
```

lualatex gerekir (pdflatex'in sabit ana belleği parçacık ölçekli
şekillerde tükeniyor). Kaynaklar: `rapor.tex`, `tubitak.sty`,
`sekil/*.tex`. PDF'ler derleme ürünüdür, depoda tutulmaz.

## Veri nereden geliyor

Şekiller veriyi **`../preprint/veri/*.dat`** dosyalarından okur; burada
kopyası tutulmaz. O dosyalar `scripts/onkayit_veri.py` ile sahne
kurucusunun kendi çıktısından üretilir. Tek kaynak kuralı bilinçlidir:
kopya, iki sayı kümesinin zamanla sessizce ayrışması demektir.

## Ön baskıdan farklar

| | ön baskı | 2204 raporu |
|---|---|---|
| dil | İngilizce | Türkçe (ondalık ayracı virgül) |
| düzen | iki kolon, dergi | tek kolon, A4, 1,5 satır aralığı |
| şekil | 7 | 7 (ikisi yalnız burada: kapılar; biri yalnız orada: projeksiyon) |
| kimlik | yazar adları ve ORCID | **gizli** (aşağıya bakınız) |

Ön baskının kaynakları **değiştirilmedi**. O metin DOI ile yayımlandı ve
yatırılan dosyayla bayt bayt aynı tutuluyor; şekillerin Türkçe sürümleri
bu dizinde ayrıca kuruldu.

## Kimlik bilgisi

Rapor varsayılan olarak **kimliksiz** derlenir: başlık sayfasında öğrenci,
danışman ve okul adı yoktur. Gerekçe, ön değerlendirmenin rapor üzerinden
yapılması ve kılavuzun rapor metninde kimlik bilgisi istememesidir.

Kimlikli sürüm için `rapor.tex` içindeki şu satırın başındaki `%` kaldırılır:

```latex
% \kimlikliyazdirtrue
```

Adlar ve kurum zaten `\ekip{...}` ve `\kurum{...}` ile tanımlıdır.

## Başvuru öncesi kontrol edilecekler

Bunlar rapor metnine değil, **başvuru işlemine** ait ve henüz yapılmadı:

- [ ] **Ana alan / tematik alan:** Fizik → Astronomi ve Astrofizik.
- [ ] **Proje adı sözcük sınırı.** Başlık 11 sözcüktür; kılavuzun o yılki
      sınırı doğrulanmalı.
- [ ] **Özet uzunluğu.** 150–250 sözcük beklenir; mevcut özet bu aralıkta
      yazıldı, kılavuzun sayısı yine de doğrulanmalı.
- [ ] **Sayfa sınırı.** Rapor 11 sayfa; kılavuzun sınırı doğrulanmalı.
- [ ] **TRUBA izin belgesi.** Kılavuz, MEB'e bağlı olmayan kurum/kuruluş
      olanaklarıyla yapılan çalışmalar için ilgili kurumdan izin belgesi
      istiyor. TRUBA bu tanıma giriyor; belge kurumsal yazışma gerektirir,
      erken başlatılmalı.
- [ ] **Başka yarışmaya başvurulmamış olması.** Kılavuz, son başvuru
      tarihinden önce aynı projeyle başka bir yarışmaya katılmış ya da
      başvurmuş projeleri eliyor. Zenodo'daki ön baskı bir yarışma başvurusu
      değil, arşiv kaydıdır; yine de bu maddenin o yılki metni okunmalı.

## Raporun iddia etmedikleri

Metin, üretim posterioru, $(\alpha_b, Y_0, f)$ için nokta tahmini ya da
Hera için sayısal bir öngörü **sunmaz**; bunlar Paper II'ye aittir.
Gerekçe raporun 4.4 bölümünde ve `docs/truba/PROTOKOL-*.md` kilitli
protokollerinde yazılıdır. Havuz tamamlandığında eklenecek bölüm 4.4'ten
sonraki tek bölümdür; geri kalan metin havuza bağlı değildir.
