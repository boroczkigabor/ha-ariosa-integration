from tests.test_data import (
    REALISTIC_MEASUREMENTS,
)


def test_measurements_dataclass() -> None:

    data = REALISTIC_MEASUREMENTS

    assert data.external_temperature == 23.5
    assert data.external_humidity == 65.4
    assert data.motor_1_rpm == 1200
    assert data.filter_hours == 1234
    assert data.bypass_open is False
