from datetime import timedelta

DOMAIN = "ariosa"

MANUFACTURER = "Ariosa"

DEFAULT_NAME = "Ariosa Ventilation"

DEFAULT_PORT = 502

DEFAULT_SLAVE = 1

# Optional config-flow field: a user-supplied entity_id (typically another
# sensor.* temperature entity) used as the reference value for the
# "temperature waste" sensor. Not a fixed HA const, so it's defined here.
CONF_REFERENCE_TEMPERATURE_ENTITY = "reference_temperature_entity"

UPDATE_INTERVAL = timedelta(seconds=30)

START_REGISTER = 100

REGISTER_COUNT = 13
REGISTER_EXT_TEMP = 0
REGISTER_EXT_HUM = 1
REGISTER_EJECT_TEMP = 2
REGISTER_EJECT_HUM = 3
REGISTER_INT_TEMP = 4
REGISTER_INT_HUM = 5
REGISTER_FLOW_TEMP = 6
REGISTER_FLOW_HUM = 7
REGISTER_MOTOR_1_RPM = 8
REGISTER_MOTOR_2_RPM = 9
REGISTER_POST_TRTMT = 10
REGISTER_MACHINE_DAYS = 11
REGISTER_FILTER_HOURS = 12
PLATFORMS: list[str] = ["sensor", "binary_sensor"]
