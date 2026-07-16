# Ariosa Ventilation for Home Assistant

[![CI](https://github.com/boroczkigabor/ha-ariosa-integration/actions/workflows/ci.yml/badge.svg)](https://github.com/boroczkigabor/ha-ariosa-integration/actions/workflows/ci.yml)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A Home Assistant custom integration for **Ariosa** heat-recovery ventilation
units, connecting over **Modbus TCP** to poll temperature, humidity, and
operational data.

## Features

> [!WARNING]
> This is still very much a work-in-progress, vibe-coded thingy.
> Even though it only pulls data from the device and does not write
> anything back, use with caution. 

- UI-based setup (config flow) — no YAML required
- Polls the unit every 10 seconds over Modbus TCP
- Exposes 13 sensors covering temperatures, humidity, motor speeds, and
  maintenance counters
- Available in English and Hungarian

## Requirements

- Home Assistant 2026.1.0 or newer
- Network access from Home Assistant to the ventilation unit's Modbus TCP
  interface (default port `502`)

## Supported devices
The integration surely works with the following devices:
- Valsir Ariosa HV 330 Enthalpic

Feel free to confirm support for this integration on this issue: [1](https://github.com/boroczkigabor/ha-ariosa-integration/issues/1)

## Installation

### HACS (recommended)

This integration isn't in the default HACS store yet, so it needs to be
added as a custom repository:

1. In Home Assistant, open **HACS**.
2. Click the **⋮** menu in the top right and choose **Custom repositories**.
3. Add `https://github.com/boroczkigabor/ha-ariosa-integration` as the
   repository URL, with category **Integration**.
4. Find **Ariosa Ventilation** in HACS and click **Download**.
5. Restart Home Assistant.

### Manual

1. Copy the `custom_components/ariosa` folder from this repository into
   your Home Assistant `config/custom_components/` directory, so you end
   up with `config/custom_components/ariosa/`.
2. Restart Home Assistant.

## Configuration

Configuration is done entirely through the UI:

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Ariosa Ventilation**.
3. Enter the connection details:

   | Field | Description                                    | Default |
   |-------|------------------------------------------------|---------|
   | Host  | IP address or hostname of the ventilation unit | —       |
   | Port  | Modbus TCP port                                | `502`   |

4. Home Assistant will attempt to connect and read the unit's registers
   before creating the entry — if this fails, double-check the host/port
   and that the device's Modbus TCP interface is reachable from Home
   Assistant (firewall rules, same network/VLAN, etc.).

Multiple ventilation units can be added by repeating the process with a
different host.

## Entities

| Sensor               | Unit | Notes                          |
|----------------------|------|--------------------------------|
| External temperature | °C   | Outdoor air                    |
| External humidity    | %    | Outdoor air                    |
| Ejection temperature | °C   | Air expelled outside           |
| Ejection humidity    | %    | Air expelled outside           |
| Internal temperature | °C   | Room air extracted             |
| Internal humidity    | %    | Room air extracted             |
| Flow temperature     | °C   | Supply air into the room       |
| Flow humidity        | %    | Supply air into the room       |
| Motor 1 speed        | rpm  |                                |
| Motor 2 speed        | rpm  |                                |
| Post treatment       | %    |                                |
| Machine days         | d    | Total running days             |
| Filter hours         | h    | Hours since last filter change |

## Contributing

Issues and pull requests are welcome — see the
[issue tracker](https://github.com/boroczkigabor/ha-ariosa-integration/issues).

Running the test suite locally:

```bash
pip install -r requirements_dev.txt
ruff check . --output-format=full
ruff format --check --diff .
pytest
```

## License

Licensed under the [Apache License 2.0](LICENSE).