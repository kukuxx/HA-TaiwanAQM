[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]

[contributors-shield]: https://img.shields.io/github/contributors/kukuxx/HA-TaiwanAQM.svg?style=for-the-badge
[contributors-url]: https://github.com/kukuxx/HA-TaiwanAQM/graphs/contributors

[forks-shield]: https://img.shields.io/github/forks/kukuxx/HA-TaiwanAQM.svg?style=for-the-badge
[forks-url]: https://github.com/kukuxx/HA-TaiwanAQM/network/members

[stars-shield]: https://img.shields.io/github/stars/kukuxx/HA-TaiwanAQM.svg?style=for-the-badge
[stars-url]: https://github.com/kukuxx/HA-TaiwanAQM/stargazers

[issues-shield]: https://img.shields.io/github/issues/kukuxx/HA-TaiwanAQM.svg?style=for-the-badge
[issues-url]: https://github.com/kukuxx/HA-TaiwanAQM/issues

[license-shield]: https://img.shields.io/github/license/kukuxx/HA-TaiwanAQM.svg?style=for-the-badge
[license-url]: https://github.com/kukuxx/HA-TaiwanAQM/blob/main/LICENSE

# 🌏 Taiwan Air Quality Monitor

**Monitor Taiwan's air quality in real-time with Home Assistant**

[English](/README.md) | [繁體中文](/README-zh-TW.md)

---

## 📋 Overview

This integration provides comprehensive air quality monitoring across Taiwan, supporting both **standard monitoring stations** and **micro air quality sensors**. Data is sourced from the [Taiwan Ministry of Environment's Environmental Data Open Platform API](https://data.moenv.gov.tw/).

> [!IMPORTANT]
> **API Key Required**: You must register as a member and apply for an API KEY before using this integration.
>
> **API Key Validity**: The API KEY is valid for **1 year only**.

> [!TIP]
> **Debugging**: If you encounter any issues, enable **debug mode** in the integration settings, reproduce the problem, then open an issue with the log file.

---

## ✨ Features

### 🎯 Dual Monitoring Support
- **Standard Monitoring Stations**: Access data from Taiwan's official air quality monitoring network
- **Micro Air Quality Sensors**: Monitor data from air quality micro sensors deployed across the country

### 📊 Comprehensive Air Quality Metrics

**Standard Monitoring Stations** provide:
- PM2.5 (Fine Particulate Matter)
- PM10 (Coarse Particulate Matter)
- O₃ (Ozone)
- CO (Carbon Monoxide)
- SO₂ (Sulfur Dioxide)
- NO₂ (Nitrogen Dioxide)
- AQI (Air Quality Index)
- Wind Speed & Direction

**Micro Air Quality Sensors** provide:
- PM2.5 (Fine Particulate Matter)
- Temperature
- Humidity

---

## 📦 Installation

### Method 1: HACS (Recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-TaiwanAQM&category=Integration)

1. Open HACS in your Home Assistant instance
2. Search for "Taiwan Air Quality Monitor"
3. Click "Download"
4. Restart Home Assistant

### Method 2: Manual Installation

1. Download the `taiwan_aqm` folder from this repository
2. Copy it to your `custom_components` directory
3. Restart Home Assistant

---

## 🚀 Setup Guide

### Initial Setup

1. Navigate to **Settings** → **Devices & Services**
2. Click **Add Integration**
3. Search for **Taiwan Air Quality Monitor**
4. Enter your **API KEY** from the Environmental Data Open Platform
5. Click **Submit**

### Adding Monitoring Stations

After initial setup, you can add monitoring stations:

1. Go to your **Taiwan Air Quality Monitor** integration
2. Click **Configure** or **Add Entry**
3. Choose the type:
   - **Add Monitoring Station**: For standard air quality monitoring stations
   - **Add Micro Sensor**: For micro air quality sensors
4. Select the station from the dropdown list
5. Click **Submit**

The entities will be automatically created within a few seconds!

### Managing Stations

- **View Stations**: All configured stations appear as subentries under the main integration
- **Remove Station**: Click the trash icon next to any station to remove it and its entities

---

## 🔍 Troubleshooting

### Entities Not Appearing After Adding Station

1. Wait 1-2 seconds for the automatic reload to complete
2. Check Home Assistant logs for any errors
3. Try manually reloading the integration
4. Ensure your API KEY is valid and not expired

### API Key Expired

1. Follow the instructions in your registration email to reapply for a new key.
2. Update the key in the integration settings

### Debug Mode

Enable debug logging by adding to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.taiwan_aqm: debug
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

## 📄 License

This project is licensed under the Apache 2.0 License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Credits

- Forked from [besthand/TaiwanAQI](https://github.com/besthand/TaiwanAQI)
- Data provided by [Taiwan Ministry of Environment](https://data.moenv.gov.tw/)

---

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/kukuxx/HA-TaiwanAQM/issues) page
2. Enable debug mode and collect logs
3. Open a new issue with detailed information

---