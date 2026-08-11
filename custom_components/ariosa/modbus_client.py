from __future__ import annotations

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .const import (
    REGISTER_BYPASS_OPEN,
    REGISTER_CONNECTION_ALARM,
    REGISTER_COUNT,
    REGISTER_EJECT_HUM,
    REGISTER_EJECT_TEMP,
    REGISTER_EXT_HUM,
    REGISTER_EXT_TEMP,
    REGISTER_FILTER_CHANGE_ALARM,
    REGISTER_FILTER_CLOGGED_ALARM,
    REGISTER_FILTER_HOURS,
    REGISTER_FLOW_HUM,
    REGISTER_FLOW_TEMP,
    REGISTER_FROST_PROTECTION_ALARM,
    REGISTER_GENERIC_ALARM,
    REGISTER_INT_HUM,
    REGISTER_INT_TEMP,
    REGISTER_MACHINE_DAYS,
    REGISTER_MOTOR_1_RPM,
    REGISTER_MOTOR_2_RPM,
    REGISTER_MOTOR_ALARM,
    REGISTER_MOTOR_PROTECTION_ALARM,
    REGISTER_POST_TRTMT,
    REGISTER_PRE_HEATER_ALARM,
    REGISTER_PRE_HEATER_STATE,
    REGISTER_SEASON_STATE,
    REGISTER_SENSOR_ALARM,
    START_REGISTER,
)
from .exceptions import CannotConnect, ReadError
from .models import AriosaMeasurements


class AriosaClient:
    """Ariosa Modbus TCP client."""

    def __init__(self, host: str, port: int, slave: int) -> None:
        self._host = host
        self._port = port
        self._slave = slave

        self._client = AsyncModbusTcpClient(
            host=host,
            port=port,
        )

    @property
    def connected(self) -> bool:
        """Return connection state."""
        return self._client.connected

    async def connect(self) -> None:
        """Connect to the device."""

        connected = await self._client.connect()

        if not connected:
            raise CannotConnect

    async def disconnect(self) -> None:
        """Disconnect."""

        self._client.close()

    async def read_inputs(self) -> AriosaMeasurements:
        """Read all input registers."""

        if not self.connected:
            await self.connect()

        try:
            response = await self._client.read_input_registers(
                address=START_REGISTER, count=REGISTER_COUNT, device_id=self._slave
            )
        except ModbusException as err:
            raise ReadError from err

        if response.isError():
            raise ReadError

        registers = response.registers

        return AriosaMeasurements(
            external_temperature=self._temperature(registers[REGISTER_EXT_TEMP]),
            external_humidity=self._humidity(registers[REGISTER_EXT_HUM]),
            ejection_temperature=self._temperature(registers[REGISTER_EJECT_TEMP]),
            ejection_humidity=self._humidity(registers[REGISTER_EJECT_HUM]),
            internal_temperature=self._temperature(registers[REGISTER_INT_TEMP]),
            internal_humidity=self._humidity(registers[REGISTER_INT_HUM]),
            flow_temperature=self._temperature(registers[REGISTER_FLOW_TEMP]),
            flow_humidity=self._humidity(registers[REGISTER_FLOW_HUM]),
            motor_1_rpm=registers[REGISTER_MOTOR_1_RPM],
            motor_2_rpm=registers[REGISTER_MOTOR_2_RPM],
            post_treatment=registers[REGISTER_POST_TRTMT],
            machine_days=registers[REGISTER_MACHINE_DAYS],
            filter_hours=registers[REGISTER_FILTER_HOURS],
            pre_heater_status=self._boolean(registers[REGISTER_PRE_HEATER_STATE]),
            bypass_open=self._boolean(registers[REGISTER_BYPASS_OPEN]),
            season_status=registers[REGISTER_SEASON_STATE],
            general_alarm=self._boolean(registers[REGISTER_GENERIC_ALARM]),
            filter_change_alarm=self._boolean(registers[REGISTER_FILTER_CHANGE_ALARM]),
            filter_clogged_alarm=self._boolean(
                registers[REGISTER_FILTER_CLOGGED_ALARM]
            ),
            frost_protection_alarm=self._boolean(
                registers[REGISTER_FROST_PROTECTION_ALARM]
            ),
            connection_alarm=self._boolean(registers[REGISTER_CONNECTION_ALARM]),
            motor_alarm=self._boolean(registers[REGISTER_MOTOR_ALARM]),
            sensor_alarm=self._boolean(registers[REGISTER_SENSOR_ALARM]),
            motor_protection_alarm=self._boolean(
                registers[REGISTER_MOTOR_PROTECTION_ALARM]
            ),
            pre_heater_alarm=self._boolean(registers[REGISTER_PRE_HEATER_ALARM]),
        )

    @staticmethod
    def _temperature(value: int) -> float:
        """Decode signed 16-bit temperature."""

        return AriosaClient._signed(value) / 10.0

    @staticmethod
    def _humidity(value: int) -> float:
        """Decode humidity."""

        return value / 10.0

    @staticmethod
    def _signed(value: int) -> int:
        """Convert unsigned Modbus register to signed int16."""

        if value >= 0x8000:
            return value - 0x10000

        return value

    @staticmethod
    def _boolean(value: int) -> bool:
        """Convert unsigned int16 to boolean."""
        return bool(value)
