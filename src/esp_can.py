import logging
import re
import serial
import time
import random

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
    def __init__(
        self,
        channel,
        reset=False,
        after_reset_delay=2.0,
        clear_input_buffer=False,
        send_delay_ms=1.0,
        tx_error_ratio=0,
        **kwargs
    ):
        self.send_delay_ms = send_delay_ms
        self.tx_error_ratio = tx_error_ratio

        logger.debug("channel: %s", channel)
        if reset:
            import esptool
            esptool.main(["--port", channel, "chip_id"])
            time.sleep(after_reset_delay)

        self.device = serial.Serial(channel, timeout=1.0, baudrate=4000000)
        if clear_input_buffer:
            t = time.time()
            while time.time() - t < 5:
                lines = self.device.readlines()
                if lines:
                    logger.info("ignore %d lines present already in the input buffer", len(lines))

        # for some reason, after reset, ESP input buffer sometimes
        # contain some data already. Few examples:
        # 're to isolate al', 'O pins in sleep ', 'ins in sleep sta'
        # if this happens first send CAN frame gets broken.
        # To prevent that send few extra lines that will be ignored by esphome parser

        self.device.write(b"esphome-canbus-proxy\r\r")

        self._filters = None
        self.channel_info = "esp_can"

    def send(self, msg):
        if random.random() < self.tx_error_ratio:
            logger.warning("injected error, loosing packet")
            return
        logger.debug("send: %r", msg)
        can_id = msg.arbitration_id
        data = "".join(f" {b:02x}" for b in msg.data)
        self.device.write(f"{can_id:03x}{data}\r".encode("utf-8"))
        self.device.flush()
        if self.send_delay_ms:
            time.sleep(0.001 * self.send_delay_ms)

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
