
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


# HA-TaiwanAQM

- [English](/README.md) | [繁體中文](/README-zh-TW.md)

> <b>This integration can monitor air quality across Taiwan.<br>
> The data source is the <a href='https://data.moenv.gov.tw/'>Environmental Data Open Platform API of the Taiwan Ministry of the Environment</a>.<br>
> Before using the integration, remember to first become a member and apply for an API KEY.</b>

>[!Important]
> The API KEY is <b>valid for only 1 year</b>. If the <b>API KEY expires</b>, please <b>follow the instructions in the email</b> you received when you became a member to reapply for a new API KEY.

> [!Tip]
> If you encounter a bug during use, <br>
> please enable <b>debug mode</b> in the integration and try the original operation, <br>
> then open issues and post the log.

## Instructions for use

- It is recommended to use <b>HACS</b> to install. If you want to install manually,please put the <b>taiwan_aqm</b> folder in <b>custom_components</b> folder, and restart <b>Home assistant</b>.
<br>After the restart is completed, search for <b>Taiwan Air Quality Monitor</b> in the integration and set it up.

  [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-TaiwanAQM&category=Integration)

## Credits

- This project is forked from <a href='https://github.com/besthand/TaiwanAQI'>besthand/TaiwanAQI</a>