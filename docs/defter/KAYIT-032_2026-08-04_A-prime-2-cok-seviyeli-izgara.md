# KAYIT-032 — A′-2: çok seviyeli ızgara israfı **tam olarak** kaldırıyor (2026-08-04)

**Kapsam:** FAZ 4.2 · **Durum:** ölçüldü — **A′'nın bedeli kesinleşti**
**Öncül:** [KAYIT-031](KAYIT-031_2026-08-04_A-prime-tek-izgara-ise-yaramiyor.md)

---

## 0. Kapatılan iddia

KAYIT-031 şunu söyledi:

> A′'nın bedeli, parçacık başına `h` ve `Ω`'nın yanında **çok seviyeli komşu
> aramayı** da içerir — bu bir iyileştirme değil, **ön koşuldur**.

Ama çok seviyeli aramanın israfı **gerçekten** kaldırıp kaldırmadığı
ölçülmemişti. *"Ön koşul"* demek, o koşulun işe yaradığını **varsaymaktır**
— ve bu proje varsaymaz.

---

## 1. Doğru sorgu yarıçapı

Simetrik (`average_h`) biçimde bir `(i, j)` çiftinin etkileşim yarıçapı:

```
2·h_ij = h_i + h_j
```

Yani parçacık `i`, **her seviye** `L` için o seviyenin ızgarasını
`h_i + h_L` yarıçapıyla sorgulamalıdır.

Tek ızgarada bu yarıçap **her zaman** `2·h_maks`'tır — ince parçacıklar
için gereğinden büyük. Çok seviyeli aramada her sorgu **kendi çiftine**
göre daralır.

---

## 2. Ölçüm

| λ | oran | sev. | tek (ince) | tek (genel) | **çok (ince)** | **çok (genel)** | kazanç | tam mı |
|---|---|---|---|---|---|---|---|---|
| **1,00** | 1,0 | 1 | 1,000 | 1,000 | **1,000** | **1,000** | 1,00× | ✔ |
| 1,26 | 2,0 | 2 | 1,789 | 1,282 | **1,000** | **1,000** | 1,28× | ✔ |
| 1,59 | 4,0 | 2 | 3,308 | 2,120 | **1,000** | **1,000** | 2,12× | ✔ |
| 2,00 | 8,0 | 2 | 6,271 | 4,494 | **1,000** | **1,000** | 4,49× | ✔ |
| 2,52 | 16,0 | 2 | 11,163 | 9,005 | **1,000** | **1,000** | 9,01× | ✔ |

`multilevel_is_exact` her satırda **True** — israf `1e-12` içinde **tam
1,000**. Boşluk kontrolü de geçti: `λ = 1`'de tek seviye var ve iki yöntem
aynı sonucu veriyor.

> **Çok seviyeli arama, israfı tamamen kaldırıyor.** Bu bir yaklaşım değil;
> her çift **kendi** doğru yarıçapıyla sorgulanınca fazla aday zaten kalmıyor.

---

## 3. A′'nın net maliyeti — üç mimari

| λ | oran | tasarruf | tek ızgara israf | **net** | çok seviye israf | **net** |
|---|---|---|---|---|---|---|
| 1,26 | 2:1 | 1,90× | 1,282 | 0,677 | 1,000 | **0,528** |
| 1,59 | 4:1 | 3,54× | 2,120 | 0,599 | 1,000 | **0,282** |
| 2,00 | 8:1 | 5,99× | 4,494 | 0,750 | 1,000 | **0,167** |
| 2,52 | 16:1 | 9,45× | 9,005 | 0,953 | 1,000 | **0,106** |

> **Çok seviyeli ızgarayla A′, parçacık tasarrufunun tamamını gerçekleştiriyor:
> 16:1'de `9,45×` daha ucuz.**
>
> Tek ızgarayla aynı oranda kazanç **%4,7** — yani pratikte sıfır.

---

## 4. A′'nın bedeli artık **kesin**

| bileşen | nitelik | ölçülmüş |
|---|---|---|
| parçacık başına `h` | mekanik | **68 site** (KAYIT-031 §1) |
| `Ω` (grad-h) düzeltmesi | bilinen formül, ek çekirdek | KAYIT-024'te uygulandı |
| parçacık başına CFL | mekanik | — |
| **seviye başına ızgara** | **yeni mimari** | israfı **tam** kaldırıyor (§2) |
| CPU referansının aynısı | çapraz kontrol zorunlu | 24 site |

**Bedelin karşılığı ölçüldü**: 16:1'de `9,45×` maliyet düşüşü. Bu, A′'yı
"pahalı ama işe yarar" konumuna oturtuyor — KAYIT-031'in bıraktığı
"pahalı ve belki işe yaramaz" konumundan farklı.

### Ama arayüz bedeli duruyor

KAYIT-024: parçacık başına `h`, arayüzdeki yapay kuvveti **3,2–6,5 kat**
artırıyor ve `Ω` kurtarmıyor. Çok seviyeli ızgara bunu **düzeltmez** —
farklı bir sorundur (komşu **bulma** değil, komşuluk **tutarlılığı**).

KAYIT-026 ise o gürültünün şok geçişine **ölçülebilir etki yapmadığını**
gösterdi (taşma %0,000).

---

## 5. Karar tablosunun son hâli

| # | mermiyi çözer | **ölçülmüş bedel** | **ölçülmüş kazanç** |
|---|---|---|---|
| ~~A~~ | **hayır** | — | — |
| **A′** | evet | arayüz 3,2–6,5× gürültü + çok seviyeli ızgara (68+24 site, yeni arama mimarisi) | **16:1'de 9,45× ucuz**, model-form hatası **yok** |
| ~~B~~ | A′ ile | = A′ | = A′ |
| **C** | evet | momentum **7,5e-03 sistematik** + MLS + korunum düzeltmesi | arayüzde yapay kuvvet yok |
| **D** | **atlar** | model-form **%5–7**, kalibre edilemiyor | en ucuzu |

**A′'nın kefesi artık dolu ve kazançlı tarafı ölçülmüş.** Karar hâlâ
proje sahibinin — ama seçenekler arasında **tek** *"model-form hatası yok"*
diyebilen A′.

---

## 6. Sırada

| # | iş | neden |
|---|---|---|
| — | **ADR-0041'in kilitlenmesi** | tüm kefeler ölçüldü; karar proje sahibinin |
| D-3 | iki parametreli kaynak terimi | D seçilirse gerekli |
| — | ADR-0041 §5 boşluk 3 (mukavemetli malzeme) | hangisi seçilirse seçilsin açık |

---

## 7. Bu kayıtta uygulanan kurallar

| kural | nerede |
|---|---|
| *"ön koşul"* demek onun **işe yaradığını varsaymaktır** — ölçülür | §0 |
| bir maliyet oranında **payda** da modelin parçasıdır | KAYIT-031 §3b (bu ölçüm ortaya çıkardı) |
| boşluk kontrolü: `λ=1`'de iki yöntem **aynı** olmalı | §2 |
| bedel ölçülünce **kazanç** da ölçülür | §3 |
| bir düzeltme **her şeyi** düzeltmez — sınırı yazılır | §4 (arayüz bedeli duruyor) |
