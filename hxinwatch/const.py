# hxinwatch/const.py
"""HXinWatch集成的常量。"""

DOMAIN = "hxinwatch"

# 默认配置
DEFAULT_SCAN_INTERVAL = 300  # 5分钟

# 设备类型
DEVICE_TYPE_WATCH = "watch"

# 传感器类型
SENSOR_TYPE_BATTERY = "battery"
SENSOR_TYPE_HEART_RATE = "heart_rate"
SENSOR_TYPE_BLOOD_PRESSURE = "blood_pressure"
SENSOR_TYPE_OXYGEN = "oxygen"
SENSOR_TYPE_TEMPERATURE = "temperature"
SENSOR_TYPE_STEPS = "steps"
# 新增的传感器类型
SENSOR_TYPE_CONTACT_COUNT = "contact_count" # 新增
SENSOR_TYPE_ALARM_COUNT = "alarm_count"     # 新增

# 二进制传感器类型
BINARY_SENSOR_TYPE_ONLINE = "online"
BINARY_SENSOR_TYPE_LOW_BATTERY = "low_battery"

# 服务名称
SERVICE_ADD_CONTACT = "add_contact"
SERVICE_DELETE_CONTACT = "delete_contact"
SERVICE_ADD_ALARM = "add_alarm"
SERVICE_DELETE_ALARM = "delete_alarm"