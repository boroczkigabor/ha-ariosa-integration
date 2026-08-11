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

REGISTER_COUNT = 25
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
# Drive states
REGISTER_PRE_HEATER_STATE = 13
REGISTER_BYPASS_OPEN = 14
REGISTER_SEASON_STATE = 15
# Alarm statuses
REGISTER_GENERIC_ALARM = 16
REGISTER_FILTER_CHANGE_ALARM = 17
REGISTER_FILTER_CLOGGED_ALARM = 18
REGISTER_FROST_PROTECTION_ALARM = 19
REGISTER_CONNECTION_ALARM = 20
REGISTER_MOTOR_ALARM = 21
REGISTER_SENSOR_ALARM = 22
REGISTER_MOTOR_PROTECTION_ALARM = 23
REGISTER_PRE_HEATER_ALARM = 24

PLATFORMS: list[str] = ["sensor", "binary_sensor"]


# Raw Modbus values for the season register, mapped to the machine-readable
# enum keys used as the sensor's translated states (see sensor.py /
# translations/*.json).
SEASON_AUTOMATIC = "automatic"
SEASON_WINTER = "winter"
SEASON_MODBUS_VALUES: dict[int, str] = {
    0: SEASON_AUTOMATIC,
    1: SEASON_WINTER,
}
