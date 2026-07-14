from custom_components.ariosa.models import AriosaMeasurements


def test_measurements_dataclass() -> None:

    data = AriosaMeasurements(
        external_temperature=23.5,
        external_humidity=65.4,
        ejection_temperature=20.1,
        ejection_humidity=45.0,
        internal_temperature=22.3,
        internal_humidity=50.1,
        flow_temperature=21.4,
        flow_humidity=55.5,
        motor_1_rpm=1200,
        motor_2_rpm=1200,
        post_treatment=25,
        machine_days=365,
        filter_hours=1234,
    )

    assert data.external_temperature == 23.5
    assert data.external_humidity == 65.4
    assert data.motor_1_rpm == 1200
    assert data.filter_hours == 1234
