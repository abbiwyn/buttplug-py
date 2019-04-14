# TODO Maybe use marshmallow?

from dataclasses import dataclass
import json
import sys
from typing import Dict, List
from enum import IntEnum


class ButtplugMessageEncoder(json.JSONEncoder):
    def pascal_case(self, cc_string):
        return ''.join(x.title() for x in cc_string.split('_'))

    def build_obj_dict(self, obj):
        # Build camel case versions of our internal variables
        return dict((self.pascal_case(key), value)
                    for (key, value) in obj.__dict__.items())

    def default(self, obj):
        return {type(obj).__name__: self.build_obj_dict(obj)}


# ButtplugMessage isn't a dataclass, because we usually set id later than
# message construction, and don't want to require it in constructors
class ButtplugMessage(object):
    SYSTEM_ID = 0
    DEFAULT_ID = 1

    def __init__(self):
        self.id = ButtplugMessage.DEFAULT_ID

    def as_json(self):
        return ButtplugMessageEncoder().encode(self)

    @staticmethod
    def from_json(json_str: str):
        d = json.loads(json_str)
        return ButtplugMessage.from_dict(d)

    @staticmethod
    def from_dict(msg_dict: dict):
        classname = list(msg_dict.keys())[0]
        cls = getattr(sys.modules[__name__], classname)
        d = list(msg_dict.values())[0]
        msg = cls.from_dict(d)
        msg.id = d["Id"]
        return msg


@dataclass
class ButtplugDeviceMessage(ButtplugMessage):
    device_index: int


class ButtplugOutgoingOnlyMessage(object):
    pass


@dataclass
class Ok(ButtplugOutgoingOnlyMessage, ButtplugMessage):
    @staticmethod
    def from_dict(d: dict) -> "Ok":
        return Ok()


class ButtplugErrorCode(IntEnum):
    ERROR_UNKNOWN = 0
    ERROR_INIT = 1
    ERROR_PING = 2
    ERROR_MSG = 3
    ERROR_DEVICE = 4


@dataclass
class Error(ButtplugOutgoingOnlyMessage, ButtplugMessage):
    error_message: str
    error_code: int

    @staticmethod
    def from_dict(d: dict) -> "Error":
        return Error(d['ErrorMessage'], d['ErrorCode'])


@dataclass
class Test(ButtplugMessage):
    test_string: str

    @staticmethod
    def from_dict(d: dict) -> "Test":
        return Test(d['TestString'])


@dataclass
class RequestServerInfo(ButtplugMessage):
    client_name: str
    message_version: int = 1

    @staticmethod
    def from_dict(d: dict) -> "RequestServerInfo":
        return RequestServerInfo(d['ClientName'], d['MessageVersion'])


@dataclass
class ServerInfo(ButtplugMessage):
    server_name: str
    major_version: int
    minor_version: int
    build_version: int
    message_version: int = 1
    max_ping_time: int = 0

    @staticmethod
    def from_dict(d: dict) -> "ServerInfo":
        return ServerInfo(d['ServerName'], d['MajorVersion'],
                          d['MinorVersion'], d['BuildVersion'],
                          d['MessageVersion'], d['MaxPingTime'])


@dataclass
class RequestDeviceList(ButtplugMessage):
    pass


@dataclass
class MessageAttributes:
    feature_count: int

    @staticmethod
    def from_dict(d: dict) -> "MessageAttributes":
        return MessageAttributes(d["FeatureCount"])


@dataclass
class DeviceInfo:
    device_name: str
    device_index: int
    device_messages: Dict[str, MessageAttributes]

    @staticmethod
    def from_dict(d: dict) -> "DeviceInfo":
        attrs = dict([(k, MessageAttributes.from_dict(v))
                      for k, v in d["DeviceMessages"]])
        return DeviceInfo(d["DeviceName"], d["DeviceIndex"], attrs)


@dataclass
class DeviceList(ButtplugMessage, ButtplugOutgoingOnlyMessage):
    devices: List[DeviceInfo]

    @staticmethod
    def from_dict(d: dict) -> "DeviceList":
        return DeviceList([DeviceInfo(x["DeviceName"],
                                      x["DeviceIndex"],
                                      x["DeviceMessages"])
                           for x in d["Devices"]])


@dataclass
class DeviceAdded(ButtplugMessage, DeviceInfo, ButtplugOutgoingOnlyMessage):
    @staticmethod
    def from_dict(d: dict) -> "DeviceAdded":
        msg = DeviceInfo.from_dict(d)
        return DeviceAdded(msg.device_name, msg.device_index,
                           msg.device_messages)


@dataclass
class DeviceRemoved(ButtplugMessage, ButtplugOutgoingOnlyMessage):
    device_index: int

    @staticmethod
    def from_dict(d: dict) -> "DeviceRemoved":
        return DeviceRemoved(d["DeviceIndex"])


@dataclass
class StartScanning(ButtplugMessage):
    @staticmethod
    def from_dict(d: dict) -> "StartScanning":
        return StartScanning()


@dataclass
class StopScanning(ButtplugMessage):
    @staticmethod
    def from_dict(d: dict) -> "StopScanning":
        return StopScanning()


@dataclass
class ScanningFinished(ButtplugMessage, ButtplugOutgoingOnlyMessage):
    @staticmethod
    def from_dict(d: dict) -> "ScanningFinished":
        return ScanningFinished()


class ButtplugLogLevel(object):
    off: str = "Off"
    fatal: str = "Fatal"
    error: str = "Error"
    warn: str = "Warn"
    info: str = "Info"
    debug: str = "Debug"
    trace: str = "Trace"


@dataclass
class RequestLog(ButtplugMessage):
    log_level: str

    @staticmethod
    def from_dict(d: dict) -> "RequestLog":
        return RequestLog(d["LogLevel"])


@dataclass
class Log(ButtplugMessage, ButtplugOutgoingOnlyMessage):
    log_level: str
    log_message: str

    @staticmethod
    def from_dict(d: dict) -> "Log":
        return RequestLog(d["LogLevel"], d["LogMessage"])


@dataclass
class Ping(ButtplugMessage):
    @staticmethod
    def from_dict(d: dict) -> "Ping":
        return Ping()


@dataclass
class FleshlightLaunchFW12Cmd(ButtplugDeviceMessage):
    position: int
    speed: int


@dataclass
class LovenseCmd(ButtplugDeviceMessage):
    command: str


@dataclass
class KiirooCmd(ButtplugDeviceMessage):
    command: str


@dataclass
class VorzeA10CycloneCmd(ButtplugMessage):
    speed: int
    clockwise: bool


@dataclass
class SpeedSubcommand:
    index: int
    speed: float


@dataclass
class VibrateCmd(ButtplugDeviceMessage):
    speeds: List[SpeedSubcommand]


@dataclass
class RotateSubcommand:
    index: int
    speed: float
    clockwise: bool


@dataclass
class RotateCmd(ButtplugMessage):
    rotations: List[RotateSubcommand]


@dataclass
class LinearSubcommand:
    index: int
    position: float
    duration: int


@dataclass
class LinearCmd(ButtplugMessage):
    pass


class StopDeviceCmd(ButtplugDeviceMessage):
    pass


class StopAllDevices(ButtplugMessage):
    pass