#pragma once

#include "esphome/core/component.h"
#include "esphome/core/defines.h"

namespace esphome {
namespace canbus_usb_serial {
const char *const TAG = "canbus_proxy";

class CanbusUsbSerial : public canbus::Canbus {
  std::string line_buffer;

 public:
  canbus::Canbus *canbus;

  CanbusUsbSerial() {
    this->canbus = nullptr;
    line_buffer.reserve(512);
  }
  CanbusUsbSerial(canbus::Canbus *canbus) {
    this->canbus = canbus;
    line_buffer.reserve(512);
  }
  void send_serial_message(uint32_t can_id, bool use_extended_id, bool remote_transmission_request,
                           const std::vector<uint8_t> &data);

  void setup();
  void loop() override;

 protected:
  bool setup_internal() override;
  canbus::Error send_message_no_loopback(struct canbus::CanFrame *frame);
  canbus::Error send_message(struct canbus::CanFrame *frame) override;
  canbus::Error read_message(struct canbus::CanFrame *frame) override;

 private:
  void trigger(uint32_t can_id, bool use_extended_id, bool remote_transmission_request,
               const std::vector<uint8_t> &data);
};
}  // namespace canbus_proxy
}  // namespace esphome
