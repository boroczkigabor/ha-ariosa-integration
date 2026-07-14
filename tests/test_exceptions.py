from custom_components.ariosa.exceptions import (
    AriosaError,
    CannotConnect,
    ReadError,
)


def test_exception_inheritance() -> None:
    assert issubclass(CannotConnect, AriosaError)
    assert issubclass(ReadError, AriosaError)
