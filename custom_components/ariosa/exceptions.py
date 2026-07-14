"""Exceptions for the Ariosa integration."""


class AriosaError(Exception):
    """Base exception for Ariosa."""


class CannotConnect(AriosaError):
    """Unable to connect to the device."""


class ReadError(AriosaError):
    """Unable to read Modbus registers."""
