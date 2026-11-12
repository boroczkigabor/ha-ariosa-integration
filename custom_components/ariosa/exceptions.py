"""Exceptions for the Ariosa integration."""


class AriosaError(Exception):
    """Base exception for Ariosa."""


class CannotConnect(AriosaError):
    """Unable to connect to the device."""


class ReadError(AriosaError):
    """Unable to read Modbus registers."""


class WriteError(AriosaError):
    """Unable to write a Modbus register (e.g. Modbus control is disabled)."""
