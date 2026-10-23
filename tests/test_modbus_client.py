from unittest.mock import AsyncMock
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from custom_components.ariosa.modbus_client import AriosaClient


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (235, 23.5),
        (0, 0.0),
        (65531, -0.5),
        (65483, -5.3),
    ],
)
def test_temperature_conversion(
    value: int,
    expected: float,
) -> None:
    """Test signed temperature conversion."""

    assert AriosaClient._temperature(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (654, 65.4),
        (0, 0.0),
        (1000, 100.0),
    ],
)
def test_humidity_conversion(
    value: int,
    expected: float,
) -> None:
    """Test humidity conversion."""

    assert AriosaClient._humidity(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (0, 0),
        (32767, 32767),
        (65535, -1),
        (65531, -5),
        (65483, -53),
    ],
)
def test_signed_conversion(
    value: int,
    expected: int,
) -> None:
    """Test int16 conversion."""

    assert AriosaClient._signed(value) == expected


@pytest.mark.asyncio
async def test_read_inputs() -> None:
    """Test reading input registers."""

    registers = [
        235,  # external temperature
        654,  # external humidity
        200,  # ejection temperature
        450,  # ejection humidity
        215,  # internal temperature
        501,  # internal humidity
        198,  # flow temperature
        490,  # flow humidity
        1200,  # motor 1
        1190,  # motor 2
        55,  # post treatment
        365,  # machine days
        123,  # filter hours
        0,  # pre-heater status
        1,  # bypass status
        0,  # season status
        0,  # general alarm
        0,  # filter change alarm
        0,  # filter clogged alarm
        0,  # frost protection alarm
        0,  # connection alarm
        0,  # motor alarm
        0,  # sensor alarm
        0,  # motor protection alarm
        0,  # pre-heater alarm
    ]

    response = MagicMock()
    response.isError.return_value = False
    response.registers = registers

    with patch(
        "custom_components.ariosa.modbus_client.AsyncModbusTcpClient"
    ) as client_cls:
        client = MagicMock()

        client.connected = True
        client.read_input_registers = AsyncMock(return_value=response)

        client_cls.return_value = client

        ariosa = AriosaClient("127.0.0.1", 502, 1)

        data = await ariosa.read_inputs()

        assert data.external_temperature == 23.5
        assert data.external_humidity == 65.4
        assert data.ejection_temperature == 20.0
        assert data.motor_1_rpm == 1200
        assert data.machine_days == 365
        assert data.season_status == 0
        assert data.bypass_open == 1


@pytest.mark.asyncio
async def test_read_timeout_resets_client_so_next_poll_reconnects() -> None:
    """A timeout (e.g. device powered off, half-open socket) must raise
    ReadError and replace the client, so the next poll starts from a fresh
    connection instead of reusing the dead one.
    """

    from custom_components.ariosa.exceptions import ReadError

    with patch(
        "custom_components.ariosa.modbus_client.AsyncModbusTcpClient"
    ) as client_cls:
        dead = MagicMock()
        dead.connected = True
        dead.read_input_registers = AsyncMock(side_effect=TimeoutError)

        fresh = MagicMock()

        client_cls.side_effect = [dead, fresh]

        ariosa = AriosaClient("127.0.0.1", 502, 1)

        with pytest.raises(ReadError):
            await ariosa.read_inputs()

        dead.close.assert_called_once()
        assert client_cls.call_count == 2
        assert ariosa._client is fresh


@pytest.mark.asyncio
async def test_connect_failure_raises_cannot_connect_and_resets() -> None:
    from custom_components.ariosa.exceptions import CannotConnect

    with patch(
        "custom_components.ariosa.modbus_client.AsyncModbusTcpClient"
    ) as client_cls:
        first = MagicMock()
        first.connected = False
        first.connect = AsyncMock(side_effect=OSError("unreachable"))

        client_cls.side_effect = [first, MagicMock()]

        ariosa = AriosaClient("127.0.0.1", 502, 1)

        with pytest.raises(CannotConnect):
            await ariosa.connect()

        first.close.assert_called_once()
        assert client_cls.call_count == 2
