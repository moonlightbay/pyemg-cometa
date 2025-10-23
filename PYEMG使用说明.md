# pyemg-cometa 说明文档

Python 封装库：基于 pythonnet 调用 Cometa Waveplus .NET SDK，对 sEMG/IMU/Foot Switch 等采集流程提供更“pythonic”的接口。当前仅支持 Windows。

## 项目简介
- 目标：为 Cometa Waveplus 系列设备提供 Python 访问，覆盖设备状态、采样配置、事件订阅、数据读取（EMG/IMU/FSW/同步信号）等能力。
- 技术路线：使用 `pythonnet` 加载随包分发的 .NET DLL（见 `src/pyemg_cometa/lib`），对类型与方法进行轻量封装，统一返回 Python 友好的枚举/数据结构。
- 适用场景：在线采集、事件驱动的数据处理、基础工具/算法原型开发、科研实验脚本化。

## 文件结构
```
pyemg-cometa/
├─ src/pyemg_cometa/
│  ├─ lib/                         # 随发行的 .NET 依赖（Cometa SDK 与 CyUSB）
│  │  ├─ CyUSB.dll
│  │  ├─ Waveplus.DaqSys.dll
│  │  └─ Waveplus.DaqSysInterface.dll
│  ├─ __init__.py                  # 包入口（当前为空）
│  ├─ constants.py                 # 将 .NET 常量/枚举映射为 Python 枚举类
│  ├─ daq_system.py                # 采集系统核心包装（设备状态/启动停止/事件/通道设置等）
│  ├─ capture_configuration.py     # 采集配置封装（采样率、触发、FSW 协议、IMU 采样模式）
│  ├─ sensor_configuration.py      # 传感器配置封装（类型、加速度/陀螺仪量程）
│  ├─ device_dependent_functionalities.py # 设备依赖功能可用性查询
│  ├─ event_args.py                # 事件参数包装（数据可用、状态变化、传感器内存数据）
│  ├─ foot_sw_transducer.py        # 足底开关（Foot Switch）通道开关/阈值配置
│  └─ version.py                   # 设备/固件/软件版本信息封装
├─ README.md                       # 本说明文档
├─ CHANGELOG.md                    # 版本变更记录
├─ LICENSE                         # MIT 许可证
├─ pyproject.toml                  # 构建/元数据（基于 setuptools）
└─ setup.py                        # 平台守卫与构建入口（仅 Windows）
```

## 代码作用与模块说明
- `constants.py`
  - 将 .NET SDK 的状态、错误码、RF 通道、采样率、IMU 采样模式、FSW 协议等枚举统一为 Python 端可读的枚举类。
  - 便于调用方书写类型安全、可补全的代码。

- `daq_system.py`
  - `CometaDaqSystem` 继承 .NET `DaqSystem` 并暴露友好方法：
    - 设备状态/错误：`get_state()`, `get_initial_error()`
    - 采集控制：`set_capture_configuration()`, `start_capturing()`, `stop_capturing()`
    - 触发：`generate_start_trigger()`, `generate_stop_trigger()`
    - 传感器管理：启停通道、获取/设置传感器配置、检测电极阻抗、LED 控制
    - 事件订阅：`add_on_data_available_handler()`, `add_on_state_changed_handler()` 等
    - 版本/通道：固件/硬件/软件版本、RF 通道读写

- `capture_configuration.py`
  - `CometaCaptureConfiguration`：采样率、外部触发电平/使能、FSW A/B 开启与阈值、FSW 协议、IMU 采样模式等。

- `sensor_configuration.py`
  - `CometaSensorConfiguration`：设置传感器类型（EMG/IMU/FSW/模拟）、加速度计/陀螺仪量程。

- `event_args.py`
  - 数据事件 `CometaDataAvailableEventArgs`：
    - EMG 样本、IMU（四元数/Raw acc/gyr/mag）、FSW、同步信号、丢包、触发扫描号等。
  - 设备状态事件、传感器内存数据事件的参数获取器一并封装。

- `foot_sw_transducer.py`
  - FSW 各压敏位置（A/1/5/T）的开关与阈值读写封装。

- `version.py`
  - 统一读取设备 `Version/ExtVersion` 字段（主/次版本、构建号、修订号）。

## 使用环境与前置条件
- 平台：仅 Windows（`setup.py` 含平台守卫）。
- 驱动：必须先安装 Cometa OEM USB 驱动（确保设备可被系统识别）。
- 依赖：Python 3.7+，`pythonnet`（已在 `pyproject.toml` 中声明）。
- DLL：项目已随包提供必要 .NET 依赖（位于 `src/pyemg_cometa/lib`）。

## 快速上手（最小示例）
以下示例展示如何配置采样、订阅数据事件并启动采集。请在设备连接、驱动安装完成后运行。

```python
from pyemg_cometa.daq_system import CometaDaqSystem
from pyemg_cometa.capture_configuration import CometaCaptureConfiguration
from pyemg_cometa.sensor_configuration import CometaSensorConfiguration
from pyemg_cometa.constants import (
    SamplingRateEnum, DataAvailableEventPeriodEnum,
    SensorTypeEnum
)

def on_data_available(sender, args):
    # args: CometaDataAvailableEventArgs
    emg = args.get_emg_samples()           # list[list[float]]
    acc = args.get_accelerometer_samples() # 仅 RAW/MIXED 模式可用
    quat = args.get_orientation_samples()  # 仅 FUSED/MIXED 模式可用
    print("scan:", args.scan_number(), "emg_frames:", len(emg))

daq = CometaDaqSystem()

# 采集配置
cap = CometaCaptureConfiguration()
cap.set_sampling_rate(SamplingRateEnum.HZ_2000)

# 传感器配置（示例：将 0 号通道设置为 EMG 并使能）
sen = CometaSensorConfiguration()
sen.set_sensor_type(SensorTypeEnum.EMG_SENSOR)
daq.set_sensor_configuration(sen, sensor_id=0)
daq.enable_sensor(0)

# 注册事件并启动采集
daq.add_on_data_available_handler(on_data_available)
daq.set_capture_configuration(cap)
daq.start_capturing(DataAvailableEventPeriodEnum.MS_25)

# ...进行你的业务逻辑...

daq.stop_capturing()
daq.dispose()
```

提示：IMU 的原始/融合数据可用性取决于 `IMU` 采集模式（见 `ImuAcqTypeEnum`）。

## 业务开发指南（进阶）

以下内容帮助你把“最小示例”扩展为可用于实际业务的稳定数据管线。

### 安装与导入
- 开发安装：`pip install -e .`（在项目根目录）
- 包名与导入名：发行名是 `pysio-pyemg-cometa`，导入名是 `pyemg_cometa`。

### 典型工作流
1) 发现并启用传感器通道
```python
num = daq.get_num_installed_sensors()
for ch in range(num):
    cfg = CometaSensorConfiguration()
    cfg.set_sensor_type(SensorTypeEnum.EMG_SENSOR)
    daq.set_sensor_configuration(cfg, ch)
    daq.enable_sensor(ch)
```

2) 选择 IMU 模式（如需）
```python
from pyemg_cometa.constants import ImuAcqTypeEnum

cap = CometaCaptureConfiguration()
cap.set_sampling_rate(SamplingRateEnum.HZ_2000)
cap.set_imu_acq_type(ImuAcqTypeEnum.FUSED_9DOF_142HZ)
daq.set_capture_configuration(cap)
```

3) 事件驱动的数据管线
- 建议在回调中只做轻量工作，把数据放入队列，另起线程/协程做计算与存储。
```python
import queue, threading, time

q = queue.Queue(maxsize=64)
stop = threading.Event()

def on_data_available(sender, args):
    ts = time.time()  # 生成你的时间戳
    q.put((ts, args.scan_number(), args.get_emg_samples()))

def consumer():
    while not stop.is_set():
        try:
            ts, scan, emg = q.get(timeout=0.5)
            # TODO: 处理/滤波/入库
        except queue.Empty:
            pass

daq.add_on_data_available_handler(on_data_available)
worker = threading.Thread(target=consumer, daemon=True)
worker.start()

daq.start_capturing(DataAvailableEventPeriodEnum.MS_25)
# ...运行一段时间...
daq.stop_capturing()
stop.set(); worker.join()
daq.remove_on_data_available_handler(on_data_available)
daq.dispose()
```
提示：事件来自 .NET 线程环境，避免在回调中做重计算或阻塞。

### 触发与同步
- 内部触发：
```python
daq.generate_start_trigger()
daq.generate_stop_trigger()
```
- 外部触发：
```python
cap = daq.get_capture_configuration()
cap.set_external_trigger_status(True)
cap.set_trigger_level(1)  # 具体电平依据硬件接线
daq.set_capture_configuration(cap)
```
- 在回调中可判断是否检测到触发并获取扫描号：`args.is_start_trigger_detected()`、`args.start_trigger_scan()`。

### 电极阻抗检查（EMG 预检查）
```python
from pyemg_cometa.constants import SensorCheckReportEnum
report = daq.check_impedance(sensor_id=0)
# 返回枚举结果（通过/失败/未执行），在 Idle 状态执行更稳妥
```

### 足底开关（FSW）配置
```python
from pyemg_cometa.foot_sw_transducer import (
    CometaFootSwTransducerEnabled, CometaFootSwTransducerThreshold)
from pyemg_cometa.constants import FootSwProtocolEnum

cap = CometaCaptureConfiguration()
en = CometaFootSwTransducerEnabled(); en.set_transducer_a(True)
th = CometaFootSwTransducerThreshold(); th.set_transducer_a(0.5)
cap.set_fsw_a_is_enabled(en)
cap.set_fsw_a_threshold(th)
cap.set_fsw_protocol(FootSwProtocolEnum.FULL_FOOT)
daq.set_capture_configuration(cap)
```

### RF 信道与多设备环境
```python
from pyemg_cometa.constants import RFChannelEnum
# 读取/设置主设备与传感器 RF 通道（示例 device_id=0）
ch = daq.get_master_device_rf_channel(device_id=0)
daq.set_master_device_rf_channel(RFChannelEnum.RF_CHANNEL_3, device_id=0)
daq.set_semsor_rf_channel(RFChannelEnum.RF_CHANNEL_3, device_id=0)
```
注意：请确保采集器与传感器使用一致信道。

### 离线读取（传感器内存）
```python
def on_mem_data(sender, args):
    # CometaSensorMemoryDataAvailableEventArgs
    progress = args.get_transfer_progress()
    emg = args.get_emg_samples()
    if args.is_trial_end():
        print("trial end", args.get_current_trial_id())

daq.add_on_sensor_memory_data_available_handler(on_mem_data)
daq.start_selective_memory_reading(trial_id=1)
# 等待进度/数据 ...
daq.stop_selective_memory_reading()
daq.remove_on_sensor_memory_data_available_handler(on_mem_data)
```

### 错误处理与资源回收
- 初始化后检查：`daq.get_initial_error()`；发生异常时记录 .NET 异常信息。
- 停止采集、移除事件、调用 `dispose()` 释放底层资源，避免句柄泄露。

### 数据单位与标定
- 返回值与单位遵循 Cometa SDK 定义。EMG/IMU 的绝对单位、标定与零偏按设备文档与实物配置为准。

## 项目总结
- 优势：
  - 轻量封装，调用链清晰；事件模型与原厂 SDK 一致；跨工程脚本友好。
  - 随包自带 DLL，开箱即用（在 Windows + 驱动就绪前提下）。
- 限制：
  - 仅 Windows；依赖 .NET/USB 驱动；API 以原厂能力为上限。
  - `__init__.py` 暂未导出便捷别名，需从子模块显式导入类型。

## 开发建议
- 代码结构
  - 继续保持“薄封装”策略：尽量不改变 .NET 语义，仅做 Python 化命名与返回值类型整理。
  - 为关键方法与事件参数补充 docstring，便于 IDE 提示与类型检查。
  - 在 `__init__.py` 暴露常用类型（如 `CometaDaqSystem`、`CometaCaptureConfiguration`、`CometaSensorConfiguration`、常量枚举）以简化导入路径。

- 类型与枚举
  - 在 `constants.py` 中集中维护映射，新增 SDK 枚举时统一在此扩展，避免分散。

- 示例与测试
  - 增加最小可运行示例与简单集成脚本（基于模拟或可选跳过硬件），便于 CI 进行冒烟检查（在无设备时仅验证导入/类型）。

- 发布与兼容
  - 保持 `pyproject.toml` 的平台与依赖约束；如上游 DLL 更新，记录在 `CHANGELOG.md` 并进行向后兼容性评估。

## 许可证
本项目基于 MIT 许可证发布，详见 `LICENSE`。

## 致谢
由 KU Leuven e-Media Lab 与贡献者共同维护，感谢 Cometa 提供的设备与 SDK 支持。
