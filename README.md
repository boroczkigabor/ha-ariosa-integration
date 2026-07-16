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
- Three additional **calculated sensors** derived from the temperature
  data: supply-side and exhaust-side heat recovery efficiency, and the
  imbalance between the two
- A **binary sensor** that infers whether the heat exchanger bypass is
  likely active, based on temperature behavior
- Built-in [diagnostics](https://www.home-assistant.io/integrations/diagnostics/)
  support — download a snapshot of the config entry and latest readings
  for bug reports
- Available in English and Hungarian

## Requirements

- Home Assistant 2026.1.0 or newer
- Network access from Home Assistant to the ventilation unit's Modbus TCP
  interface (default port `502`)

## Supported devices

The integration surely works with the following devices:

- Valsir Ariosa HV 330 Enthalpic

Feel free to confirm support for this integration on this
issue: [1](https://github.com/boroczkigabor/ha-ariosa-integration/issues/1)

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

### Calculated sensors

These aren't read from the device — they're derived from the temperature
sensors above, using the standard heat-recovery temperature efficiency
formulas (ODA = outdoor/external, SUP = supply/flow, ETA = extract/
internal, EHA = exhaust/ejection).

| Sensor                                | Unit | Formula                           | Notes                                                                                                                      |
|---------------------------------------|------|-----------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| Supply-side heat recovery efficiency  | %    | `(SUP − ODA) / (ETA − ODA) × 100` | How much of the outdoor/room temperature gap the incoming air closed                                                       |
| Exhaust-side heat recovery efficiency | %    | `(ETA − EHA) / (ETA − ODA) × 100` | How much of that gap was recovered from the outgoing stale air                                                             |
| Heat recovery efficiency imbalance    | pts  | Supply-side − exhaust-side        | Near zero on a healthy unit; a growing gap can hint at a leak, unequal airflow, or sensor drift — not a diagnosis of which |

The formulas work the same whether the unit is recovering heat (winter,
outdoor colder than indoor) or recovering "coolness" (summer, outdoor
warmer than indoor) — only the ratio matters, not the direction of the
gap. All three report as *unknown* when the outdoor/room temperature
gap is too small (< 0.5 °C) for the math to be meaningful.

### Binary sensors

| Sensor        | Notes                                                                                                                                                                                                                                                                                                                                                                                                        |
|---------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| Bypass active | Best-effort guess at whether the heat exchanger bypass is engaged, inferred from both efficiency sensors collapsing toward zero at the same time. This is a heuristic based on temperature behavior, **not** a read of the unit's actual bypass state (its Modbus register isn't working yet) — a partially-open/modulating bypass, a defrost cycle, or sensor drift can look similar. Shown as Open/Closed. |

## Diagnostics

From **Settings → Devices & Services → Ariosa Ventilation → ⋮ → Download
diagnostics**, you can grab a snapshot containing the config entry's
connection details, the latest successful poll's measurements, and
whether the last update succeeded — handy to attach when reporting an
issue.

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
