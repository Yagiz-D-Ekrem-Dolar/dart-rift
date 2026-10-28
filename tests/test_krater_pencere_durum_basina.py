"""ADR-0061 + ADR-0062 — krater penceresi ve **örtülü krater** reddi.

A86/KAYIT-088: üretim havuzunda 30/96 nokta `krater_derinlik = nan`
dönüyordu. Kök sebep iki katmanlıydı ve ikisi ayrı ayrı sınanıyor:

1. **ADR-0061** — `tepe` iki durumdan *ortak* alınıyordu. Zayıf
   matriste yukarı fırlayan ama kaçmayan (`bağlı`) malzeme `tepe`'yi
   şişiriyor, `arama_derinligi` kadar sarkan pencere **referans**
   yüzeyi hiç görmüyordu. Artık pencere **durum başına** kurulur.
2. **ADR-0062** — (1) düzeltilince `nan` kalkıyor ama yerine gelen sayı
   krater derinliği *değil*: `phi = esik` eş-yüzeyi dıştan içe tarandığı
   için **örtünün tepesini** okuyor. Ölçüldü: `d_merkez = -(yük+0,913)`
   m. Üretimde `z_ref = 59,517`, `z_son = 105,916` → `-46,4` m.
   Operatör bu durumda sayı döndürmek yerine REDDEDER.

Mevcut `test_krater_yuzey.py` (1)'i yakalayamıyordu: oradaki perde
yalnız `2 m` yükseliyor, `arama_derinligi` ise `10 m`. Buradaki
sınavlar kaldırmayı **pencereden büyük** seçer (üretimde ölçülen kayma
`30–35 m`'ydi).
"""
from __future__ import annotations

import numpy as np
import pytest

from dartrift.observables.crater_shape import krater_yuzey
from dartrift.setup.rubble_generator import lattice_points, particle_volume

S = 0.35
H = 2.0 * S
RHO = 2700.0 / 1.3
#: Varsayilan `arama_derinligi` (m); kaldirma bundan BUYUK secilir.
ARAMA = 10.0
#: Cekirdek destegi = ADR-0062 ortu payi (m). Ayarlanmis sayi DEGIL.
ORTU_PAYI = 2.0 * H
#: Olculen bagimlilik: `d_merkez = -(yuk + PERDE_OFSET)`.
PERDE_OFSET = 0.9134


@pytest.fixture(scope="module")
def levha():
    x = lattice_points(np.array([-7.0, -7.0, -5.0]),
                       np.array([7.0, 7.0, 0.0]), S, "fcc")
    x = x[x[:, 2] <= 1e-9]
    m = np.full(len(x), RHO * particle_volume(S, "fcc"))
    return x, m


def _olc(x, x0, m, v, rho=None, **kw):
    n = len(x)
    return krater_yuzey(x, x0, m=m, h=np.full(n, H),
                        rho=np.full(n, RHO) if rho is None else rho,
                        rho_reference=np.full(n, RHO),
                        impact_direction=np.array([0.0, 0.0, -1.0]),
                        v=v, merkez=np.array([0.0, 0.0, -2.5]), **kw)


def _ortulu(levha, *, yukseklik: float, D: float = 1.0, a: float = 2.0):
    """Paraboloit çukur + eksen üstünde **bağlı** (yavaş) yüksek örtü.

    Örtü `yukseklik` metrede ve hızı sıfır: kaçmış sayılmaz, yani
    `bagli` kümeye girer. Üretimdeki mekanizmanın sentetik eşi.
    """
    x0, m = levha
    x = x0.copy()
    s_yan = np.hypot(x[:, 0], x[:, 1])
    z_yuzey = np.where(s_yan < a, -D * (1.0 - (s_yan / a) ** 2), 0.0)
    sil = x[:, 2] > z_yuzey + 1e-9
    v = np.zeros_like(x)
    x[sil, 2] = yukseklik + (x[sil, 2] - x[sil, 2].min())
    return x, x0, m, v, int(sil.sum())


def _sil_ejekta(levha, *, D: float = 1.0, a: float = 2.0):
    """Aynı çukur, ama örtü yok (ejekta kaçmış) — ölçülebilir hâl."""
    x0, m = levha
    x = x0.copy()
    s_yan = np.hypot(x[:, 0], x[:, 1])
    z_yuzey = np.where(s_yan < a, -D * (1.0 - (s_yan / a) ** 2), 0.0)
    sil = x[:, 2] > z_yuzey + 1e-9
    v = np.zeros_like(x)
    x[sil, 2] += 50.0
    v[sil, 2] = 5.0
    return x, x0, m, v, int(sil.sum())


# --- ADR-0061: pencere durum basina -------------------------------------

def test_pencereden_YUKSEK_ortu_artik_REFERANSI_KACIRMIYOR(levha):
    """Asıl gerileme sınavı: `30 m` örtü `10 m`'lik pencereyi aşar.

    Ortak pencereyle hata *"REFERANS ... bulunamadi"* oluyordu. Durum
    başına pencereyle referans yüzey bulunur; red artık **örtü**
    sebebiyle gelir. Fark kritik: biri ölçme kusuru, öteki fizik.
    """
    x, x0, m, v, n_ortu = _ortulu(levha, yukseklik=30.0)
    assert n_ortu > 0, "sinav bos: ortu olusmadi"
    with pytest.raises(ValueError) as e:
        _olc(x, x0, m, v)
    mesaj = str(e.value)
    assert "ORTULU KRATER" in mesaj, mesaj
    assert "bulunamadi" not in mesaj, f"referans yuzey hala kaciyor: {mesaj}"


def test_referans_penceresi_ORTUDEN_ETKILENMIYOR(levha):
    """Referans penceresi referansın kendi tepesine (`z ≈ 0`) bağlı.

    Örtünün `10 m` ya da `40 m`'de olması referans penceresini
    değiştirmemeli; son pencere ise örtüyle birlikte yukarı taşınır.
    Pencereler redden önce kurulduğu için istisnanın içinden değil,
    hiçbir yüzeyin eşiği kesmediği (`esik` çok büyük) bir çağrıdan
    okunuyor — ölçülen şey yalnız pencere kurulumu.
    """
    pen = {}
    for y in (10.0, 40.0):
        with pytest.raises(ValueError) as e:
            _olc(*_ortulu(levha, yukseklik=y)[:4])
        assert "ORTULU KRATER" in str(e.value)
        with pytest.raises(ValueError) as e2:
            _olc(*_ortulu(levha, yukseklik=y)[:4], esik=1e9)
        pen[y] = str(e2.value)
        assert "bulunamadi" in pen[y]

    def _ref(mesaj: str) -> str:
        return mesaj.split("REFERANS (pencere ")[1].split(" m)")[0]

    assert _ref(pen[10.0]) == _ref(pen[40.0]), (
        f"referans penceresi son duruma bagli: {pen[10.0]} / {pen[40.0]}")


def test_son_penceresi_ortuyle_YUKARI_TASINIYOR(levha):
    """Durum başına pencerenin öteki yüzü: son pencere örtüyü izler."""
    alt = {}
    for y in (10.0, 40.0):
        with pytest.raises(ValueError) as e:
            _olc(*_ortulu(levha, yukseklik=y)[:4], esik=1e9)
        alt[y] = float(str(e.value).split("SON (pencere ")[1].split("..")[0])
    assert alt[40.0] > alt[10.0] + 25.0, alt


# --- ADR-0062: ortulu krater reddi --------------------------------------

def test_ortu_payi_COZUNURLUK_olcegindedir(levha):
    """Kapı `2h`; `d_merkez = -(yük + 0,913)` ölçüldü.

    `yuk = 0,4` → `-1,313 m`, destek `1,400 m`: geçer.
    `yuk = 0,5` → `-1,413 m`: reddedilir. Sınır ölçülen bağıntıdan
    geliyor, ayarlanmadı.
    """
    k = _olc(*_ortulu(levha, yukseklik=0.4)[:4])
    assert k.tani["ortu_payi"] == pytest.approx(ORTU_PAYI)
    assert k.derinlik_merkez == pytest.approx(-(0.4 + PERDE_OFSET), abs=1e-3)
    assert k.derinlik_merkez > -ORTU_PAYI

    with pytest.raises(ValueError, match="ORTULU KRATER"):
        _olc(*_ortulu(levha, yukseklik=0.5)[:4])


def test_ortu_yuksekligi_d_merkezi_BIREBIR_SURUKLUYOR(levha):
    """Ölçülen bağıntı: örtü `1 m` yükselince `d_merkez` `1 m` düşer.

    Bu, okunan şeyin kraterin tabanı DEĞİL örtünün tepesi olduğunun
    doğrudan kanıtı — ADR-0062'nin gerekçesi.
    """
    yuk = [0.0, 0.1, 0.2, 0.3, 0.4]
    d = [_olc(*_ortulu(levha, yukseklik=y)[:4]).derinlik_merkez for y in yuk]
    egim = float(np.polyfit(yuk, d, 1)[0])
    assert egim == pytest.approx(-1.0, abs=1e-3), f"egim {egim}"


def test_ortu_KACARSA_krater_OLCULUYOR(levha):
    """Kapı kör değil: ejekta kaçmışsa aynı çukur ölçülür ve POZİTİF.

    ADR-0062'nin yönü önceden belli — yalnız sayıyı redde çevirir,
    hiçbir yerde krater yaratmaz ya da yok etmez.
    """
    k = _olc(*_sil_ejekta(levha)[:4])
    assert np.isfinite(k.derinlik_merkez)
    assert k.derinlik_merkez == pytest.approx(0.9216, abs=1e-3)
    assert k.derinlik_merkez > 0.0


def test_URETIM_SAYILARI_dogru_tarafa_dusuyor():
    """Üretimdeki üç ölçüm, kapının iki yanına doğru düşüyor mu.

    Merdivenin en ince kabuğu `3:0,35` → `h = 0,70`, destek `1,40 m`.
    Çalışan iki nokta `+0,748` / `+0,892`; düşen noktalar
    `59,517 − 105,916 = −46,399`. Kapı `−1,40`. Arada `45 m` boşluk
    var: kapı `−1` ile `−45` arasında HERHANGİ bir yerde aynı
    sınıflamayı verir — yani eşik ayarlanmış bir sayı değil.
    """
    kapi = -2.0 * 0.70
    calisan = (59.517 - 58.769, 59.517 - 58.625)
    dusen = 59.517 - 105.916
    assert all(c > kapi for c in calisan), calisan
    assert dusen < kapi
    for deneme in (-1.0, -5.0, -20.0, -45.0):
        assert all(c > deneme for c in calisan) and dusen < deneme, deneme


# --- A86 ikinci tespiti: sebep yazilmali --------------------------------

def test_SADECE_SON_dusunce_mesaj_yalniz_SONU_yaziyor(levha):
    """Asimetrik düşüş adıyla yazılmalı (KAYIT-088 §8).

    Son durumun yoğunluğu çok büyütülürse `V = m/rho` küçülür ve
    `phi` son pencerede eşiği kesmez; referans ise `rho_reference`
    kullandığı için sağlam kalır. Yani tek taraf düşer.
    """
    x, x0, m, v, _ = _ortulu(levha, yukseklik=30.0)
    sil = x[:, 2] > 10.0
    with pytest.raises(ValueError) as e:
        _olc(x, x0, m, v, rho=np.where(sil, 1e9, RHO))
    mesaj = str(e.value)
    assert "bulunamadi" in mesaj, mesaj
    assert "SON (pencere" in mesaj, mesaj
    assert "REFERANS" not in mesaj, f"yanlis taraf suclandi: {mesaj}"


def test_IKI_TARAF_dusunce_mesaj_IKISINI_de_yaziyor(levha):
    """Eşik ulaşılmaz yapılırsa iki yüzey de bulunamaz; mesaj ikisini
    de pencereleriyle yazar — 30 vaka sessizce kaybolmasın."""
    x, x0, m, v, _ = _ortulu(levha, yukseklik=30.0)
    with pytest.raises(ValueError) as e:
        _olc(x, x0, m, v, esik=1e9)
    mesaj = str(e.value)
    assert "REFERANS (pencere" in mesaj, mesaj
    assert "SON (pencere" in mesaj, mesaj


def test_durum_basina_pencere_ARAMA_DERINLIGINE_dayaniklilastirdi(levha):
    """Yan ürün, ölçüldü: pencere durum başına kurulunca `1e-6` m'lik
    arama derinliğinde bile her iki yüzey bulunur (her durum kendi
    tepesinden pencerelendiği için). Eskiden bu ayar kritikti; artık
    red **fizik** sebebiyle (örtü) geliyor, ölçme kusuruyla değil."""
    x, x0, m, v, _ = _ortulu(levha, yukseklik=30.0)
    with pytest.raises(ValueError) as e:
        _olc(x, x0, m, v, arama_derinligi=1e-6)
    assert "ORTULU KRATER" in str(e.value), str(e.value)
    assert "bulunamadi" not in str(e.value), str(e.value)
