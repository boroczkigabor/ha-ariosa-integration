from custom_components.ariosa.models import AriosaMeasurements

# A physically realistic winter scenario: cold outdoor air, warm indoor air,
# and the heat exchanger recovering most of the difference on both sides.
WINTER_MEASUREMENTS = AriosaMeasurements(
    external_temperature=0.0,
    external_humidity=80.0,
    ejection_temperature=3.0,
    ejection_humidity=90.0,
    internal_temperature=21.0,
    internal_humidity=45.0,
    flow_temperature=18.0,
    flow_humidity=30.0,
    motor_1_rpm=1200,
    motor_2_rpm=1190,
    post_treatment=0,
    machine_days=100,
    filter_hours=50,
    pre_heater_status=True,
    bypass_open=False,
    season_status=1,
)

# A physically realistic summer scenario: hot outdoor air, cooler indoor
# air (external > internal). The exchanger recovers "coolness" instead of
# heat, but the same ratio formula should hold — the sign of the gap
# shouldn't matter, only how much of it gets closed.
SUMMER_MEASUREMENTS = AriosaMeasurements(
    external_temperature=32.5,
    external_humidity=55.2,
    ejection_temperature=29.4,
    ejection_humidity=50.1,
    internal_temperature=24.0,
    internal_humidity=59.1,
    flow_temperature=27.9,
    flow_humidity=55.4,
    motor_1_rpm=1200,
    motor_2_rpm=1190,
    post_treatment=25,
    machine_days=100,
    filter_hours=50,
    pre_heater_status=False,
    bypass_open=False,
    season_status=0,
)

# Winter, but with the exchanger core bypassed: supply air stays close to
# outdoor temperature, exhaust air stays close to room temperature, because
# neither passed through the core.
BYPASS_MEASUREMENTS = AriosaMeasurements(
    external_temperature=5.0,
    external_humidity=70.0,
    ejection_temperature=20.5,
    ejection_humidity=45.0,
    internal_temperature=21.0,
    internal_humidity=45.0,
    flow_temperature=5.5,
    flow_humidity=70.0,
    motor_1_rpm=1200,
    motor_2_rpm=1190,
    post_treatment=0,
    machine_days=100,
    filter_hours=50,
    pre_heater_status=False,
    bypass_open=True,
    season_status=0,
)
