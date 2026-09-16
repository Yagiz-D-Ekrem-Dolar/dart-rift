# KAYIT-056 — YağızTRUBA kuruldu; U'dan önce duman sınavı (2026-09-16)

**Kapsam:** Bitiş 3 / Protokol U hazırlığı · **Durum:** kurulum doğrulandı,
duman sınavı kuyrukta · **Öncül:** [`docs/DEVAM-BITIS3.md`](../DEVAM-BITIS3.md),
[`PROTOKOL-U-MODEL.md`](../truba/PROTOKOL-U-MODEL.md), sıkıntı kayıtları A84–A88

---

## 0. Neden yeni kurulum

14 Eylül'de TRUBA işlerinin çoğu iptal oldu; Protokol U'nun 20 görevinin
**hiçbiri koşmamıştı**. Eski çalışma alanlarına (`egitimg16u4`, `egitimg16u1`)
erişim kalmadı. Kullanıcı kendi MCP bağlayıcısını kurdu (**YağızTRUBA**) ve iki
karar verdi:

- GPU sınırı **8 → 20** ("8 GPU fazlası da olur, 20'ye kadar okey").
  Kuyruğa yığmama kuralı değişmedi (görev görev, boş yuva kadar).
- "Tüm güç senin; bütün U serisini koştur, hatasız ve kusursuz; her şeyi defterle."

## 1. Keşif (yalnız okuma)

| soru | ölçülen |
|---|---|
| kullanıcı / Slurm hesabı | `egitimg16u3` / `egitimg16` (yine **ortak** grup), QoS `normal` |
| eski alanlar | u4 ve u1 `driftclaude`: **Permission denied** → eski havuzlar okunamaz (U'nun onlara ihtiyacı yok) |
| giriş düğümleri | varsayılan `arf-ui1` (CPU); GPU için `cuda-ui` |
| `kolyoz-cuda` | 47 dolu, 4 karışık, 1 boş düğüm (yoğun) |
| modül `apps/truba-ai/gpu-2024.0` | ortam Python **3.10.15**, numpy **1.26.4**, h5py 3.12.1, pydantic 2.9.2, PyYAML 6.0.2, pytest 8.3.5; **warp YOK** |
| tuzak | modül yüklense bile çıplak `python` bir kabukta **sistem 3.9.18 / numpy 1.20.1**'e gitti → iş betikleri yanlış Python'la sessizce koşabilirdi |
| GitHub | TRUBA'dan erişilebilir (`git ls-remote` HEAD = yereldeki) |

## 2. Kurulum ve doğrulamalar

| adım | sonuç |
|---|---|
| `warp_lang-1.15.0-py3-none-manylinux_2_28_x86_64.whl` (PyPI, kullanıcı onayıyla) | `166 711 381` bayt, **SHA-256 PyPI özetiyle eşleşti**; `pip install` yok, `pylib/` altına açıldı (`/arf`'a kurulum yasağı) |
| depo klonu | `42e4c68443351fc1bec99d385183c0c8003a3eb7` — beklenen commit, `--ff-only` |
| CRLF | `ortak_bas.sh`, `is_U_model.slurm`, `is_DUMAN.slurm`'de **0** satır |
| kod sabitleme | `$KOK/SABIT_COMMIT` = yukarıdaki commit |
| ortam içe aktarma | `numpy 1.26.4 | warp 1.15.0 | dartrift` klondan |
| TRUBA'da sınav | `test_sirali_gonderici` + `test_kok_uygula`: **19 geçti** |

Warp 1.15.0 bilerek seçildi: 13–14 Eylül kilitli sonuçları TRUBA'da bu sürümle
alındı (yerel dizüstünde 1.16.0 var; tekrarlanabilirlik bölümüne yazılacak).

### `ortak_bas.sh` artık depoda (`truba/ortak_bas.sh`)

Eski kopya yalnız TRUBA'daydı ve hesap değişince **kayboldu**. Yenisi her işin
başında sırayla dener ve ilk saniyede durur:

| kod | koşul |
|---|---|
| 91 | `nvidia-smi` GPU görmüyor |
| 92 | çalışma ağacı kirli ya da `SABIT_COMMIT`'ten farklı |
| 93 | ortam `bin`'i PATH başına konduktan sonra Python 3.10 değil |
| 94 | `numpy`, `warp`, `dartrift` içe aktarılamıyor |

**Bilinçli sapma:** işin başındaki `git pull` **kaldırıldı**. Eskiden bir dizinin
görevleri, kuyrukta beklerken yapılan bir push yüzünden **farklı kodla**
koşabiliyordu. Artık kod sabit; sürüm uymazsa iş 92 ile durur.
Sınav: `tests/test_ortak_bas.py` (Git Bash'le gerçek `source`: `KOK` yoksa ve GPU
yoksa 91).

## 3. Kendi hatalarım (bu kayıt boyunca)

1. **Kurulum betiği sessizce kesilecekti.** `set -euo pipefail` altında
   `grep -c $'\r' ...` eşleşme bulamayınca (beklenen, iyi durum) `1` döner;
   `pipefail` bunu boru hattının sonucu yapar, `set -e` betiği keser. Yani
   kurulum tam **başarılı** olacağı anda yarıda kalacaktı. Çalıştırmadan önce
   fark edildi; `{ grep ... || true; }` ile sarıldı.
2. Devir notuna ekleme yaparken çapa metnini ezberden yazdım (`**` eksik),
   düzenleme tutmadı; kısa ve benzersiz çapayla yeniden yapıldı.

## 4. Duman sınavı (protokol değil, bilimsel veri değil)

`truba/is_DUMAN.slurm`, plan `truba/sira_duman.json`: U0 merkez θ
`(1,15 ; 1e5 ; 0,275)`, kaba, U ile **aynı** üretim bayrakları, `t_end = 3 ms`,
şok kapısı kapalı (amaç yazma yolu). İş sonunda kendi denetimi: JSONL satırı ≥ 1,
`npz` ≥ 1, `beta_hedef` sonlu → yoksa `exit 8`.

| | |
|---|---|
| üretim | `sirali_gonderici betikler` → `kok` u3'e çevrildi; betikte `egitimg16u1` **kalmadı** (gönderim öncesi `grep` denetimi) |
| iş | **`1565202`**, `PENDING (Priority)`, 1 GPU |
| çalışma ağacı | temiz (0 değişiklik) |

## 5. U planı (duman geçerse)

`truba/sira_bitis3_U.json`: `U_kaba` 0–15 (8 varyant × 2 tohum), bitince
`U_orta` 16–19 (U0/U8 × 2 tohum). En fazla 20 GPU → kaba tek turda; üst sınır
`200` GPU-saat, duvar `≤ 20 sa` (kuyruk beklemesi hariç). Yargı kuralı
`u_model_raporu.py`'de kilitli (`|z| ≤ 2`); rapor artık kapsamı (TAM/EKSİK) da yazıyor.

## Sonuç

*(İş bitince bu başlığın altına eklenecek; yukarıdaki satırlar değiştirilmez.)*

### 6.1 İlk duman denemesi düğümde başlatılamadı (`1565202`)

| | |
|---|---|
| belirti | `PENDING (launch failed requeued held)`; `kolyoz9`'da 22:24:17'de başlatıldı, `batch` adımı **1 s içinde** CANCELLED, **çıktı dosyası bile oluşmadı** |
| kod mu? | hayır — `ortak_bas.sh` hiç çalışmadı; `ciktilar/` izinleri doğru |
| düğüm | `kolyoz9` IDLE, sebep yazılı değil; son 12 saatte orada başka düşen iş yok |
| `scontrol release` | TRUBA'nın bilinen tuhaflığı: *"time limit … interactive jobs"* → serbest bırakılamıyor (hold/update ile aynı) |
| tanı işi `1565203` | aynı ayarlar, yalnız `hostname/id/nvidia-smi/ls`, `kolyoz9` dışlanmış → **`kolyoz22`'de hemen COMPLETED**, H100 80GB görünüyor |
| karar | sorun düğüme özgü; tutulan iş serbest bırakılamadığı için U görevleri takılmasın diye `kolyoz9` DUMAN/U/V betiklerinde dışlandı (`b0d5ac8`); `1565202` iptal, durum dosyasında `HATA` |

### 6.2 Duman sınavı GEÇTİ (`1565204`)

| | |
|---|---|
| düğüm / süre | `kolyoz22`, kuyrukta ~20 s, `00:01:14` (sürücü duvarı `65 s`; warp çekirdek derlemesi ~`18 s`) |
| `ortak_bas` | `H100 80GB HBM3`, `Python 3.10.15`, commit `b0d5ac8…` — dört denetim de geçti |
| Warp | 1.15.0, CUDA Toolkit 12.9, sürücü 13.0 |
| çıktı | JSONL `1` satır, `npz` `1`, `t = 0,003 s`, `beta_hedef = 1,2173`, `N = 16 954` |
| yargı | **DUMAN SONUC: GECTI** |

### 6.3 İki bulgu

1. **`module: command not found`** (`.err`, satır 17): iş kabuğunda `module` tanımlı
   değil, yani betiklerdeki `module load` **sessizce etkisiz**. Koşuya zarar
   vermedi: `ortak_bas.sh` ortam Python'unu PATH'e kendisi koyuyor ve 93/94 ile
   denetliyor. Duman sınavı **bu modülsüz ortamda** geçti; U aynı sınanmış ortamda
   koşsun diye bilerek **dokunulmadı**. İleride temizlenecek bilinen uyarı.
2. **Tasarım dosyasında yarış (kendi kodum, gönderimden ÖNCE bulundu):** U ve V
   betiklerinde aynı varyantın iki tohumu aynı `U_tasarim_<A>.json`'a
   `echo … > "$TAS"` ile yazıyordu. 16 görev aynı anda başlarken biri dosyayı
   sıfırlarken öbürünün python'u okursa boş JSON okuyup düşerdi. Geçici dosya +
   `mv -f` (atomik) yapıldı (`24e513e`); `tests/test_tasarim_yazimi.py` gerçek
   bash'le geçerli JSON ve geçici dosya kalmadığını sınar.

U kampanyasının kendisi: [KAYIT-057](KAYIT-057_2026-09-16_protokol-U-kampanyasi.md).
