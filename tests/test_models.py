from tests.test_data import SUMMER_MEASUREMENTS


def test_measurements_dataclass() -> None:

    data = SUMMER_MEASUREMENTS

    assert data.external_temperature == 32.5
    assert data.external_humidity == 55.2
    assert data.motor_1_rpm == 1200
    assert data.filter_hours == 50
    assert data.bypass_open is False
