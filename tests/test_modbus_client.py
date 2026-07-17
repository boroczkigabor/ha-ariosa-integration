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
        235,
        654,
        200,
        450,
        215,
        501,
        198,
        490,
        1200,
        1190,
        55,
        365,
        123,
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
