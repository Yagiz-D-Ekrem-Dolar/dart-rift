# TÜBİTAK 2204-A proje raporu

> **17 sayfa** (sınır 20) · **11 şekil** · **18 denklem** · **3 tablo**
> Yapı: `proje_yazma_sablonu_2026-2027.docx` · Dil: Türkçe

`rapor.tex`, 2204-A başvurusu için Türkçe proje raporudur. Ön baskının
([`../preprint`](../preprint), DOI
[10.5281/zenodo.23284193](https://doi.org/10.5281/zenodo.23284193))
çevirisi **değildir**: aynı ölçümleri resmî şablonun istediği yapıda,
Türkçe ve tek kolon olarak sunar.

---

## Derleme

```bash
make          # on bir şekil, sonra rapor (iki kez, çapraz başvurular için)
make temiz    # ara dosyaları sil
```

`make` kurulu değilse (Windows'ta çoğu zaman değil) aynı iş Git Bash'ten:

```bash
cd docs/rapor2204
for f in dejenerasyon cekirdek malzeme hedef kaskad tasarim \
         kapilar bulgular atlas duyarlilik eksen; do
  lualatex -interaction=nonstopmode -halt-on-error sekil/$f.tex
done
lualatex -interaction=nonstopmode rapor.tex
lualatex -interaction=nonstopmode rapor.tex
```

**lualatex gerekir** — pdflatex'in sabit ana belleği parçacık ölçekli
şekillerde tükeniyor, ve pgfmath `1e-5`'in altında taşıyor.

Kaynaklar: `rapor.tex`, `tubitak.sty`, `sekil/*.tex`, `veri/*.dat`.
PDF'ler derleme ürünüdür, depoda tutulmaz.

---

## Şablona uygunluk

Resmî şablonun biçim kuralı birebir uygulanmıştır:

| kural | şablon | rapor |
|---|---|---|
| yazı tipi | Times New Roman | newtxtext (Times klonu) |
| punto | 12 | 12 |
| kenar boşluğu | her yandan 2,5 cm | 2,5 cm |
| satır aralığı | **tek** | tek |
| hizalama | iki yana yaslı | iki yana yaslı |
| sayfa sınırı | en fazla 20 | **17** |
| kapak sayfası | **yasak** | yok |
| kimlik bilgisi | **yasak** | yok (aşağıya bakınız) |

> **Yazı tipi notu.** newtxtext, Times New Roman'ın ölçü ve görünüm
> olarak eşi olan serbest klonudur. Gerçek TTF'yi `fontspec` ile çağırmak
> metin tarafında çalışır ama matematik tarafını bozar; rapor denklem
> yoğun olduğu için klon tercih edildi. Baskıda ayırt edilemez.

Bölüm sırası da şablondan: Proje Ana/Tematik Alanı → Proje Adı → **Yapay
Zekâ Araçları Kullanım Beyanı** → Özet → Anahtar Kelimeler → Amaç →
Giriş → Yöntem → İş-Zaman Çizelgesi → Bulgular → Sonuç ve Tartışma →
Öneriler → Kaynaklar → Ekler.

---

## ⚠ Göndermeden önce **mutlaka** yapılacaklar

- [ ] **Yapay Zekâ Beyanını oku ve doğrula.** 2026-2027 şablonunun yeni
      zorunlu bölümü. Dört başlık (araç, amaç, kapsam, insan müdahalesi)
      dolduruldu, ama yalnız *görülebilen* kullanım yazıldı. Başka araç
      kullandıysan ekle. **Eksik ya da yanlış beyan diskalifiye
      sebebidir.**
- [ ] **Son başvuru tarihini TYBS'den teyit et.** Depoda 4 Ocak 2027
      kayıtlı; sözlü olarak "10 gün" denildi. İkisi çok farklı sıralama
      gerektiriyor.
- [ ] **TRUBA izin belgesi.** Kılavuz, MEB'e bağlı olmayan kurum
      olanaklarıyla yapılan çalışmalar için izin belgesi istiyor. TRUBA
      bu tanıma giriyor; kurumsal yazışma gerektirir, **erken başlat**.
- [ ] **Başka yarışmaya başvurulmamış olması.** Zenodo'daki ön baskı bir
      yarışma başvurusu değil, arşiv kaydıdır; yine de maddenin o yılki
      metni okunmalı.
- [ ] **Sözcük sınırları.** Başlık 11 sözcük (sınır 15 ✓), özet 190
      sözcük (150–250 ✓), 5 anahtar kelime (sınır 5 ✓). Kılavuzun o yılki
      sayıları yine de doğrulanmalı.

---

## Kimlik bilgisi

Rapor varsayılan olarak **kimliksiz** derlenir. Şablon açıkça şunu
yasaklıyor: *"kesinlikle kapak sayfası yapmayınız ve kişisel
bilgilerinizi (adınız-soyadınız, okul adı, danışman adı, okul logosu ve
filigranı dâhil) yerleştirmeyiniz."*

Kimlikli sürüm gerekirse `rapor.tex` içindeki şu satırın `%`'i kaldırılır:

```latex
% \kimlikliyazdirtrue
```

Adlar ve kurum `\ekip{...}` / `\kurum{...}` ile zaten tanımlı.

---

## Veri nereden geliyor

Üç kaynak, hepsi tek yönlü — rapor hiçbir sayıyı kendi içinde tutmaz:

| kaynak | ne | üreten |
|---|---|---|
| `../preprint/veri/*.dat` | sahne geometrisi, pilot koşular, tasarım | `scripts/onkayit_veri.py` |
| `veri/cekirdek.dat`, `lundborg.dat`, `crush.dat` | malzeme modeli eğrileri | `scripts/rapor2204_veri.py` |
| `veri/eksen_duyarliligi.dat` | üretim havuzu ölçümü (88/96) | TRUBA, bkz. KAYIT-078 |

Malzeme eğrileri **koddaki formülün kendisinden** hesaplanır ve sabitler
`dartrift`'ten okunur; elle çizilmiş eğri yoktur. Kopya tutulmamasının
sebebi bilinçlidir: kopya, iki sayı kümesinin zamanla sessizce ayrışması
demektir.

---

## Havuz dolduğunda ne değişir

Raporun havuza bağlı her sayısı **tek bir satırdan** okunur
(`rapor.tex`, `\havuzBiten`). Gövdede altı yerde elle yazılıydı; biri
atlanırsa rapor kendi kendisiyle çelişiyordu. Sıra şudur:

1. `python scripts/uretim_posterior.py` — ölçümleri yeniler: Spearman
   korelasyonları, Fisher öz değerleri, $n_{\text{yön}}$, kaçış eşiği
   koşu sayısı, $\beta$ gelenek oranının ortancası.
2. `rapor.tex` içindeki `\newcommand{\havuzBiten}{88}` → yeni sayı.
   **Yalnız bu satır**; gövdeye dokunulmaz.
3. `veri/eksen_duyarliligi.dat` başlığındaki `88/96` ve tarih —
   kaynak künyesi, elle güncellenir.
4. `make` — iki geçiş; sonra `pdftotext rapor.pdf - | grep -c 88` ile
   eski sayının kalmadığı denetlenir (yarı eksen `88,5` hariç).

`\havuzToplam` **kilitli tasarım boyudur** (ADR-0053 S4, lhs 96) ve
havuz eksik kalsa bile düşmez: rapor bulduğunu değil beklediğini sayar.

---

## Şekiller

| # | dosya | ne gösterir |
|---|---|---|
| 1 | `dejenerasyon` | tek skalerin ters görüntüsü bir nokta değil koridor; Fisher elipsi |
| 2 | `cekirdek` | Wendland C2 ağırlık fonksiyonu + komşuluk |
| 3 | `malzeme` | $Y_0$ ve $\alpha_b$ fiziğe nereden giriyor |
| 4 | `hedef` | sabit sahne, $z=0$ kesiti, bloklar ve incelme kabukları |
| 5 | `kaskad` | benzetimin kapsadığı ve kapsamadığı zaman aralığı |
| 6 | `tasarim` | kilitli 96 + 12 iç içe tasarım |
| 7 | `kapilar` | beş ön kayıtlı karar kapısı ve düşme dalları |
| 8 | `bulgular` | beş pilot koşu, dört gözlenebilir |
| 9 | `atlas` | bağdaşım–momentum manzarası |
| 10 | `duyarlilik` | ölçülen her kaldıraç tek ölçekte |
| 11 | `eksen` | **hangi gözlenebilir hangi ekseni görüyor** |

Hepsi vektör (TikZ/pgfplots), hiçbiri elle çizilmedi. Yazı tipi gövde
metniyle aynı; ondalık ayracı her yerde virgül.

---

## Ön baskıdan farklar

| | ön baskı | 2204 raporu |
|---|---|---|
| dil | İngilizce | Türkçe |
| düzen | iki kolon, dergi | tek kolon A4, tek aralık |
| şekil | 7 | 11 |
| kimlik | yazar adları + ORCID | gizli |
| $\beta$ geleneği | çarpıcı | **fırlatı** (ADR-0060) |

Ön baskının kaynakları **değiştirilmedi**. O metin DOI ile yayımlandı ve
yatırılan dosyayla bayt bayt aynı tutuluyor.

> **Dikkat:** ön baskıda *"iki izdüşüm arasındaki açıyı vermiyoruz"*
> yazıyor. Bu cümle ADR-0060 ile **yanlışlandı** — asıl terim yörünge
> geometrisine değil kendi fırlatı alanımıza bağlı ve ölçüldü
> (ortanca 1,166). Rapor düzeltilmiş hâli taşıyor; ön baskı Paper II'de
> güncellenecek.

---

## Raporun iddia ettikleri ve etmedikleri

**İddia edilen** (ölçülmüş, 88/96 kısmi havuz):

* $\beta$ pratikte tek bir koordinat taşıyor:
  $\rho(\beta,\log Y_0) = -0{,}983$, diğer iki eksenle $\approx 0$.
* Çarpmanın kazandırdığı spin, $\beta$'nın kör olduğu eksenleri görüyor;
  $r(\beta,\omega) = +0{,}131$.
* $\beta$'nın izdüşüm geleneği düzeltildi; fark ortanca `1,166`.

**İddia edilmeyen:**

* $(\alpha_b, Y_0, f)$ için nokta tahmini ya da güven aralığı.
* Hera için sayısal, mühürlü öngörü.
* Çözünürlük yakınsaması.

Gerekçeler raporun *Geçerlilik sınırları* bölümünde ve
`docs/truba/PROTOKOL-*.md` kilitli protokollerinde yazılı.

Havuz tamamlandığında eklenecek tek şey mühürlü $n_{\text{yön}}$
ölçümüdür; boru hattı hazırdır
([`scripts/uretim_posterior.py`](../../scripts/uretim_posterior.py)).
