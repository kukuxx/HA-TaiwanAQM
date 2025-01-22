from datetime import timedelta
from homeassistant.const import Platform
from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass

DOMAIN = "taiwan_aqm"
CONF_API_KEY = "api_key"
CONF_SITEID = "siteID"
COORDINATOR = "COORDINATOR"
API_KEY = "API_KEY"
SITEID = "SITEID"
TASK = "TIMER_TASK"
API_URL = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
HA_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HomeAssistant/HA-TaiwanAQM"
UPDATE_INTERVAL = timedelta(minutes=11)
PLATFORM = [Platform.SENSOR]

SITEID_DICT = {
    "基隆市基隆": "1",
    "新北市汐止": "2",
    "新北市萬里": "3",
    "新北市新店": "4",
    "新北市土城": "5",
    "新北市板橋": "6",
    "新北市新莊": "7",
    "新北市菜寮": "8",
    "新北市林口": "9",
    "新北市淡水": "10",
    "新北市三重": "67",
    "新北市永和": "70",
    "新北市富貴角": "84",
    "新北市樹林": "311",
    "台北市士林": "11",
    "台北市中山": "12",
    "台北市萬華": "13",
    "台北市古亭": "14",
    "台北市松山": "15",
    "台北市大同": "16",
    "台北市陽明": "64",
    "桃園市桃園": "17",
    "桃園市大園": "18",
    "桃園市觀音": "19",
    "桃園市平鎮": "20",
    "桃園市龍潭": "21",
    "桃園市中壢": "68",
    "新竹縣湖口": "22",
    "新竹縣竹東": "23",
    "新竹市新竹": "24",
    "苗栗縣頭份": "25",
    "苗栗縣苗栗": "26",
    "苗栗縣三義": "27",
    "臺中市豐原": "28",
    "臺中市沙鹿": "29",
    "臺中市大里": "30",
    "臺中市忠明": "31",
    "臺中市西屯": "32",
    "彰化縣彰化": "33",
    "彰化縣線西": "34",
    "彰化縣二林": "35",
    "彰化縣大城": "85",
    "彰化縣員林": "139",
    "南投縣南投": "36",
    "南投縣竹山": "69",
    "南投縣埔里": "72",
    "雲林縣斗六": "37",
    "雲林縣崙背": "38",
    "雲林縣臺西": "41",
    "雲林縣麥寮": "83",
    "嘉義縣新港": "39",
    "嘉義縣朴子": "40",
    "嘉義市嘉義": "42",
    "台南市新營": "43",
    "台南市善化": "44",
    "台南市安南": "45",
    "台南市臺南": "46",
    "台南市麻豆": "203",
    "高雄市美濃": "47",
    "高雄市橋頭": "48",
    "高雄市仁武": "49",
    "高雄市鳳山": "50",
    "高雄市大寮": "51",
    "高雄市林園": "52",
    "高雄市楠梓": "53",
    "高雄市左營": "54",
    "高雄市前金": "56",
    "高雄市前鎮": "57",
    "高雄市小港": "58",
    "高雄市復興": "71",
    "高雄市湖內": "202",
    "屏東縣屏東": "59",
    "屏東縣潮州": "60",
    "屏東縣枋山": "313",
    "屏東縣恆春": "61",
    "屏東縣琉球": "204",
    "臺東縣臺東": "62",
    "臺東縣關山": "80",
    "花蓮縣花蓮": "63",
    "花蓮縣美崙": "312",
    "宜蘭縣宜蘭": "65",
    "宜蘭縣冬山": "66",
    "宜蘭縣頭城": "201",
    "澎湖縣馬公": "78",
    "金門縣金門": "77",
    "連江縣馬祖": "75",
}

SITENAME_DICT = {v: k for k, v in SITEID_DICT.items()}

SENSOR_INFO = {
    "aqi": {
        "dc": SensorDeviceClass.AQI,
        "unit": None,
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": None,
    },
    "pollutant": {
        "dc": None,
        "unit": None,
        "sc": None,
        "dp": None,
        "icon": "mdi:smog",
    },
    "status": {
        "dc": None,
        "unit": None,
        "sc": None,
        "dp": None,
        "icon": "mdi:nature-people-outline",
    },
    "publishtime": {
        "dc": None,
        "unit": None,
        "sc": None,
        "dp": None,
        "icon": "mdi:update",
    },
    "so2": {
        "dc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        "unit": "ppb",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": "mdi:molecule",
    },
    "so2_avg": {
        "dc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        "unit": "ppb",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": "mdi:molecule",
    },
    "co": {
        "dc": SensorDeviceClass.CO,
        "unit": "ppm",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": None,
    },
    "co_8hr": {
        "dc": SensorDeviceClass.CO,
        "unit": "ppm",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": None,
    },
    "o3": {
        "dc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        "unit": "ppb",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": "mdi:molecule",
    },
    "o3_8hr": {
        "dc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        "unit": "ppb",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": "mdi:molecule",
    },
    "no2": {
        "dc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        "unit": "ppb",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": "mdi:molecule",
    },
    "nox": {
        "dc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        "unit": "ppb",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": "mdi:molecule",
    },
    "no": {
        "dc": SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS_PARTS,
        "unit": "ppb",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": "mdi:molecule",
    },
    "pm10": {
        "dc": SensorDeviceClass.PM10,
        "unit": "µg/m³",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": None,
    },
    "pm10_avg": {
        "dc": SensorDeviceClass.PM10,
        "unit": "µg/m³",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": None,
    },
    "pm2.5": {
        "dc": SensorDeviceClass.PM25,
        "unit": "µg/m³",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": None,
    },
    "pm2.5_avg": {
        "dc": SensorDeviceClass.PM25,
        "unit": "µg/m³",
        "sc": SensorStateClass.MEASUREMENT,
        "dp": 2,
        "icon": None,
    },
}
