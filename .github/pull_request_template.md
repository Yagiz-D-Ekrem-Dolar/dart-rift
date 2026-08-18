## Ne değişti

<!-- Bir iki cümle. -->

## Fiziksel iddia değişti mi?

- [ ] **Hayır** — yalnızca kod/belge/altyapı.
- [ ] **Evet** — hangi iddia, hangi yönde:

> Fiziksel bir iddia değiştiyse ve o iddia bir ADR'de kilitliyse,
> `docs/adr/` altında bir ADR **zorunludur**. RULES.txt: kilitli karara
> sessiz değişiklik yok.

## Kanıt

| soru | cevap |
|---|---|
| Hangi test eklendi/değişti? | |
| Hangi ölçüm koşuldu? (iş numarası, makine) | |
| Ölçüt **veriye bakılmadan** mı yazıldı? | |
| Kanıt nereye yazıldı? (`docs/defter/`, `docs/evidence/`) | |

## Kontrol listesi

- [ ] `ruff check src tests scripts` temiz
- [ ] `pytest tests -m "not gpu"` geçiyor
- [ ] GPU yolu değiştiyse CPU↔GPU çapraz kontrolü koşuldu
- [ ] Bir modül testini geçemediyse **başarı iddia edilmedi**
- [ ] Yanlış çıkan önceki bir iddia varsa **silinmedi, notla düzeltildi**

## Bilerek yapılmayanlar

<!-- Kapsam dışı bıraktıklarını yaz; sessizce daraltma. -->
