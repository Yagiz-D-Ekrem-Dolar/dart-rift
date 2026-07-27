"""P0-FR-01: birim testi + boyut analizi."""

import pytest

from dartrift import units as U


class TestConversions:
    def test_g_per_cm3_to_kg_per_m3_exact(self):
        assert U.convert(2.6, "g/cm^3", "kg/m^3") == pytest.approx(2600.0, rel=0, abs=0)

    def test_kg_per_m3_to_g_per_cm3_exact(self):
        assert U.convert(2600.0, "kg/m^3", "g/cm^3") == pytest.approx(2.6)

    def test_km_s_to_m_s(self):
        # DART carpma hizi 6.1 km/s -> 6100 m/s
        assert U.convert(6.1, "km/s", "m/s") == pytest.approx(6100.0)

    def test_gpa_to_pa(self):
        assert U.convert(26.7, "GPa", "Pa") == pytest.approx(26.7e9)

    def test_mj_per_kg_to_j_per_kg(self):
        assert U.convert(4.87, "MJ/kg", "J/kg") == pytest.approx(4.87e6)

    @pytest.mark.parametrize(
        "unit", ["kg", "g", "m", "cm", "km", "s", "m/s", "km/s", "kg/m^3", "g/cm^3", "Pa", "GPa"]
    )
    def test_roundtrip_via_si(self, unit):
        q = U.to_si(3.7, unit)
        assert U.from_si(q, unit) == pytest.approx(3.7, rel=1e-15)

    def test_unknown_unit_raises(self):
        with pytest.raises(U.UnitError, match="bilinmeyen birim"):
            U.to_si(1.0, "parsec")

    def test_cross_dimension_conversion_raises(self):
        # yogunluk -> hiz donusumu fiziksel sacmalik; ACIK hata (P0-FR-01)
        with pytest.raises(U.UnitError, match="boyut uyusmazligi"):
            U.convert(1.0, "g/cm^3", "km/s")


class TestDimensionAlgebra:
    def test_velocity_is_length_over_time(self):
        assert U.VELOCITY == U.LENGTH / U.TIME

    def test_pressure_dimension(self):
        # Pa = kg m^-1 s^-2
        assert U.PRESSURE == U.MASS / (U.LENGTH * U.TIME**2)

    def test_energy_dimension(self):
        assert U.ENERGY == U.MASS * U.VELOCITY**2

    def test_dimension_str(self):
        assert str(U.DIMENSIONLESS) == "1"
        assert "kg" in str(U.DENSITY) and "m^-3" in str(U.DENSITY)


class TestQuantity:
    def test_add_same_dim(self):
        a = U.Quantity(1.0, U.PRESSURE)
        b = U.Quantity(2.0, U.PRESSURE)
        assert (a + b).value == pytest.approx(3.0)

    def test_add_mixed_dim_raises(self):
        a = U.Quantity(1.0, U.PRESSURE)
        b = U.Quantity(1.0, U.DENSITY)
        with pytest.raises(U.UnitError, match="boyut uyusmazligi"):
            _ = a + b

    def test_sub_mixed_dim_raises(self):
        with pytest.raises(U.UnitError):
            _ = U.Quantity(1.0, U.MASS) - U.Quantity(1.0, U.TIME)

    def test_add_raw_float_raises(self):
        with pytest.raises(U.UnitError):
            _ = U.Quantity(1.0, U.MASS) + 1.0  # type: ignore[operator]

    def test_mul_combines_dims(self):
        rho = U.Quantity(2600.0, U.DENSITY)
        vol = U.Quantity(2.0, U.LENGTH**3)
        m = rho * vol
        assert m.dim == U.MASS
        assert m.value == pytest.approx(5200.0)

    def test_div_combines_dims(self):
        d = U.Quantity(100.0, U.LENGTH) / U.Quantity(10.0, U.TIME)
        assert d.dim == U.VELOCITY
        assert d.value == pytest.approx(10.0)

    def test_pow(self):
        v = U.Quantity(3.0, U.VELOCITY) ** 2
        assert v.dim == U.VELOCITY**2
        assert v.value == pytest.approx(9.0)

    def test_scalar_mul(self):
        assert (2 * U.Quantity(3.0, U.MASS)).value == pytest.approx(6.0)


class TestConstants:
    def test_G_value_and_dimension(self):
        assert U.G.value == pytest.approx(6.67430e-11)
        assert U.G.dim == U.GRAVITATIONAL_PARAMETER

    def test_standard_gravity(self):
        assert U.STANDARD_GRAVITY.value == pytest.approx(9.80665)
        assert U.STANDARD_GRAVITY.dim == U.ACCELERATION
