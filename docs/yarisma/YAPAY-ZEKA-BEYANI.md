# Yapay zekâ kullanım beyanı — DART-RIFT

**Tarih:** 2026-11-01 · **Depo:** <https://github.com/> (kalıcı public)
**Bu beyan jüriye sorulmadan verilir.**

---

## 1. Kısa beyan (yarışma formuna yazılacak hâli)

> Bu projenin kaynak kodunun büyük bölümü, araştırmacının yönlendirmesiyle
> çalışan bir büyük dil modeli (Anthropic Claude, Claude Code aracı)
> tarafından yazılmıştır. Araştırmacı; problemi tanımlamış, fizik ve
> çıkarım kararlarını onaylamış, hesaplama kaynağını (TÜBİTAK ULAKBİM
> TRUBA) yönetmiş, her koşunun sonucunu değerlendirmiş ve neyin
> yayımlanacağına karar vermiştir. Bütün yazışma geçmişi, karar kayıtları
> (ADR), çalışma defteri (KAYIT) ve kusur kayıtları depoda açıktır;
> hangi kararın kim tarafından verildiği izlenebilir.

## 2. Ayrıntılı dökümü — ne, kim

| iş | kim | kanıt |
|---|---|---|
| Problemin seçimi ve bilimsel soru | **araştırmacı** | `docs/FIZIBILITE.md`, `docs/BETA-HEDEFI.md` |
| Fizik modeli seçimi (SPH + Tillotson + P–α + Grady–Kipp + Lundborg) | dil modeli önerdi, **araştırmacı onayladı** | `docs/adr/` karar kayıtları |
| Kodun yazımı (`src/` 26 916 satır) | **ağırlıklı olarak dil modeli** | git geçmişi |
| Sınavların yazımı (`tests/` 32 256 satır) | **ağırlıklı olarak dil modeli** | git geçmişi |
| Kilitli protokollerin yazımı | dil modeli yazdı, **koşudan önce** araştırmacı onayladı | `docs/truba/PROTOKOL-*.md` |
| Hangi koşunun gönderileceği, kaç GPU | **araştırmacı** (açık sınır: en çok 20 GPU) | `CLAUDE.md` kural 2 |
| Sonuçların yorumu ve yayım kararı | **araştırmacı** | `docs/defter/KAYIT-*.md` |
| Olumsuz sonuçları yayımlama kararı | **araştırmacı** | S9/S10/S11/S12 düşük olarak duruyor |

## 3. Dil modelinin **hata yaptığı** ve düzeltildiği yerler

Bu bölüm beyanın en önemli parçasıdır: dil modeli yanılmıştır ve
yanılgıları depoda yazılıdır.

| hata | nasıl yakalandı | kayıt |
|---|---|---|
| Krater operatörü `nan` yerine **yanlış sayı** döndürecekti (47 nokta) | sentetik levhada ölçüm, bağıntı `−(y + 0,913)` çıktı | [KAYIT-089](../defter/KAYIT-089_2026-10-27_ADR-0061-tek-basina-30-nani-30-yanlis-sayiya-cevirecekti.md) |
| "SPH birim bölünmesi bozuluyor" açıklaması | 96 noktada sayıldı, `AUC = 0,203` ile **ters** çıktı | [KAYIT-092](../defter/KAYIT-092_2026-11-01_doluluk-hipotezi-CURUDU-muhur-atildi-gec-dokum-gonderildi.md) §3 |
| `kos` fonksiyonu hatası → dört bulgu | sınav eklendi, bulgular **geri çekildi** | [KAYIT-082](../defter/KAYIT-082_2026-10-16_kos-hatasi-ve-duzeltilmis-sonuclar.md) |
| Havuzun yarısını kaybedecek kusur (A114) | koşmadan **önce** yakalandı | `docs/FAZ4-SIKINTI-RAPORU.md` A114 |
| İki ayrı krater çıkarıcısı karıştırıldı (30/96 ≠ 47/96) | KAYIT-088'e düzeltme NOT'u eklendi | [KAYIT-088](../defter/KAYIT-088_2026-10-22_A86-kok-sebep-tepe-ortak-alininca-referans-yuzey-kaciyor.md) |
| Commit mesajı araç hatasıyla bozuldu | KAYIT-091 §11'de düzeltildi | `1ac1ddd` |

**Toplam kusur kaydı: 114 · açık: 87.** Kusurlar silinmiyor, kapandıkça
kapalı işaretleniyor (`CLAUDE.md` kural 5: "hiçbir satır silinmez").

## 4. Dil modelinin **yapmadığı** şeyler

- Hiçbir sayıyı uydurmadı; her sayının bir ölçüm dosyası var
  (`docs/sonuclar/*.csv`, `docs/olcumler/`).
- Sonuç görüldükten sonra hiçbir kural değiştirilmedi: protokoller
  koşudan **önce** commit'lendi ve commit tarihleri bunu gösterir.
- Mühürlü ön kayıtlar (`docs/onkayit/`) SHA-256 ile çivili; Hera verisi
  geldiğinde değiştirilemez.

## 5. Araştırmacının savunması niçin geçerli

Araştırmacı kodu satır satır yazmadı. Savunması şuna dayanır:

1. **Her modülü ne yaptığı ve niçin orada olduğuyla anlatabilir**
   → [`SAVUNMA-NOTU.md`](SAVUNMA-NOTU.md) §3.
2. **Her sayının nereden geldiğini gösterebilir** → aynı belge §4.
3. **Projenin neyi başaramadığını kendisi söyler** → aynı belge §2.
4. **Yöntemin niçin bu biçimde kurulduğunu savunabilir** (önceden
   kilitleme, mühürleme, olumsuzu yayımlama) → aynı belge §5.

Jüri "bu kodu sen mi yazdın" diye sorarsa doğru cevap §6'daki tek
cümledir ve kaçamak değildir.

## 6. Jüriye söylenecek tek cümle

> Kodu büyük ölçüde bir dil modeline yazdırdım; kurguyu, kararları ve
> neyin yayımlanacağını ben belirledim. Modelin yanıldığı yerleri de
> depoya yazdım — üç tanesini size şimdi anlatabilirim.

Bu cümle, modelin çürütülen hipotezini ([KAYIT-092](../defter/KAYIT-092_2026-11-01_doluluk-hipotezi-CURUDU-muhur-atildi-gec-dokum-gonderildi.md)
§3) anlatmaya hazır olmayı gerektirir. Hazırlığı
[`SAVUNMA-NOTU.md`](SAVUNMA-NOTU.md) §6'da.
