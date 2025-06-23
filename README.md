# 华芯沃 (HXinWatch) Home Assistant 集成
## 本集成由AI参与生成

这是一个 Home Assistant 自定义集成，用于连接和控制华芯沃 (HXinWatch) 智能手表设备，提供设备状态监控和远程控制功能。

## ✨ 功能特性
- **设备状态监控**：
  - **传感器**：实时获取电池电量、心率、血氧饱和度、体温、步数、通讯录数量和闹钟数量。
  - **二进制传感器**：监控设备是否处于低电量状态。
  - **设备追踪器**：获取设备的实时位置（经纬度、地址），并在地图上显示。
- **Token 自动刷新**：无需手动更新 Token，集成会根据 AppID 自动获取和刷新 Token，确保连接持续有效。
- **通讯录管理服务**：
  - `hxinwatch.add_contact`：向手表添加新的联系人。
  - `hxinwatch.delete_contact`：删除手表中的指定联系人。
- **闹钟管理服务**：
  - `hxinwatch.add_alarm`：向手表添加新的闹钟。
  - `hxinwatch.delete_alarm`：删除手表中的指定闹钟。
- **可配置的刷新间隔**：在集成设置中自定义数据更新的频率（1-60 秒）。

## 🚀 安装
### 手动安装
1. 将 `custom_components/hxinwatch` 文件夹复制到您的 Home Assistant 配置目录下的 `custom_components` 文件夹中。  
   例如：`<config_directory>/custom_components/hxinwatch/`
2. 重启 Home Assistant。

### 通过 HACS 安装（推荐）
1. 确保您已经安装了 [HACS](https://hacs.xyz/)。
2. 在 Home Assistant 中，导航到 **HACS** -> **集成 (Integrations)**。
3. 点击右下角的 **Explore & Download Repositories** (或 **+** 号)，然后选择 **Custom repositories**。
4. 在 `Add custom repository` 对话框中：
   - **Repository**：填写仓库地址 `https://github.com/hlhk2017/hxinwatch-homeassistant`。
   - **Category**：选择 `Integration`。
   - 点击 `ADD`。
5. 在 HACS 中搜索 `华芯沃` 或 `HXinWatch`，然后点击下载。
6. 重启 Home Assistant。

## ⚙️ 配置
重启 Home Assistant 后，您可以通过 UI 配置此集成：
1. 导航到 **设置 (Settings)** -> **设备与服务 (Devices & Services)**。
2. 点击右下角的 **添加集成 (Add Integration)**。
3. 搜索 `华芯沃` 或 `HXinWatch` 并选择它。
4. 按照提示输入以下信息：
   - **IMEI**：设备的 IMEI 号码。
   - **AppID**：您的华芯沃 API 应用 ID。请参考下方 **“AppID 获取方式”** 部分获取。
   - **语言 (可选)**：API 请求的语言，默认为 `zh-Hans` (简体中文)。
   - **刷新时间 (可选)**：数据更新的间隔秒数（范围 1-60），默认为 30 秒。
5. 点击 **提交 (Submit)** 完成配置。

### AppID 获取方式
`AppID` 是用于华芯沃 API 认证的关键参数。您可以按照以下步骤通过抓包工具获取：
1. 在您的手机上，打开微信并进入华芯沃智能手表相关的服务号、小程序或网页（通常是您日常管理手表的入口）。
2. 使用专业的抓包工具（如 [Fiddler](https://www.telerik.com/fiddler)、[Charles](https://www.charlesproxy.com/)、[Proxyman](https://proxyman.io/) 或 [Reqable](https://reqable.com/)）代理您手机的网络流量。
3. 在抓包工具中，监控网络请求，查找目标主机为 `yg.hxinwatch.com` 的请求。
4. 找到一个类似 `GET http://yg.hxinwatch.com/sdkapi/api/wechat/auth?appid=YOUR_APPID_HERE&...` 的请求。
5. 从该请求的 URL 参数中，提取 `appid` 的值。这个值通常是固定的，您只需获取一次即可。

## 🔧 服务
集成提供了多个服务，您可以在自动化、脚本或开发者工具中调用它们。

**重要提示**：所有服务都需要通过 `entity_id` 或 `entry_id` 参数来指定目标设备，以便集成知道对哪个 HXinWatch 设备执行操作。
- **推荐方式（通过实体 ID）**：  
  选择该集成下任意一个实体（例如`sensor.your_device_name_battery_level` 或 `device_tracker.your_device_name_location`）的 `entity_id` 作为服务调用的目标。系统会自动识别其所属的配置条目。
- **直接方式（通过配置入口 ID）**：  
  如果您知道 `ConfigEntry ID`（可以通过查看该集成下的任何设备的“设备信息”页面，点击“配置条目”链接，在 URL 中找到 `config_entry=YOUR_ENTRY_ID`），也可以直接提供 `entry_id`。

### `hxinwatch.add_contact` (添加联系人)
向手表添加一个新的联系人。

| 参数        | 类型   | 必填 | 描述                          |
| ----------- | ------ | ---- | ----------------------------- |
| `entity_id` | string | 是   | 关联的 HXinWatch 实体 ID。    |
| `entry_id`  | string | 否   | HXinWatch 集成的配置入口 ID。 |
| `name`      | string | 是   | 联系人姓名。                  |
| `phone`     | string | 是   | 联系人电话号码。              |

**示例 YAML：**
```yaml
action:
  - service: hxinwatch.add_contact
    data:
      entity_id: sensor.hxinwatch_device_battery_level  # 替换为您的 HXinWatch 实体 ID
      name: "华芯沃测试"
      phone: "13812345678"
```

### `hxinwatch.delete_contact` (删除联系人)
从手表中删除一个联系人。

| 参数        | 类型   | 必填 | 描述                          |
| ----------- | ------ | ---- | ----------------------------- |
| `entity_id` | string | 是   | 关联的 HXinWatch 实体 ID。    |
| `entry_id`  | string | 否   | HXinWatch 集成的配置入口 ID。 |
| `contact_id`| integer| 是   | 要删除的联系人 ID（从通讯录传感器属性中获取）。 |

**示例 YAML：**
```yaml
action:
  - service: hxinwatch.delete_contact
    data:
      entity_id: sensor.hxinwatch_device_battery_level  # 替换为您的 HXinWatch 实体 ID
      contact_id: 12345  # 替换为实际的联系人 ID
```

### `hxinwatch.add_alarm` (添加闹钟)
向手表添加一个新的闹钟。

**示例 YAML：**
```yaml
# 工作日闹钟（07:30，周一至周五重复）
action:
  - service: hxinwatch.add_alarm
    data:
      entity_id: sensor.hxinwatch_device_battery_level  # 替换为您的 HXinWatch 实体 ID
      name: "工作日闹钟"
      time: "07:30"
      week: ["mon", "tue", "wed", "thu", "fri"]  # 工作日重复
      status: 1

# 周末起床（09:00，周六、周日重复）
action:
  - service: hxinwatch.add_alarm
    data:
      entity_id: sensor.hxinwatch_device_battery_level  # 替换为您的 HXinWatch 实体 ID
      name: "周末起床"
      time: "09:00"
      week: ["周六", "周日"]  # 周末重复
      status: 1

# 每天提醒（12:00，每天重复）
action:
  - service: hxinwatch.add_alarm
    data:
      entity_id: sensor.hxinwatch_device_battery_level  # 替换为您的 HXinWatch 实体 ID
      name: "每天提醒"
      time: "12:00"
      week: [1, 2, 3, 4, 5, 6, 7]  # 每天重复（1-7 代表周一至周日）
      status: 1

# 单次提醒（10:00，不重复）
action:
  - service: hxinwatch.add_alarm
    data:
      entity_id: sensor.hxinwatch_device_battery_level  # 替换为您的 HXinWatch 实体 ID
      name: "单次提醒"
      time: "10:00"
      week: []  # 不重复（默认值，可省略）
      status: 1
```

### `hxinwatch.delete_alarm` (删除闹钟)
从手表中删除一个闹钟。

| 参数        | 类型   | 必填 | 描述                          |
| ----------- | ------ | ---- | ----------------------------- |
| `entity_id` | string | 是   | 关联的 HXinWatch 实体 ID。    |
| `entry_id`  | string | 否   | HXinWatch 集成的配置入口 ID。 |
| `alarm_id`  | string | 是   | 要删除的闹钟 ID（从闹钟数量传感器属性中获取）。 |

**示例 YAML：**
```yaml
action:
  - service: hxinwatch.delete_alarm
    data:
      entity_id: sensor.hxinwatch_device_battery_level  # 替换为您的 HXinWatch 实体 ID
      alarm_id: "5942"  # 替换为实际的闹钟 ID
```

## 🔍 实体
集成加载后，会自动创建以下类型的实体：
### 传感器 (Sensor)
- `sensor.your_device_name_battery_level`（电池电量）
- `sensor.your_device_name_heart_rate`（心率）
- `sensor.your_device_name_oxygen_saturation`（血氧饱和度）
- `sensor.your_device_name_temperature`（体温）
- `sensor.your_device_name_steps`（步数）
- `sensor.your_device_name_contact_count`（通讯录数量）- 包含 `contacts` 属性，列出详细通讯录条目。
- `sensor.your_device_name_alarm_count`（闹钟数量）- 包含 `alarms` 属性，列出详细闹钟条目，其中的 `week_readable` 属性会以人类可读的方式显示重复周期。

### 二进制传感器 (Binary Sensor)
- `binary_sensor.your_device_name_battery_low`（低电量）

### 设备追踪器 (Device Tracker)
- `device_tracker.your_device_name_location`（设备位置）- 包含经纬度、地址和电池电量属性。

> 其中 `your_device_name` 会根据您设备在华芯沃平台上的名称自动生成，例如 `an_an`。

## 🐞 调试与故障排除
如果遇到问题，请检查 Home Assistant 的日志。

### 启用调试日志
在您的 `configuration.yaml` 文件中添加以下内容，然后重启 Home Assistant：
```yaml
logger:
  default: info
  logs:
    custom_components.hxinwatch: debug
```

### 查看日志
检查 Home Assistant 日志文件 (`home-assistant.log`) 或通过 UI 中的 **设置 (Settings)** -> **系统 (System)** -> **日志 (Logs)** 查看详细信息。

## 📄 许可证
本项目遵循 MIT 许可证。
