#!/bin/bash

AUCBOARD_USER="aucboard";
AUCBOARD_DIR="/opt/aucboard";
SYSTEMD_TEMPLATE_FILE="aucboard.service.template";
SYSTEMD_BOOT_TEMPLATE_FILE="aucboard-boot.service.template";
SYSTEMD_AUCBOARD_FILE="aucboard.service";
SYSTEMD_AUCBOARD_BOOT_FILE="aucboard-boot.service";
GITHUB_URL="https://github.com/JustAnEric/aucboard";
GITHUB_RAW_USER_CONT="https://raw.githubusercontent.com/JustAnEric/aucboard/refs/heads/main";
SYSTEMD_SERVICE_DIR="/etc/systemd/system";

auc_sep() {
    echo -e "----------------------------------\n";
}

auc_banner() {
    echo "AUCBOARD INSTALL";
    auc_sep;
}

auc_enable_hw_param() {
    local param="$1";
    if grep -q "^${param}" "$CONFIG_FILE"; then
        echo "  $param is already active"
    elif grep -q "^#.*${param}" "$CONFIG_FILE"; then
        echo "  enabling commented parameter: ${param}";
        sed -i "s/^#.${param}/${param}/" "$CONFIG_FILE"
    else
        echo "  enabling new parameter: ${param}";
        echo "$param" >> "$CONFIG_FILE"
    fi;
}

auc_banner;

if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root!";
    exit 1
fi;

echo "VERIFICATION";

for group in gpio i2c spi; do
    getent group "$group" >/dev/null || groupadd -r "$group"
done;

if [ -f "/boot/firmware/config.txt" ]; then
    CONFIG_FILE="/boot/firmware/config.txt"
elif [ -f "/boot/config.txt" ]; then
    CONFIG_FILE="/boot/config.txt"
else
    echo "ERROR: Is this a Raspberry Pi??" >&2;
    exit 1
fi;

echo -e "Hardware Configuration File: $CONFIG_FILE\n";

echo "PACKAGE INSTALL (net required)";
auc_sep;

sudo apt install build-essential liblgpio-dev python3-dev swig python3-pip python3-pil libfreetype6-dev libjpeg-dev libopenjp2-7 libtiff6 curl wget -y

auc_sep;
echo "AUCBOARD USER+GROUP";

sudo mkdir -p $AUCBOARD_DIR;
sudo useradd -r -M -s /bin/false $AUCBOARD_USER
sudo chown -R $AUCBOARD_USER:$AUCBOARD_USER $AUCBOARD_DIR

auc_sep;
echo "COPY PROJ";

sudo cp -r $PWD/* $AUCBOARD_DIR;

auc_sep;
echo "PERMISSIONS";

sudo usermod -aG gpio,i2c,spi $AUCBOARD_USER;

auc_sep;
echo "PROJ SETUP";

python3 -m venv $AUCBOARD_DIR/auc_venv;
$AUCBOARD_DIR/auc_venv/bin/pip install -r $AUCBOARD_DIR/requirements.txt;

auc_sep;
if [ -f "/bin/raspi-config" ]; then
    echo "RASPI CONFIG";

    # For this, users will want some form of Raspberry Pi OS installed
    sudo raspi-config nonint do_i2c 0
    sudo raspi-config nonint do_spi 0
else
    echo "UNIVERSAL CONFIG";

    # For users without Raspberry Pi OS Lite installed
    auc_enable_hw_param "dtparam=i2c_arm=on"
    auc_enable_hw_param "dtparam=spi=on"
fi;

auc_sep;
echo "SYSTEMD";

if [ -f "$AUCBOARD_DIR/$SYSTEMD_TEMPLATE_FILE" ]; then
    # The user has the systemd template file in Aucboard dir.
    SYSTEMD_1_READY=true;
    SYSTEMD_1_FILE="$AUCBOARD_DIR/$SYSTEMD_TEMPLATE_FILE";
elif [ -f "$DIR/$SYSTEMD_TEMPLATE_FILE" ]; then # safety check!!
    # The user has the systemd template file in local dir.
    SYSTEMD_1_READY=true;
    SYSTEMD_1_FILE="$DIR/$SYSTEMD_TEMPLATE_FILE";
else
    # The user does not have the template file at all;
    DOWNLOAD_URL="$GITHUB_RAW_USER_CONT/firmware/aucboard.service.template";
    DOWNLOAD_DESTINATION="$AUCBOARD_DIR/aucboard.service.template";
    if command -v wget >/dev/null 2>&1; then
        wget -q "$DOWNLOAD_URL" -O "$DOWNLOAD_DESTINATION"
    elif command -v curl >/dev/null 2>&1; then
        curl -sFL "$DOWNLOAD_URL" -o "$DOWNLOAD_DESTINATION"
    else
        echo "No viable download solution found!"
    fi;
    if [ -f "$AUCBOARD_DIR/$SYSTEMD_TEMPLATE_FILE" ]; then
        echo "Download of $DOWNLOAD_DESTINATION file has completed";
        SYSTEMD_1_READY=true;
        SYSTEMD_1_FILE="$AUCBOARD_DIR/$SYSTEMD_TEMPLATE_FILE";
    else
        echo "No systemd template file found?? You'll have to make it yourself or use the one here: $DOWNLOAD_URL";
        SYSTEMD_1_READY=false;
    fi
fi;

if [ -f "$AUCBOARD_DIR/$SYSTEMD_BOOT_TEMPLATE_FILE" ]; then
    # The user has the systemd template file in Aucboard dir.
    SYSTEMD_2_READY=true;
    SYSTEMD_2_FILE="$AUCBOARD_DIR/$SYSTEMD_BOOT_TEMPLATE_FILE";
elif [ -f "$DIR/$SYSTEMD_BOOT_TEMPLATE_FILE" ]; then # safety check!!
    # The user has the systemd template file in local dir.
    SYSTEMD_2_READY=true;
    SYSTEMD_2_FILE="$DIR/$SYSTEMD_BOOT_TEMPLATE_FILE";
else
    # The user does not have the template file at all;
    DOWNLOAD_URL="$GITHUB_RAW_USER_CONT/firmware/aucboard-boot.service.template";
    DOWNLOAD_DESTINATION="$AUCBOARD_DIR/aucboard-boot.service.template";
    if command -v wget >/dev/null 2>&1; then
        wget -q "$DOWNLOAD_URL" -O "$DOWNLOAD_DESTINATION"
    elif command -v curl >/dev/null 2>&1; then
        curl -sFL "$DOWNLOAD_URL" -o "$DOWNLOAD_DESTINATION"
    else
        echo "No viable download solution found!"
    fi;
    if [ -f "$AUCBOARD_DIR/$SYSTEMD_BOOT_TEMPLATE_FILE" ]; then
        echo "Download of $DOWNLOAD_DESTINATION file has completed";
        SYSTEMD_2_READY=true;
        SYSTEMD_2_FILE="$AUCBOARD_DIR/$SYSTEMD_BOOT_TEMPLATE_FILE";
    else
        echo "No systemd template file found?? You'll have to make it yourself or use the one here: $DOWNLOAD_URL";
        SYSTEMD_2_READY=false;
    fi
fi;

if [[ -v SYSTEMD_1_FILE && "$SYSTEMD_1_READY" = true ]]; then
    echo "Creating systemd file...";
    sudo cp "$SYSTEMD_1_FILE" "$SYSTEMD_SERVICE_DIR/$SYSTEMD_AUCBOARD_FILE";
    systemctl daemon-reload;
    systemctl enable --now $SYSTEMD_AUCBOARD_FILE;
    echo "Systemd configured.";
else 
    echo "!!!Please configure systemd yourself!!! This is EXTREMELY important, as your portable device won't display any output on boot!"
fi;

if [[ -v SYSTEMD_2_FILE && "$SYSTEMD_2_READY" = true ]]; then
    echo "Creating systemd file...";
    sudo cp "$SYSTEMD_2_FILE" "$SYSTEMD_SERVICE_DIR/$SYSTEMD_AUCBOARD_BOOT_FILE";
    systemctl daemon-reload;
    systemctl enable $SYSTEMD_AUCBOARD_BOOT_FILE;
    echo "Systemd configured.";
else 
    echo "!!!Please configure systemd yourself!!! This is EXTREMELY important, as your portable device won't display any output on boot!"
fi;

auc_sep;
echo "done! please reboot to enable this service!";