import logging
import re
import serial
import time
import can

logger = logging.getLogger(__name__)


DATA_RE = re.compile(r"\[canbus_proxy:\d*\]: ([0-9a-f]{3})(( [0-9a-f][0-9a-f]){0,8}).*")

ESP_LOG_LEVEL = re.compile(r"\[(D|I|W|E)\]")

LEVELS = {
    "D": logging.DEBUG,
    "I": logging.INFO,
    "W": logging.WARN,
    "E": logging.ERROR,
}

class EspCan(can.bus.BusABC):
    def __init__(self, channel, **kwargs):
        logger.debug("channel: %s", channel)
        self.device = serial.Serial(channel, timeout=1.0, baudrate=4000000)
        lines = self.device.readlines()
        if lines:
            logger.info("ignore %d lines present already in the input buffer", len(lines))
        self._filters = None
        self.channel_info = "esp_can"

    def send(self, msg):
        logger.debug("send: %r", msg)
        can_id = msg.arbitration_id
        data = "".join(f" {b:02x}" for b in msg.data)
        self.device.write(f"{can_id:03x}{data}\r".encode("utf-8"))
        self.device.flush()
        time.sleep(0.001)

    def _recv_internal(self, timeout=None):
        data = self.device.readline().decode("utf-8")
        match = DATA_RE.search(data)
        msg = None
        if match:
            arb_id, data, *_ = match.groups()
            try:
                data = bytes(int(v, 16) for v in data[1:].split(" "))
            except Exception:
                logger.error("can't parse data: %r", data)
                return None, False
            msg = can.Message(
                timestamp=time.time(),
                arbitration_id=int(arb_id, 16),
                is_extended_id=False,
                is_remote_frame=False,
                dlc=len(data),
                data=data,
            )
            logger.debug("recv: %r", msg)
        else:
            m = ESP_LOG_LEVEL.search(data)
            if m:
                level = LEVELS.get(m.group(1))
                logger.log(level, "esp log: %s", data[0:-1])
        return msg, False
