# Protokol F — yapay viskozite × çözünürlük ızgarası

**Yazıldı:** 2026-09-06, **koşudan önce** · **Dayanak:** rapor A53, A52

---

## Soru

A53 ölçtü: `α_av 1,0 → 0,1` ile kaçan hedef kütlesi `132` kat artıyor
ve kütle ağırlıklı eksenel hız `1264 m/s` (jet) → `0,397 m/s`
(**kazı akışı ölçeği**) düşüyor.

**Açık soru:** bu kaba parçacık artefaktı mı? Kaçan `33` parçacığın
hepsi kaba seviyeden geliyordu (`372,8 kg`/parçacık).

Doğru sınav bir kademe ince merdivendi; **A52 yüzünden `107` saat**
sürerdi. Onun yerine iki *mevcut* ölçekte tekrarlanıyor.

## Izgara

| | `α_av = 1,0` | `α_av = 0,4` | `α_av = 0,1` |
|---|---|---|---|
| **kaba** (`N = 17 201`) | `F_kaba_av10` | `F_kaba_av04` | `F_kaba_av01` |
| **orta** (`N = 69 886`) | `F_orta_av10` | `F_orta_av04` | `F_orta_av01` |

`β_av` her zaman `2 α_av`. `t_end = 0,024 s`, tek değişken AV.

## Ölçülen büyüklük

```
⟨v⟩ = P_kacan_hedef / kutle_kacan_hedef
```

Ayrıca: `kutle_kacan_hedef`, `n_kacan_hedef`, `Δβ_hedef`,
`ejekta_seviyeleri` (hangi inceltme seviyesinden geldiği).

**Neden `⟨v⟩`:** tek başına kütle veya tek başına `Δβ` bu mekanizmayı
**gizliyor** — kütle `132` kat artarken `Δβ` `24` kat düşüyor ve
ikisi ayrı okununca çelişki gibi görünüyor. Çelişki değil: hız
`3 188` kat düşmüş. A53'ün dersi buydu.

## Yargı — **şimdi kilitleniyor**

| gözlenen | sonuç |
|---|---|
| `⟨v⟩` **her iki ölçekte de** `α_av` ile monoton azalıyor | **AV gerçek bir kontrol parametresi.** Mekanizma sürekli ve çözünürlük-dirençli. |
| Etki yalnız **bir** ölçekte görünüyor | **Çözünürlük artefaktı.** AV aday olmaktan çıkar. |
| İki ölçekte **aynı yönde**, farklı büyüklükte | Mekanizma gerçek, **büyüklüğü çözülmemiş**. Sonuç şartlı bildirilir. |
| Kaba ölçekte `n_kacan_hedef = 0` kalıyor (her AV'de) | Kaba ölçek bu soruyu **yanıtlayamaz**; yalnız orta ölçek okunur ve çözünürlük iddiası **yapılmaz**. |

### Ek koşul — ejekta seviyesi

Her kolda kaçan kütlenin **inceltme seviyesi dağılımı** raporlanır.
Bir kolda kaçanların **tamamı** en kaba seviyedense o kol
*"çözülmüş ejekta"* sayılmaz — A36'da konan kural, burada da
geçerli.

## Geçersizlik

1. Adım sınırı (`ADIM SINIRINA TAKILDI`).
2. Tesisat sınavı (`exit 91`).
3. Bir kolda şok yargısı `SOK_YOK` ise o kol okunmaz (ADR-0049).

## Maliyet

Kaba: `5` dk/koşu (ölçüldü, `Rb_R1` `00:05:06`).
Orta: `~1,2` sa/koşu (`2,81` adım/s, `≈ 6 100` adım).
Altı kol, tek dizi, `6` GPU → **`~1,5` saat**.
