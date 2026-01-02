# Bergfex Snow Report Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=flat-square)](https://github.com/hacs/integration)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/timmaurice/bergfex?style=flat-square)
[![GH-downloads](https://img.shields.io/github/downloads/timmaurice/bergfex/total?style=flat-square)](https://github.com/timmaurice/bergfex/releases)
[![GH-last-commit](https://img.shields.io/github/last-commit/timmaurice/bergfex.svg?style=flat-square)](https://github.com/timmaurice/bergfex/commits/master)
[![GH-code-size](https://img.shields.io/github/languages/code-size/timmaurice/bergfex.svg?style=flat-square)](https://github.com/timmaurice/bergfex)
![GitHub](https://img.shields.io/github/license/timmaurice/bergfex?style=flat-square)

This custom integration for Home Assistant fetches snow reports and ski resort data directly from [Bergfex](https://www.bergfex.com). Since Bergfex does not provide a public API, this component scrapes the data from their website.

*   **Multi-language Support**: Use Bergfex in your preferred language. Now supporting **18 languages** with full keyword parsing and translation:
    *   **Major**: German, English, French, Italian, Spanish, Dutch
    *   **Scandinavian**: Swedish, Norwegian, Danish, Finnish
    *   **Slavic/Central**: Czech, Slovak, Polish, Slovenian, Croatian
    *   **Others**: Hungarian, Romanian, Russian
*   **Dynamic Domain Mapping**: Automatically uses the correct Bergfex domain (e.g., .at, .com, .fr, .it) based on your language selection.
*   **Enhanced Localization**: data values (like "Powder", "Open", "Moderate") are automatically translated into your selected language.
*   **Multi-Country Support**: Select ski areas from various European countries including Austria, Germany, Switzerland, Italy, France, and others.
*   **Efficient Polling**: Fetches data for an entire region/country efficiently, shared across all sensors.
*   **Device per Ski Area**: Creates a dedicated device in Home Assistant for each monitored ski area.
*   **Detailed Sensors**: Provides comprehensive sensors for snow depths, lift status, slope conditions, and avalanche warnings.

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
3.  **Step 1: Select Language**: Choose your preferred language. This will determine the Bergfex domain used (e.g., English -> bergfex.com, French -> bergfex.fr).
4.  **Step 2: Select Country**: Select the country where your desired ski area is located.
5.  **Step 3: Select Ski Area**: Choose a ski area from the list.
    *   **Manual Entry**: If your desired ski area is not in the list, you can manually enter its URL path (e.g., `nebelhorn-oberstdorf` or `lelex-crozet`) in the "Manual URL Path" field.
6.  Click **Submit**.

A new device will be created for the ski area, containing all the sensors listed below. You can repeat this process to add multiple ski areas.

## Created Sensors

For each configured ski area, the following sensors will be created:

| Sensor            | Description                                   | Example Value         |
| ----------------- | --------------------------------------------- | --------------------- |
| **Status**            | The current operational status of the resort. | `Open`                |
| **Snow Valley**       | Snow depth in the valley, in cm.              | `35`                  |
| **Snow Mountain**     | Snow depth on the mountain, in cm.            | `110`                 |
| **New Snow**          | Fresh snow in the last 24h, in cm.            | `15`                  |
| **Snow Condition**    | Condition of the snow.                        | `Pulver`              |
| **Last Snowfall**     | Date of the last snowfall.                    | `28.11.`              |
| **Avalanche Warning** | Current avalanche warning level.              | `2 - mäßig`           |
| **Lifts Open**        | The number of currently open lifts.           | `14`                  |
| **Lifts Total**       | The total number of lifts in the resort.      | `26`                  |
| **Slopes Open (km)**  | Kilometers of open slopes.                    | `45.5`                |
| **Slopes Total (km)** | Total kilometers of slopes.                   | `60`                  |
| **Slopes Open**       | Number of open slopes.                        | `20`                  |
| **Slopes Total**      | Total number of slopes.                       | `30`                  |
| **Slope Condition**   | Condition of the slopes.                      | `gut`                 |
| **Last Update**       | The timestamp of the last data report.        | `2024-10-28 21:54:24` |

## Image Entities

In addition to sensors, the integration provides image entities for snow forecasts. These can be displayed in dashboards using the Picture Entity card or similar.

| Entity                        | Description                                      |
| ----------------------------- | ------------------------------------------------ |
| **Snow Forecast Day 0-5**     | Daily snow forecast maps for the next 6 days.    |
| **Snow Forecast Summary Xh**  | Summary forecast maps (48h, 72h, 96h, 120h, 144h). |

## Contributions

Contributions are welcome! If you find a bug or have a feature request, please open an issue on the GitHub repository.

---

For further assistance or to [report issues](https://github.com/timmaurice/bergfex/issues), please visit the [GitHub repository](https://github.com/timmaurice/bergfex).

![Star History Chart](https://api.star-history.com/svg?repos=timmaurice/bergfex&type=Date)

## ☕ Support My Work

[<img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" height="30" />](https://www.buymeacoffee.com/timmaurice)
