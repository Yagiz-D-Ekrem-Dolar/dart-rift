# KAYIT-093 — 2204-A kuralları resmî belgeden denetlendi; **özet bayat çıktı**

**Tarih:** 2026-11-01 · **Sıfır GPU** · **Sıfır TRUBA**
**Öncül:** [KAYIT-092](KAYIT-092_2026-11-01_doluluk-hipotezi-CURUDU-muhur-atildi-gec-dokum-gonderildi.md)
**Çıktılar:** [`docs/yarisma/TUBITAK-2204A-KURAL-DENETIMI.md`](../yarisma/TUBITAK-2204A-KURAL-DENETIMI.md),
[`SAVUNMA-NOTU.md`](../yarisma/SAVUNMA-NOTU.md),
[`YAPAY-ZEKA-BEYANI.md`](../yarisma/YAPAY-ZEKA-BEYANI.md)

---

## 1. Tek cümle

`DEVAM-BITIS3.md` §6.8'in *"İSEF/TÜBİTAK kural ve tarih kontrolü"* maddesi
bir yıldır açıktı; resmî iki PDF (Çağrı Duyurusu 2027 + Proje Rehberi
2027) okundu ve rapor bunlara karşı denetlendi. **Denetim bir kusur
yakaladı:** proje özeti projenin **eski** hâlini anlatıyordu.

## 2. Niçin bu iş önemliydi — eleme sebepleri sayıldı

Çağrı Duyurusu *"hangi aşamada olursa olsun yarışmadan elenir"*
ifadesini **on bir ayrı maddede** kullanıyor. Bu projeyi doğrudan
ilgilendiren dördü kural denetimi belgesinde §1'de. En ağırı:

> **4.2.9** — MEB'e bağlı olmayan kurumlarda yapılan projeler için o
> kurumdan **izin belgesi** alınmalı ve sisteme yüklenmelidir.
> **4.1.12** — gerekli iznin gerekip gerekmediği *"tamamen proje
> sahiplerinin sorumluluğundadır"*; jüri eksik bulursa **elenir**.

Bütün üretim koşuları TÜBİTAK ULAKBİM TRUBA'da, **ortak bir hesapta**
yürütüldü. **İzin belgesi alınmadı.** Bu, bugün projenin en büyük
yarışma riski ve kod/fizik işi değil, **yazı işi** — kurum yazısı zaman
alır, son başvuruya bırakılamaz.

İkinci sıra **4.1.11**: hiçbir belgede kurum/firma/marka **öne
çıkarılamaz** → elenir. Rapor sayıldı: `NASA` ×2 (araştırmanın konusu),
`TÜBİTAK ULAKBİM TRUBA` ×2, `NVIDIA H100` ×4, `Claude (Anthropic)` ×2 —
**hepsi** yöntem, Ek 3 ve yapay zekâ beyanı bölümlerinde, olgusal; proje
başlığında marka **yok**, logo **yok**. Proje Rehberi §3.3 zaten *"hangi
araç ya da yazılımları kullandığınız"* ve *"çalışılan laboratuvarın
özellikleri"*ni **zorunlu** tutuyor. Yasak "öne çıkarma", "anma" değil —
bugünkü hâl korunmalı, yeni marka adı **eklenmemeli**.

## 3. **Özet bayat çıktı** — eski metin burada duruyor (kural 5)

Sert sayılar denetlenirken görüldü: özet `177` kelimeydi, sınıra
uyuyordu, ama **projenin eski hâlini** anlatıyordu — *"Sabit bir çarpma
sahnesinde geçerliliği denetlenmiş **beş** benzetim tamamlanmıştır"*.
Oysa havuz `96/96` kapanmış, `n_yön = 1` kilitlenmiş, tarih eşlemesi
`%34` vermiş, SBC geçmiş ve **iki ön kayıt mühürlenmişti**. Jürinin ilk
okuduğu metin buydu.

Özetin **250 kelime sert sınırı** var, dolayısıyla düzeltme NOT olarak
eklenemezdi. Metin yenilendi; eskisi **silinmedi, buraya taşındı**:

> Amerika Birleşik Devletleri Ulusal Havacılık ve Uzay Dairesi'nin (NASA)
> DART görevi 2022'de Dimorphos asteroidine çarparak yörünge dönemini
> ölçülebilir biçimde değiştirmiş ve cisme aktarılan momentumu `β`
> katsayısıyla sınırlamıştır. Bu tek sayıdan cismin iç yapısını geri
> okumak doğrudan bir ters problem değildir: yakın tarihli çalışmalar
> birbirinden farklı iç yapıların aynı `β` değerini ürettiğini
> göstermiştir. Bu projede çarpma, grafik işlem birimi (GPU) üzerinde
> düzgünleştirilmiş parçacık hidrodinamiği ile modellenmiş ve üç iç yapı
> koordinatının — blok gözenekliliği, matris bağdaşım dayanımı ve blok
> hacim kesri — gözlemden ne kadarının öğrenilebildiği sorusu, bir nokta
> tahmini yerine tanımlanabilirlik sorusu olarak kurulmuştur. Sabit bir
> çarpma sahnesinde geçerliliği denetlenmiş beş benzetim tamamlanmıştır.
> Bağdaşım dayanımı 10 Pa'dan 5000 Pa'ya çıkarıldığında `β` 3,7480'den
> 1,8738'e düşmekte, fırlatılan kütle 26,1 kat azalmaktadır. Denenen
> matris çekme yasasının açılması fazla momentumu %97,1 değiştirmekte;
> çarpma noktasının 25 m kaydırılması ise `β`'yı yalnız %2,2
> değiştirirken fırlatı kütlesini %18 değiştirmektedir. Ölçülen tüm
> etkiler tek ölçekte sıralandığında en büyüğü, çıkarılmak istenen
> koordinatlardan değil, kararla sabitlenen bir model seçiminden
> gelmektedir. Üretim çıkarımının tasarımı, olabilirlik tanımı ve beş
> karar kapısı veriye bakılmadan önce yazılıp tarih damgasıyla kayda
> alınmıştır.

**Eski metindeki sayılar yanlış değildi** — pilot koşunun gerçek
ölçümleriydi (KAYIT-063 dönemi) ve ön baskıda yerleri duruyor. Kusur
sayılarda değil, **kapsamdaydı**: özet artık raporun anlattığı çalışmayı
anlatmıyordu.

### 3.1 Yeni özet ve ölçümü

| ne | eski | yeni | sınır |
|---|---:|---:|---|
| kelime | 177 | **190** | 150–250 (Çağrı 4.2.4) |
| sayfa (rapor) | 20 | **20** | en az 2, **en fazla 20** |
| LaTeX hatası | 0 | **0** | — |

İlk yenileme `218` kelime oldu ve raporu **`21` sayfaya** taşırdı —
yani **şekilsel ön incelemede eleme** demekti. Sıkıştırıldı, yeniden
derlendi, `20` sayfada ölçüldü. Yeni özet şunları taşıyor: `96/96`
havuz, `n_yön = 1`, büzülme `0,882`, `%34` bağdaşır hacim, SBC, ve
**dürüst sınır** (`×3,22` çözünürlük yanlılığı → *"niceliksel öngörü
değil yöntem gösterimi"*), ve iki mühürlü Hera öngörüsü.

> **Ders.** Rapor gövdesi aylarca güncellendi, özet güncellenmedi.
> Jürinin **ilk** okuduğu metin en seyrek bakılan metindi. Sayfa sınırı
> denetlenmeseydi bu da görülmeyecekti — sert sayıları saymak, içeriği
> de denetledi.

## 4. Sert sayılar — hepsi ölçüldü

| kural | madde | sınır | bizde |
|---|---|---|---|
| rapor sayfası (tüm başlıklar dâhil) | 4.2.4 | 2–**20** | **20** ✓ |
| özet | 4.2.4 | 150–250 kelime | **190** ✓ |
| proje adı | 4.2.6 | ≤ 15 kelime | **11** ✓ |
| dosya | 4.2.4/4.2.5 | tek PDF, ≤ 10 MB, ad ≤ 25 karakter | `rapor.pdf`, 1,1 MB, 9 ✓ |
| dil | 4.2.4 | Türkçe | Türkçe ✓ |
| ana / tematik alan | Tablo 1 / 2 | listeden | **Fizik** / **Astronomi ve Astrofizik** ✓ |
| sözlü sunum | Rehber §1.4 | **en fazla 10 dakika** | iskelet hazır ✓ |

**Açık kalan tek sert kural:** 4.2.4 raporun resmî *"Proje Yazım
Şablonu"* ile hazırlanmasını istiyor; şablon ayrı bir dosya ve Çağrı
Duyurusu'nun içinde değil. İndirilip başlıklar eşlenmeli.

## 5. Yapay zekâ — iki resmî belge de **sessiz**

Arandı: *"yapay zekâ"* sözü Proje Rehberi'nde yalnız bir **tematik alan
adı** ve konu anlatımı olarak geçiyor; **araç kullanımına dair tek kural
yok**. Çağrı Duyurusu'nda hiç geçmiyor. Yani açık bir yasak da, açık bir
beyan zorunluluğu da yok.

Ama **4.1.7** ve Rehber §2.3 şunu istiyor: proje *"danışarak ama **kendi
bilgi ve becerileri** ile"* tamamlanmış olmalı, *"Proje, öğrenci
tarafından yapılmalıdır"*, *"konu uzmanından gereğinden fazla yardım
alınmamalıdır"*. Bu ölçüt sözlü sunumda **jüri tarafından sınanacak**.
Beyan **zaten raporun içinde** (§"Yapay Zeka Araçları Kullanım Beyanı")
ve bu oturumda ayrıntılı hâli yazıldı.

## 6. Kilitli yargılara etkisi — YOK

Bu kayıt bir **yarışma uyumu** kaydıdır. Hiçbir ölçüm, hiçbir protokol,
hiçbir mühür değişmedi. Mühürlü `uretim66` ve `uretim96` dosyalarına
**dokunulmadı**; SHA-256'ları tutuyor.
