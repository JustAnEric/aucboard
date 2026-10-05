#!/bin/bash

if ! [ -e "/opt/aucboard" ]; then
    echo "Aucboard is not installed...";
    exit 1;
fi;

sudo rm -r /opt/aucboard/

systemctl disable --now aucboard
systemctl disable --now aucboard-boot
sudo rm /etc/systemd/system/aucboard.service /etc/systemd/system/aucboard-boot.service
systemctl daemon-reload

echo "Aucboard was successfully uninstalled. Thanks a lot for using it! <3";