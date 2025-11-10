# Bergfex Snow Report Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/timmaurice/bergfex?style=flat-square)
[![GH-downloads](https://img.shields.io/github/downloads/timmaurice/bergfex/total?style=flat-square)](https://github.com/timmaurice/bergfex/releases)
[![GH-last-commit](https://img.shields.io/github/last-commit/timmaurice/bergfex.svg?style=flat-square)](https://github.com/timmaurice/bergfex/commits/master)
[![GH-code-size](https://img.shields.io/github/languages/code-size/timmaurice/bergfex.svg?style=flat-square)](https://github.com/timmaurice/bergfex)
![GitHub](https://img.shields.io/github/license/timmaurice/bergfex?style=flat-square)

This custom integration for Home Assistant fetches snow reports and ski resort data directly from [Bergfex](https://www.bergfex.com). Since Bergfex does not provide a public API, this component scrapes the data from their website.

## Features

*   **Multi-Country Support**: Select ski areas from Austria, Germany, Switzerland, and more.
*   **Efficient Polling**: Fetches data for an entire country in a single request to minimize traffic, shared across all sensors for that country.
*   **Device per Ski Area**: Creates a dedicated device in Home Assistant for each monitored ski area.
*   **Detailed Sensors**: Provides sensors for key snow and lift data.

## Installation

### HACS (Recommended)

This card is available in the [Home Assistant Community Store (HACS)](https://hacs.xyz/).

<a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=timmaurice&repository=bergfex&category=integration" target="_blank" rel="noreferrer noopener"><img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open your Home Assistant instance and open a repository inside the Home Assistant Community Store." /></a>

<details>
<summary>Manual Installation</summary>

1.  Using the tool of your choice, copy the `bergfex` folder from `custom_components` in this repository into your Home Assistant's `custom_components` directory.
2.  Restart Home Assistant.
</details>

### Related lovelace card:
https://github.com/timmaurice/lovelace-bergfex-card

## Configuration

Configuration is done entirely through the Home Assistant UI.

1.  Go to **Settings** -> **Devices & Services**.
2.  Click **Add Integration** and search for "Bergfex Snow Report".
3.  **Step 1: Select Country**: A dialog will appear asking you to select the country where your desired ski area is located.
4.  **Step 2: Select Ski Area**: A second dialog will show a list of all ski areas in the selected country. Choose the one you want to monitor.
5.  Click **Submit**.

A new device will be created for the ski area, containing all the sensors listed below. You can repeat this process to add multiple ski areas.

## Created Sensors

For each configured ski area, the following sensors will be created:

| Sensor            | Description                                   | Example Value         |
| ----------------- | --------------------------------------------- | --------------------- |
| **Status**        | The current operational status of the resort. | `Open`                |
| **Snow Valley**   | Snow depth in the valley, in cm.              | `35`                  |
| **Snow Mountain** | Snow depth on the mountain, in cm.            | `110`                 |
| **New Snow**      | Fresh snow in the last 24h, in cm.            | `15`                  |
| **Lifts Open**    | The number of currently open lifts.           | `14`                  |
| **Lifts Total**   | The total number of lifts in the resort.      | `26`                  |
| **Last Update**   | The timestamp of the last data report.        | `2024-10-28 21:54:24` |

## Contributions

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository.

---

For further assistance or to [report issues](https://github.com/timmaurice/bergfex/issues), please visit the [GitHub repository](https://github.com/timmaurice/bergfex).

![Star History Chart](https://api.star-history.com/svg?repos=timmaurice/bergfex&type=Date)

## ☕ Support My Work

[<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" height="30" />](https://www.buymeacoffee.com/timmaurice)
