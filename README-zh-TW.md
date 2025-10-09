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

# 🌏 台灣空氣品質監測器

**在 Home Assistant 中即時監控台灣空氣品質**

[English](/README.md) | [繁體中文](/README-zh-TW.md)

---

## 📋 概述

此整合提供全面的台灣空氣品質監測功能，同時支援**標準監測站**和**微型空氣品質感測器**。資料來源為[台灣環境部環境資料開放平台 API](https://data.moenv.gov.tw/)。

> [!IMPORTANT]
> **需要 API Key**:使用此整合前，您必須先註冊成為會員並申請 API KEY。
>
> **API Key 有效期限**:API KEY 的有效期限為 **1 年**。

> [!TIP]
> **除錯模式**:如果使用過程中遇到問題,請在整合設定中啟用**偵錯模式**,重現問題後,開啟 issue 並附上 log 檔案。

---

## ✨ 功能特色

### 🎯 雙重監測支援
- **標準監測站**:存取台灣官方空氣品質監測網路的資料
- **微型空氣品質感測器**:監測各地部署的智慧城鄉空氣品質微型感測器資料

### 📊 完整的空氣品質指標

**標準監測站**提供:
- PM2.5 (細懸浮微粒)
- PM10 (懸浮微粒)
- O₃ (臭氧)
- CO (一氧化碳)
- SO₂ (二氧化硫)
- NO₂ (二氧化氮)
- AQI (空氣品質指標)
- 風速與風向

**微型空氣品質感測器**提供:
- PM2.5 (細懸浮微粒)
- 溫度
- 濕度

---

## 📦 安裝方式

### 方法一:HACS (建議)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=kukuxx&repository=HA-TaiwanAQM&category=Integration)

1. 在 Home Assistant 中開啟 HACS
2. 搜尋 "Taiwan Air Quality Monitor"
3. 點擊 "下載"
4. 重新啟動 Home Assistant

### 方法二:手動安裝

1. 從此儲存庫下載 `taiwan_aqm` 資料夾
2. 複製到您的 `custom_components` 目錄
3. 重新啟動 Home Assistant

---

## 🚀 設定指南

### 初始設定

1. 前往 **設定** → **裝置與服務**
2. 點擊 **新增整合**
3. 搜尋 **Taiwan Air Quality Monitor**
4. 輸入您從環境資料開放平台取得的 **API KEY**
5. 點擊 **提交**

### 新增監測站

完成初始設定後,您可以新增監測站:

1. 前往您的 **Taiwan Air Quality Monitor** 整合
2. 點擊 **設定** 或 **新增項目**
3. 選擇類型:
   - **新增監測站**:用於標準空氣品質監測站
   - **新增微型感測器**:用於微型空氣品質感測器
4. 從下拉選單中選擇站點
5. 點擊 **提交**

### 管理站點

- **檢視站點**:所有已設定的站點會顯示為主整合下的子項目
- **移除站點**:點擊任何站點旁的垃圾桶圖示即可移除該站點及其實體

---

## 🔍 疑難排解

### 新增站點後實體未出現

1. 等待 1-2 秒讓自動重新載入完成
2. 檢查 Home Assistant 日誌是否有錯誤
3. 嘗試手動重新載入整合
4. 確認您的 API KEY 有效且未過期

### API Key 過期

1. 請依照註冊時收到的 email 指示重新申請新的 API KEY。
2. 在整合設定中更新 API KEY

### 偵錯模式

在 `configuration.yaml` 中新增以下內容以啟用偵錯日誌:

```yaml
logger:
  default: info
  logs:
    custom_components.taiwan_aqm: debug
```

---

## 🤝 貢獻

歡迎貢獻!請隨時提交 Pull Request。

---

## 📄 授權

此專案採用 Apache 2.0 授權 - 詳見 [LICENSE](LICENSE) 檔案。

---

## 🙏 致謝

- 從 [besthand/TaiwanAQI](https://github.com/besthand/TaiwanAQI) 修改而來
- 資料由[台灣環境部](https://data.moenv.gov.tw/)提供

---

## 📞 支援

如果您遇到任何問題或有疑問:

1. 查看 [Issues](https://github.com/kukuxx/HA-TaiwanAQM/issues) 頁面
2. 啟用偵錯模式並收集日誌
3. 開啟新的 issue 並提供詳細資訊

---