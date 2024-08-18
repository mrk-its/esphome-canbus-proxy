#pragma once

#include "esphome.h"
using namespace esphome;

#include "esphome/core/component.h"
#include "esphome/core/defines.h"

namespace esphome {
namespace canbus_proxy {
const char *const TAG = "canbus_proxy";

class CanbusProxy : public canbus::Canbus {
  std::string line_buffer;

 public:
  canbus::Canbus *canbus;
  CanbusProxy(canbus::Canbus *canbus) {
    this->canbus = canbus;
    line_buffer.reserve(512);
  }
  // void add_trigger(UsbSerialMessageTrigger *trigger) { on_message = trigger; }
  void send_serial_message(uint32_t can_id, bool use_extended_id, bool remote_transmission_request,
                           const std::vector<uint8_t> &data);
  // void add_trigger(canbus::CanbusTrigger *trigger) {}

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
