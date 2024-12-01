set -x
#FRAMEWORK_OPTS="-s type arduino -s version recommended -s platform_version 5.4.0"
#FRAMEWORK_OPTS="-s type esp-idf -s version 5.2.1 -s platform_version 6.7.0"
FRAMEWORK_OPTS="-s type esp-idf -s version recommended -s platform_version 5.4.0"
#BOARD="-s board esp32-c3-devkitm-1"
BOARD="-s board esp32-s3-devkitc-1"
docker run --mount type=bind,source=$(pwd),target=/config -it esphome/esphome $FRAMEWORK_OPTS $BOARD compile test/config.yaml.template

