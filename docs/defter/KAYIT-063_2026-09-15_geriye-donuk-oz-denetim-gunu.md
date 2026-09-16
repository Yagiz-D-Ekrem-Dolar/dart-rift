# KAYIT-063 — TRUBA'sız öz denetim günü: "rapor bulduğunu değil beklediğini sayar" (2026-09-15)

**Kapsam:** Bitiş 3 hazırlığı · **Durum:** GERİYE DÖNÜK yazıldı (2026-09-16) ·
**Kaynak:** [`FAZ4-SIKINTI-RAPORU.md`](../FAZ4-SIKINTI-RAPORU.md) A87, A88;
[`DEVAM-BITIS3.md`](../DEVAM-BITIS3.md) §8, §11, §12; commit geçmişi
(`790fdcd` … `8d5f89d`) · **Öncül:** [KAYIT-062](KAYIT-062_2026-09-14_geriye-donuk-orta-iki-eksen-dart-onsel-disi-protokoller.md)

---

## 0. Neden TRUBA'sız

İkinci bağlanan MCP `egitimg16u5` olarak açıldı: u4 "base dir dışı", u1 izin yok,
u5'te proje verisi yok, shell yok → **hiçbir şey gönderilmedi**. Kullanıcı:
"kod yazmadan kendi hatalarını tespit et, sorunları gider." Gün, koşmamış ama
koşacak kodun denetimine gitti.

## 1. Kendi hatalarım

| kayıt | hata | nasıl bulundu | etki |
|---|---|---|---|
| **A87** | A85'in yamuk düzeltmesi uç düğümleri **ikinci kez** yarılıyordu (`F(0) = p₀/4`) | P raporuna aynı hesabı yan yana eklerken yazdığım yeni sınav: 21 düğümlü düz dağılımda `%2,5` sınırı `0,025` yerine **`0,0167`** | kilitli yargıya girmemişti (D hiç koşmadı); `cumsum(p) − p₀/2 − p/2`, `/F[-1]`; üç yerde düzeltildi |
| — | `kacis.py`'de ruff B007'ye güvenip `tur → _tur` | `test_kacis` **11 sınavla** düştü (değişken döngü sonrası kullanılıyordu) | commit'ten önce geri alındı; ders: yeniden adlandırmadan önce grep |
| — | sınavda boş iddialar (`"import" in m`, M2 kesinliğinde yalnız etiket geçerliliği) | kendi sınavımı okurken | bağımsız kâhinli sınavla değiştirildi; AST taraması: `tests/` altında başka yok |
| — | PowerShell commit mesajında çift tırnak | `git` pathspec hatası; commit olmadı | `git commit -F dosya` |

## 2. A88 — kısmi kampanya sessizce sonuca giriyordu (KAPANDI)

14 Eylül iptali kısmi veri bırakacaktı. Denetlenen her toplayıcıda aynı kalıp:

| yer | risk | çare (kural aynı, eksik **yazılır**) |
|---|---|---|
| `cozunurluk_hatasi` | kısmi Mt'den `σ_çöz`, D/HT'ye tam havuz gibi | `kapsam_denetle` + ortak `oku()` → "EKSİK HAVUZ" |
| `u_model_raporu` | düşen varyant tabloda hiç görünmeden "HİÇBİR VARYANT ULAŞMIYOR", V gönderilir | `BEKLENEN` (U 20, V 10) + `tam/eksik`; V kararı eksik U ile verilmez |
| `m_yakinsama_raporu`, `m2_kontrast_raporu` | OKUNMAZ θ kararı "YAKINSAMIYOR/DAYANIKSIZ"a kaydırıyor; Q §4 esas havuzu buna göre seçiyor | `kesin` alanı; `bitis3_raporu` kesin değilse "EKSİK", esas havuz seçilmez |
| `is_V_model.slurm` | `${V4_U:-U0}` ve `[ -f ] &&` → V4 sessizce yanlış θ | `V4_U` zorunlu (exit 2), dosya yok exit 3 |
| `is_N_genel`, `is_Pgen_rapor` | `T_END` unutulursa 24 ms; `BEKLENEN_*` verilmezse A84 denetimleri atlanıyor | `# ZORUNLU_EXPORT:`; exit 2/4/5 |

**16 Eylül'de sahada doğrulandı:** U ara raporu gerçek veride "KAPSAM: EKSİK (8)
… V kararı verilmez" yazdı (KAYIT-057).

## 3. Kullanıcı kurallarını koda dökmek

- **`scripts/sirali_gonderici.py`**: çalışan + bekleyen GPU sayımı (COMPLETING
  dahil), boş yuva kadar tek görev, adım zinciri, HATA'da durma, A84 virgül reddi;
  shell'siz MCP için `betikler` (tek-görev betiği; export'lar son `#SBATCH`'ten
  sonra; `HAZIRLANDI` sayılır) ve `kaydet`; `kok_uygula` (sabit u1 yolu → yeni
  alan, CRLF temiz); `butce` (U: ≤ 200 GPU-sa).
- **Gözlem önbelleği anahtarında eksik bağımlılık:** `crater_shape` →
  `cpu_reference.sph_ref` → `adaptive_h` anahtarda yoktu; çekirdek değişse krater
  gözlemleri eski okunurdu. AST kapanış sınavı eklendi.
- Depo kendi ruff kurallarıyla **0 ihlal**; bash sınavları WSL kısayolunu atlıyor.
- Denetlenip **temiz** çıkanlar: eksen sırası (S3 ↔ EKSENLER), HT/D σ
  tutarlılığı, `gozlenen_beta` birimi, U bayraklarının çözücüye ulaşması
  (üretim `μ_f 0,6, Pe 1e6, Ps 1e8`).

## 4. Devir

Kullanıcı başka Claude hesabına geçeceğini söyledi → `CLAUDE.md` (hesaptan
bağımsız otomatik okunan kurallar) ve `docs/DEVAM-BITIS3.md` (durum, plan, GPU
bütçesi, riskler, dersler, yazışmalar §12) depoya kondu; `scripts/gpu_saat.py`
(`sacct` toplayıcı; türlü/türsüz GPU iki kat sayılmaz).
