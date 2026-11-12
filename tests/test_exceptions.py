from custom_components.ariosa.exceptions import (
    AriosaError,
    CannotConnect,
    ReadError,
    WriteError,
)


def test_exception_inheritance() -> None:
    assert issubclass(CannotConnect, AriosaError)
    assert issubclass(ReadError, AriosaError)
    assert issubclass(WriteError, AriosaError)
