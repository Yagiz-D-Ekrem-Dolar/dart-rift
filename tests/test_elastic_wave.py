"""P2-VR-03: elastik dalga hizi sqrt((K + 4G/3)/rho)'ya yakin + yakinsiyor.

Tek bir cozunurlukteki sayi, "yakin" olup olmadigini soyler ama YAKINSADIGINI
soylemez. Sonlu cozunurlukte SPH dalga paketi yapay viskoziteyle hafif yavaslar;
dogru kanit, hatanin cozunurlukle KUCULMESI ve en ince kafeste esigi
karsilamasidir.
"""

import pytest

from dartrift.validation.solids import run_elastic_wave

RESOLUTIONS = [300, 400, 600]


class TestElasticWave:
    @pytest.fixture(scope="class")
    def ladder(self):
        return {r: run_elastic_wave(resolution=r) for r in RESOLUTIONS}

    def test_speed_matches_longitudinal_at_finest(self, ladder):
        fine = ladder[max(RESOLUTIONS)]
        assert fine["rel_err"] < 0.03, fine

    def test_error_decreases_with_resolution(self, ladder):
        errs = [ladder[r]["rel_err"] for r in RESOLUTIONS]
        assert errs[0] > errs[1] > errs[2], f"yakinsama yok: {errs}"

    def test_speed_is_longitudinal_not_bulk(self, ladder):
        # G katkisi gercek olmali: olculen hiz c0=sqrt(K/rho)'dan AYIRT edilebilir
        for r in RESOLUTIONS:
            assert ladder[r]["distinguishes_bulk"], ladder[r]

    def test_measured_speed_above_bulk(self, ladder):
        # kesme modulu dalgayi hizlandirir: c_olculen > c0_bulk
        fine = ladder[max(RESOLUTIONS)]
        assert fine["speed_measured"] > 1.2 * fine["c0_bulk"], fine

    def test_tracks_right_going_wave_even_when_underresolved(self):
        """Gerinimsiz hiz darbesi ESIT genlikli iki dalgaya ayrilir.

        d'Alembert: v = 0.5 f(x - ct) + 0.5 f(x + ct). Iki tepe de POZITIF ve
        buyuklukleri esit oldugu icin, tum dizi uzerinde argmax hangisini
        sececegi yazi-turadir. Eskiden res=150'de SOLA gideni seciyordu ve
        olculen hiz -1854 m/s (hata %140) cikiyordu. Bu test, olcumun kaba
        kafeste bile dogru dalgayi izledigini sabitler.
        """
        r = run_elastic_wave(resolution=150)
        assert r["speed_measured"] > 0.0, r          # eskiden -1854 m/s idi
        assert r["x_peak_right"] > 0.15, r           # tepe saga ilerlemis
        assert r["rel_err"] < 0.15, r                # kaba ama anlamli (%9.2)
