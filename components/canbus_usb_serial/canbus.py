import esphome.config_validation as cv
import esphome.codegen as cg
from esphome import automation
from esphome.const import CONF_ID
from esphome.components.canbus import CanbusComponent
from esphome.components.canbus import (
    CANBUS_SCHEMA,
    CanbusComponent,
    register_canbus,
)

ns = cg.esphome_ns.namespace('canbus_usb_serial')
CanbusUsbSerial = ns.class_(
    'CanbusUsbSerial',
    CanbusComponent,
)

DEPENDENCIES = ["logger"]

CONFIG_SCHEMA = CANBUS_SCHEMA.extend({
    cv.GenerateID(): cv.declare_id(CanbusUsbSerial),
    cv.Optional("canbus_id"): cv.use_id(CanbusComponent),
})


async def to_code(config):
    if "canbus_id" in config:
        canbus = await cg.get_variable(config["canbus_id"])
    else:
        canbus = cg.RawExpression('nullptr')

    canbus_usb_serial = cg.new_Pvariable(config[CONF_ID], canbus)
    await register_canbus(canbus_usb_serial, config)
