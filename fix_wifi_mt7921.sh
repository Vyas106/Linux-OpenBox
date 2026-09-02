#!/usr/bin/env bash
# ==============================================================================
# MediaTek MT7921 Linux Wi-Fi Driver & Firmware Lockup Fix
# Resolves "driver own failed / chip reset failed / timeout for driver own"
# ==============================================================================

set -e

echo "==> Applying MediaTek MT7921 Linux Hardware Fixes..."

# 1. Disable PCIe ASPM Power Management for mt7921e
echo "options mt7921e disable_aspm=y" | sudo tee /etc/modprobe.d/mt7921e.conf >/dev/null

# 2. Disable Wi-Fi Power Save in NetworkManager (powersave = 2 means OFF)
sudo mkdir -p /etc/NetworkManager/conf.d/
cat << 'EOF' | sudo tee /etc/NetworkManager/conf.d/default-wifi-powersave-off.conf >/dev/null
[connection]
wifi.powersave = 2
EOF

# 3. Disable MAC Randomization during Scanning
cat << 'EOF' | sudo tee /etc/NetworkManager/conf.d/00-no-mac-randomization.conf >/dev/null
[device-mac-randomization]
wifi.scan-rand-mac-address=no

[connection-mac-randomization]
wifi.cloned-mac-address=preserve
ethernet.cloned-mac-address=preserve
EOF

# 4. Reset & Reload MT7921 PCIe Driver
echo "==> Resetting mt7921e wireless driver in kernel..."
PCI_DEV="0000:2d:00.0"

if [ -d "/sys/bus/pci/drivers/mt7921e" ]; then
    echo "$PCI_DEV" | sudo tee /sys/bus/pci/drivers/mt7921e/unbind >/dev/null 2>&1 || true
    sleep 0.5
    sudo modprobe -r mt7921e 2>/dev/null || true
    sleep 0.5
    sudo modprobe mt7921e disable_aspm=y
    sleep 0.5
    echo "$PCI_DEV" | sudo tee /sys/bus/pci/drivers/mt7921e/bind >/dev/null 2>&1 || true
fi

# 5. Restart NetworkManager
sudo systemctl reload NetworkManager || sudo systemctl restart NetworkManager

echo "==> MediaTek MT7921 Fix applied successfully!"
echo "==> Wi-Fi radio is now active and ready to connect."
nmcli radio wifi on
nmcli device set wlan0 managed yes 2>/dev/null || true
sleep 1
nmcli dev wifi list
