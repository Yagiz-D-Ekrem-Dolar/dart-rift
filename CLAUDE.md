# DART-RIFT — Claude çalışma kılavuzu

Bu dosya her Claude Code oturumunda otomatik okunur (hesaptan bağımsız).
**Yeni oturumda önce [`docs/DEVAM-BITIS3.md`](docs/DEVAM-BITIS3.md) oku** —
durum, plan, geçmiş, riskler ve öğrenilen dersler orada.

## Proje

DART çarpışmasını GPU'da (NVIDIA Warp) SPH ile modelleyip Dimorphos'un iç
yapı parametrelerini — `θ = (α_b blok gözenekliliği, Y₀ matris dayanımı,
f blok kesri)` — gerçek DART gözleminden (momentum aktarımı `β`) çıkarmak:
**Bitiş 3**. Ardından Hera için mühürlü krater öngörüsü (Protokol HT).

## Kullanıcıyla çalışma

- **Türkçe konuş.** Kullanıcı kesintisi = dur.
- Bilimsel durumu dürüst anlat; garanti verme, sayı uydurma.
- `main` dalına commit + push serbest.
- Kullanıcı projeyi İSEF/TÜBİTAK'ta sunmayı düşünüyor: kararlar ve kod
  kullanıcının savunabileceği biçimde açıklanmalı.
- Kısa, gündelik Türkçe yazar ("kanka", "devam"); önce net özet ister; yüzde,
  takvim, "başaracak mıyız" sorar → dürüst aralık ver, varsayımı yaz.
- **Son yazışmalar, verilen cevaplar ve kullanıcıdan bekleyen kararlar:**
  `docs/DEVAM-BITIS3.md` §12 — aynı soruları yeniden sorma.
- Yapay/boş commit atılmaz (kullanıcı commit sayısını sordu; reddedildi, §12.4).

## Değişmez kurallar

1. Parola/anahtar **asla** commit'e, belgeye, ekrana yazılmaz (TRUBA
   belgelerinde düz metin parolalar var).
2. TRUBA hesabı **ortak**: aynı anda **en fazla 8 GPU** (çalışan + bekleyen);
   kuyruğa yığın iş yok, biri bitince diğeri — `scripts/sirali_gonderici.py`.
3. `ardababatrubamcpi` MCP'si **kullanılmaz**. Toplu `scancel`/iptal gibi
   yıkıcı işlemlerden önce kullanıcıya sor.
4. `/arf`'a pip/conda kurulumu **yasak** (paketler `pylib/` altında açılmış wheel).
5. **"Hiçbir satır silinmez"**: belgelerde düzeltme NOT olarak eklenir.
6. Kilitli protokoller (`docs/truba/PROTOKOL-*.md` + betikleri) **koşudan
   önce** yazılır; sonuç gelince kural değişmez — düzeltme "yan yana" alan
   olarak eklenir (ör. A85 `*_yamuk`, A88 `kesin`/`tam`).
7. Yeni dosya yazmadan önce adın **boş** olduğunu kontrol et (Write üzerine
   yazar; bir kez kilitli betik ezildi).
8. Her rapor **bulduğunu değil beklediğini** sayar (A84/A88): eksik kampanya
   sessiz geçmez.

## Geliştirme ortamı (Windows)

- Depo `C:\Users\yagiz\Desktop\videos\dart-rift`; Python `.venv\Scripts\python.exe` (3.12).
- Lint: `python -m ruff check scripts src tests` → **0 ihlal** tutulur.
- Sınav: `python -m pytest -m "not gpu" -q` (~2100 sınav, 18–25 dk).
- bash sınavları Git Bash ister (WSL `System32\bash.exe` Windows yolunu bozar).
- PowerShell 5.1: commit mesajında çift tırnak git'i bozar → `git commit -F dosya`.
- ruff B007 döngü **sonrası** kullanımı görmez — yeniden adlandırmadan önce grep.

## TRUBA kısa

- Kuyruk `kolyoz-cuda` (H100), GPU başına 16 çekirdek, modül `apps/truba-ai/gpu-2024.0`.
- İş betikleri `truba/is_*.slurm`; çalışma alanı yolu sabit `egitimg16u1`
  yazılı → plan JSON'unda `"kok"` ile değiştirilir.
- Shell'siz MCP ile gönderim: `sirali_gonderici.py betikler` → üretilen
  betikleri tek tek gönder → `kaydet`. Ayrıntı: DEVAM-BITIS3 §4.
- `# ZORUNLU_EXPORT:` satırı olan betiğe bütün değişkenler verilir
  (ör. `is_N_genel`: 24 ms'de bile `T_END=0.024 SAHA=matris`).

## Belge haritası

| belge | ne |
|---|---|
| `docs/DEVAM-BITIS3.md` | **devir notu**: durum, plan, bütçe, riskler, dersler |
| `docs/BITIS3-DURUM.md` | bilimsel durum (keşif) |
| `docs/FAZ4-SIKINTI-RAPORU.md` | kusur kayıtları A1–A88 (sayaçları sınavlı) |
| `docs/truba/PROTOKOL-{Q,D,U,V,HT}-*.md` | kilitli karar kuralları |
| `docs/SONUC-M-N-P-J-T.md` | kilitli sonuçlar |
| `truba/sira_*.json` | TRUBA sıra planları |
