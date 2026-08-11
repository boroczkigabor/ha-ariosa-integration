# Ariosa Ventilation for Home Assistant

[![CI](https://github.com/boroczkigabor/ha-ariosa-integration/actions/workflows/ci.yml/badge.svg)](https://github.com/boroczkigabor/ha-ariosa-integration/actions/workflows/ci.yml)
[![HACS Custom Repository](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/docs/faq/custom_repositories/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

A Home Assistant custom integration for **Ariosa** heat-recovery ventilation
units, connecting over **Modbus TCP** to poll temperature, humidity, and
operational data.

## Features

- UI-based setup (config flow) — no YAML required
- Polls the unit every 10 seconds over Modbus TCP
- Exposes 13 sensors covering temperatures, humidity, motor speeds, and
  maintenance counters
- Three additional **calculated sensors** derived from the temperature
  data: supply-side and exhaust-side heat recovery efficiency, and the
  imbalance between the two
- An optional **temperature waste sensor**, comparing the internal
  temperature against a reference temperature entity of your choice
- A **season sensor** reporting the unit's configured operating mode
  (Automatic / Winter)
- Two **status binary sensors** for the preheater and the heat exchanger
  bypass
- **Nine alarm binary sensors** for fault conditions, automatically
  grouped together in a collapsible *Diagnostic* section on the device's
  card
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

   | Field                        | Description                                                                                                    | Default    |
      |------------------------------|----------------------------------------------------------------------------------------------------------------|------------|
   | Host                         | IP address or hostname of the ventilation unit                                                                 | —          |
   | Port                         | Modbus TCP port                                                                                                | `502`      |
   | Reference temperature entity | Optional — an existing temperature entity to compare against. See [below](#temperature-waste-sensor-optional). | — (none)   |

4. Home Assistant will attempt to connect and read the unit's registers
   before creating the entry — if this fails, double-check the host/port
   and that the device's Modbus TCP interface is reachable from Home
   Assistant (firewall rules, same network/VLAN, etc.).

Multiple ventilation units can be added by repeating the process with a
different host.

### Changing settings later

The reference temperature entity can be set, changed, or cleared at any
time without re-adding the integration:

**Settings → Devices & Services → Ariosa Ventilation → Configure**

Saving reloads the entry automatically, so the temperature waste sensor
appears or disappears immediately to match.

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

### Season sensor

| Sensor | Possible states   | Notes                                                                                |
|--------|-------------------|--------------------------------------------------------------------------------------|
| Season | Automatic, Winter | The unit's configured operating mode, read directly from the device — not calculated |

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

### Temperature waste sensor (optional)

If a **reference temperature entity** is configured (see
[Configuration](#configuration)), an additional sensor is created:

| Sensor                          | Unit | Formula                                | Notes                                                                                                                                                 |
|---------------------------------|------|----------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------|
| Temperature waste vs. reference | °C   | `\|Internal temperature − reference\|` | How far the extracted room air deviates from whatever reference you're tracking — e.g. a thermostat's target or setpoint, or a sensor in another room |

Notes on how it behaves:

- Not tied to a specific reference entity type — anything reporting a
  numeric temperature-like state works, e.g. a room thermostat's current
  or target temperature, another integration's temperature sensor, or a
  `sensor` created by a template/helper.
- Works correctly with negative values and across 0 °C in either
  direction — it's a plain absolute difference, so the sign of the
  internal temperature, the reference, or both doesn't matter.
- Updates immediately when the reference entity changes, not just on the
  unit's regular poll.
- Reports as *unknown* while the reference entity is unavailable, unknown,
  or has a non-numeric state, rather than showing a stale or misleading
  value.
- Without a reference entity configured, this sensor simply doesn't
  exist — it isn't shown as unavailable.

### Binary sensors

| Sensor           | Notes                                               |
|------------------|-----------------------------------------------------|
| Preheater status | Whether the electric preheater is currently running |
| Bypass active    | Whether the heat exchanger bypass is open           |

### Alarm sensors

Nine alarm sensors surface fault conditions reported by the unit itself.
Exact trigger conditions are determined by the device's own firmware —
consult your unit's documentation for specifics.

| Sensor                 | Notes                                                        |
|------------------------|--------------------------------------------------------------|
| General alarm          | A fault condition not covered by a more specific alarm below |
| Filter change alarm    | The filter is due for replacement                            |
| Filter clogged alarm   | The filter is clogged, restricting airflow                   |
| Frost protection alarm | The unit's frost-protection mechanism has triggered          |
| Connection alarm       | A communication fault with the unit                          |
| Motor alarm            | A fault reported by one of the motors                        |
| Sensor alarm           | One of the unit's internal sensors is reporting a fault      |
| Motor protection alarm | Motor protection has cut in (e.g. overcurrent/thermal)       |
| Preheater alarm        | A fault on the electric preheater                            |

All nine share two things by design:

- **Device class `problem`** — shown as *Problem detected* / *OK* with a
  warning icon when active, instead of a generic on/off toggle.
- **Entity category `diagnostic`** — Home Assistant automatically groups
  every diagnostic entity together in its own collapsible section on the
  device's card, separate from the primary sensors above. This is what
  keeps all nine alarms visually together without any dashboard setup.

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
