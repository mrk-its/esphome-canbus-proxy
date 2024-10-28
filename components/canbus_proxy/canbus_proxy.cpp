#include "esphome.h"
#include "canbus_proxy.h"
#include "driver/usb_serial_jtag.h"

namespace esphome {
namespace canbus_proxy {

void CanbusProxy::setup() {
  ESP_LOGCONFIG(TAG, "Setting up CanbusProxy");
  if (!this->setup_internal()) {
    ESP_LOGE(TAG, "setup error!");
    this->mark_failed();
  }
}

bool hex(const char *ptr, uint32_t *result) {
  if (*ptr >= '0' && *ptr <= '9') {
    *result = *result * 16 + (*ptr - '0');
    return true;
  }
  if (*ptr >= 'a' && *ptr <= 'f') {
    *result = *result * 16 + (*ptr - 'a' + 10);
    return true;
  }
  return false;
};

bool hex2(const char *ptr, uint32_t *result) {
  bool ok = hex(ptr, result);
  return ok && hex(ptr + 1, result);
};

bool hex3(const char *ptr, uint32_t *result) {
  bool ok = hex2(ptr, result);
  return ok && hex(ptr + 2, result);
};

bool parse_can_frame(std::string &msg, struct canbus::CanFrame &frame) {
  frame.can_id = 0;
  frame.can_data_length_code = 0;
  frame.use_extended_id = false;
  frame.remote_transmission_request = false;

  if (!hex3(msg.c_str(), &frame.can_id))
    return false;

  auto ptr = msg.begin() + 4;

  while (ptr < msg.end()) {
    uint32_t byte = 0;
    if (hex2(&*ptr, &byte)) {
      frame.data[frame.can_data_length_code++] = (uint8_t) byte;
    } else {
      break;
    }
    ptr += 3;
  }
  return true;
};

void CanbusProxy::loop() {
  char data[256];
  int len = 0;
#ifdef USE_LOGGER_USB_SERIAL_JTAG
  len = usb_serial_jtag_read_bytes(data, 255, 0);
#else
#error You need to have logger with hardware_uart: USB_SERIAL_JTAG enabled
#endif

  if (len > 0) {
    data[len] = 0;
  }
  char *ptr = data;
  while (len > 0) {
    char *delimiter = strchr(ptr, '\r');
    if (delimiter) {
      line_buffer.append(ptr, delimiter - ptr);
      len -= (delimiter + 1 - ptr);
      ptr = delimiter + 1;

      struct canbus::CanFrame frame;
      int is_parsed = 0;
      if (parse_can_frame(line_buffer, frame)) {
        send_message_no_loopback(&frame);
        is_parsed = 1;
      }

      ESP_LOGD(TAG, "input: %s, parsed: %d", line_buffer.c_str(), is_parsed);

      line_buffer.clear();
    } else {
      line_buffer.append(ptr, len);
      break;
    }
  }
}

void CanbusProxy::trigger(uint32_t can_id, bool use_extended_id, bool remote_transmission_request,
                          const std::vector<uint8_t> &data) {
  // fire all triggers
  // TODO: currently we can't check can_id, can_mask, remote_transmission_request because these trigger fields
  // are protected
  for (auto *trigger : this->triggers_) {
    trigger->trigger(data, can_id, remote_transmission_request);
  }
}

bool CanbusProxy::setup_internal() {
  if(!this->canbus) {
    return true;
  }
  Automation<std::vector<uint8_t>, uint32_t, bool> *automation;
  LambdaAction<std::vector<uint8_t>, uint32_t, bool> *lambdaaction;
  canbus::CanbusTrigger *canbus_canbustrigger;

  canbus_canbustrigger = new canbus::CanbusTrigger(this->canbus, 0, 0, false);
  canbus_canbustrigger->set_component_source("canbus_proxy");
  App.register_component(canbus_canbustrigger);
  automation = new Automation<std::vector<uint8_t>, uint32_t, bool>(canbus_canbustrigger);
  auto cb = [this](std::vector<uint8_t> x, uint32_t can_id, bool remote_transmission_request) -> void {
    trigger(can_id, this->use_extended_id_, remote_transmission_request, x);
    this->send_serial_message(can_id, this->use_extended_id_, remote_transmission_request, x);
  };
  lambdaaction = new LambdaAction<std::vector<uint8_t>, uint32_t, bool>(cb);
  automation->add_actions({lambdaaction});
  ESP_LOGI(TAG, "trigger installed!");

  return true;
}

void CanbusProxy::send_serial_message(uint32_t can_id, bool use_extended_id, bool remote_transmission_request,
                                      const std::vector<uint8_t> &data) {
  char buf[256];
  sprintf(buf, "%03x", can_id);
  if (!data.empty()) {
    int offs = 0;
    for (auto ptr = data.begin(); ptr < data.end(); ptr++, offs++) {
      sprintf(buf + 3 + offs * 3, " %02x", *ptr);
    }
  }
  ESP_LOGI(TAG, "%s", buf);
}

canbus::Error CanbusProxy::send_message_no_loopback(struct canbus::CanFrame *frame) {
  std::vector<uint8_t> data = std::vector<uint8_t>(frame->data, frame->data + frame->can_data_length_code);
  if(this->canbus) {
    this->canbus->send_data(frame->can_id, frame->use_extended_id, frame->remote_transmission_request, data);
  }
  trigger(frame->can_id, frame->use_extended_id, frame->remote_transmission_request, data);
  return canbus::ERROR_OK;
}

canbus::Error CanbusProxy::send_message(struct canbus::CanFrame *frame) {
  std::vector<uint8_t> data = std::vector<uint8_t>(frame->data, frame->data + frame->can_data_length_code);
  if(this->canbus) {
    this->canbus->send_data(frame->can_id, frame->use_extended_id, frame->remote_transmission_request, data);
  }
  send_serial_message(frame->can_id, frame->use_extended_id, frame->remote_transmission_request, data);
  return canbus::ERROR_OK;
};

canbus::Error CanbusProxy::read_message(struct canbus::CanFrame *frame) { return canbus::ERROR_NOMSG; };

}  // namespace canbus_proxy
}  // namespace esphome
