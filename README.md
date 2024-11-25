This project turns your ESP32 device into USB CANBUS interface for [python-can](https://github.com/hardbyte/python-can)

## ESPHome

For now only USB_SERIAL_JTAG interface is supported (it is available on ESP32-C3 / ESP32-S3). You need to enable logger with `hardware_uart: USB_SERIAL_JTAG`.

Example esphome config:

```
esphome:
  name: "node-c3-3"
  platformio_options:
    board_build.flash_mode: dio
    board_build.mcu: esp32c3

esp32:
  board: esp32-c3-devkitm-1
  variant: esp32c3
  framework:
    type: esp-idf

# Enable logging
logger:
  hardware_uart: USB_SERIAL_JTAG
  level: DEBUG

  # increase rx buffer size. For now it requries this PR: https://github.com/esphome/esphome/pull/7364/files (not yet merged).
  # default value is 512 bytes and may lead to lost packets (for example when CANOpen block transfer is used)
  rx_buffer_size: 16k

  logs:
    wifi: INFO
    esp-idf: INFO

canbus:
  - platform: esp32_can
    id: can_bus
    rx_pin: GPIO5
    tx_pin: GPIO4
    can_id: 1
    bit_rate: 125kbps

    # increase queue sizes for CANOpen block transfer (up to 128 frames can be sent in burst)
    tx_queue_len: 128
    rx_queue_len: 128

  - platform: canbus_usb_serial
    id: can_bus_usb_serial
    canbus_id: can_bus  # refers to physical can interface defined above
    can_id: 1

external_components:
  - source: github://mrk-its/esphome-canbus-usb-serial


```

## python-can interface

Add esp_can module to your project:

```
pip install esp_usb_serial@git+https://github.com/mrk-its/esphome-canbus-usb-serial
```

Now in `python-can` you can use `esp_usb_serial` interface. Single 'channel' parameter is accepted: path to your USB device, like `/dev/ttyACM0`.

Example can.viewer session:

```
pip install esp_usb_serial@git+https://github.com/mrk-its/esphome-canbus-usb-serial
pip install "python-can[viewer]"
python -m can.viewer -i esp_usb_serial -c /dev/ttyACM0
```

## Limitations

* extended can ids are not supported (yet)
* remote_transmission_request (RTR) frames are not supported (yet)

## Community

* [Discord Server](https://discord.gg/VXjUSnUWsd)
