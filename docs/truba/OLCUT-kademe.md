# ÖLÇÜT — Ara basamak şoku duvarın ötesine geçiriyor mu? (koşudan **önce**)

**Tarih:** 2026-08-29 · **Öncül:** rapor A25 · **Araç:** `scripts/kademe_sinavi.py`

---

## 1. Soru

A25 ölçtü: `λ₂ = 20`'de ince parçacık `46,6 kg`, hemen dışındaki
`372 834 kg` — **arayüz oranı `8 000`** — ve cephe orada
**`0,0 m/s`** ile duruyor. Mekanizma önerisi: şok, kendisinden
`8 000` kat ağır parçacıklara momentum veremiyor.

Bu, `μ = 80`'in (KAYIT-053) aynısı. Ama **öneri**; sınanmadı.

## 2. Hipotez

> **H3:** Cephe, arayüz oranı düşürülürse duvarı **aşar**.

Kademeli inceltmenin tamamını kurmak büyük iş. Ama üç seviyeli yol
(`refine_scene_ucseviye`) zaten **bir ara basamak** ekliyor ve
depoda hazır — mekanizma onunla, **ucuza** sınanabilir.

| şema | basamaklar | **en dik** |
|---|---|---|
| bugün (tek basamak) | `0,35 -> 7,0` | **`8 000`** |
| üç seviyeli `λ₂ = 8` | `0,35 -> 0,875 -> 7,0` | `512` |
| **üç seviyeli `λ₂ = 4`** | `0,35 -> 1,75 -> 7,0` | **`125`** |

`λ₂ = 4` iki basamağı **dengeliyor** (`125` ve `64`); `λ₂ = 8`
ikinciyi `512`'de bırakıyor. En dik basamağı en aza indirmenin yolu
dengelemek — bu yüzden `λ₂ = 4` seçildi, `8` değil.

## 3. Düzenek

| | |
|---|---|
| ortak | `λ₁ = 20`, `r₁ = 3 m`, `t_end = 4,767e-3 s` |
| **kıyas** | A25'in ölçtüğü tek basamaklı koşu (cephe `3,41 m`) |
| **sınav** | `λ₂ = 4`, `r₂ = 12 m` (en dik `125`) |

**Aktarım devrede değil** — tek aşamalı koşu. Ölçülen şey yalnızca
**kademe**.

## 4. Yargı (kilitli)

Cephe, `x_referans`'tan ve çarpma noktası **dışarıdan** verilerek.

**H3 geçer** ⟺ cephe `> 3,15 m` (ince bölge sınırının `%105`'i)
**ve** şoklanan kütle tek basamaklı koşunun (`72 936 kg`)
**iki katından** fazla.

**H3 düşer** ⟺ cephe yine `~3,4 m`'de durur. O zaman duvar
açıklaması **yanlıştır** ve sebep başkadır (`h`'nin sabitliği,
ADR-0042; ya da doğal sönüm).

Ara durum — cephe ilerler ama kütle iki katına çıkmazsa — kademe
**yardım ediyor ama yetmiyor** demektir ve tam merdiven gerekir.

## 5. Neden `β` yok

`t = 4,8e-3 s`'de kazı akışı başlamamıştır. Bu ölçüt yalnızca
**cephenin duvarı aşıp aşmadığını** sorar.
