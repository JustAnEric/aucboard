#!/bin/bash

if [ "$EUID" -ne 0 ]; then
    echo "This script must be run as root!";
    exit 1
fi;

if ! [ -e "/opt/aucboard" ]; then
    echo "Aucboard is not installed...";
    exit 1
fi;

sudo rm -r /opt/aucboard/

systemctl disable --now aucboard
systemctl disable --now aucboard-boot
sudo rm /etc/systemd/system/aucboard.service /etc/systemd/system/aucboard-boot.service
systemctl daemon-reload
sudo loginctl terminate-user aucboard
sudo userdel -f aucboard

echo "Aucboard was successfully uninstalled. Thanks a lot for using it! <3";