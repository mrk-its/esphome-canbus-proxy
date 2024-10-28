from itertools import groupby
import esphome.config_validation as cv
import esphome.codegen as cg
from esphome import automation
from esphome.const import CONF_ID, CONF_TRIGGER_ID
from esphome.components.canbus import CanbusComponent
from esphome.components.mqtt import MQTTClientComponent
from esphome.components.canbus import (
    CONF_ON_FRAME,
    CONF_CAN_ID,
    CONF_CAN_ID_MASK,
    CONF_USE_EXTENDED_ID,
    CONF_REMOTE_TRANSMISSION_REQUEST,
    CanbusComponent,
    CanbusTrigger,
    validate_id,
)

ns = cg.esphome_ns.namespace('canbus_proxy')
CanbusProxy = ns.class_(
    'CanbusProxy',
    CanbusComponent,
)

DEPENDENCIES = ["logger"]

CONFIG_SCHEMA = cv.Schema({
    cv.GenerateID(): cv.declare_id(CanbusProxy),
    cv.Optional("canbus_id"): cv.use_id(CanbusComponent),
    cv.Optional(CONF_ON_FRAME): automation.validate_automation(
        {
            cv.GenerateID(CONF_TRIGGER_ID): cv.declare_id(CanbusTrigger),
            cv.Required(CONF_CAN_ID): cv.int_range(min=0, max=0x1FFFFFFF),
            cv.Optional(CONF_CAN_ID_MASK, default=0x1FFFFFFF): cv.int_range(
                min=0, max=0x1FFFFFFF
            ),
            cv.Optional(CONF_USE_EXTENDED_ID, default=False): cv.boolean,
            cv.Optional(CONF_REMOTE_TRANSMISSION_REQUEST): cv.boolean,
        },
        validate_id,
    ),
}).extend(cv.COMPONENT_SCHEMA)


async def to_code(config):
    if "canbus_id" in config:
        canbus = await cg.get_variable(config["canbus_id"])
    else:
        canbus = None
    canbus_proxy = cg.new_Pvariable(config[CONF_ID], canbus)
    await cg.register_component(canbus_proxy, config)

    for conf in config.get(CONF_ON_FRAME, []):
        can_id = conf[CONF_CAN_ID]
        can_id_mask = conf[CONF_CAN_ID_MASK]
        ext_id = conf[CONF_USE_EXTENDED_ID]
        trigger = cg.new_Pvariable(
            conf[CONF_TRIGGER_ID], canbus, can_id, can_id_mask, ext_id
        )
        if CONF_REMOTE_TRANSMISSION_REQUEST in conf:
            cg.add(
                trigger.set_remote_transmission_request(
                    conf[CONF_REMOTE_TRANSMISSION_REQUEST]
                )
            )
        await cg.register_component(trigger, conf)
        await automation.build_automation(
            trigger,
            [
                (cg.std_vector.template(cg.uint8), "x"),
                (cg.uint32, "can_id"),
                (cg.bool_, "remote_transmission_request"),
            ],
            conf,
        )