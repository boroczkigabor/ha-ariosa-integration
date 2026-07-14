from __future__ import annotations
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException
from .const import (
    DEFAULT_SLAVE,
    REGISTER_COUNT,
    START_REGISTER,
)
from .exceptions import CannotConnect, ReadError
from .models import AriosaMeasurements


class AriosaClient:
    """Ariosa Modbus TCP client."""

    def __init__(
        self,
        host: str,
        port: int,
        slave: int = DEFAULT_SLAVE,
    ) -> None:
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
                address=START_REGISTER,
                count=REGISTER_COUNT,
                slave=self._slave,
            )
        except ModbusException as err:
            raise ReadError from err

        if response.isError():
            raise ReadError

        registers = response.registers

        return AriosaMeasurements(
            external_temperature=self._temperature(registers[0]),
            external_humidity=self._humidity(registers[1]),
            ejection_temperature=self._temperature(registers[2]),
            ejection_humidity=self._humidity(registers[3]),
            internal_temperature=self._temperature(registers[4]),
            internal_humidity=self._humidity(registers[5]),
            flow_temperature=self._temperature(registers[6]),
            flow_humidity=self._humidity(registers[7]),
            motor_1_rpm=registers[8],
            motor_2_rpm=registers[9],
            post_treatment=registers[10],
            machine_days=registers[11],
            filter_hours=registers[12],
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
