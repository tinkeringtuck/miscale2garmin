#!/usr/bin/python3

import os
from datetime import datetime as dt
from bluepy import btle

# Version Info
print("Export 2 Garmin Connect v1.6 (miscale_ble.py)")
print("")

# Importing bluetooth variables from a file
path = os.path.dirname(os.path.dirname(__file__))
with open(path + '/user/export2garmin.cfg', 'r') as file:
    for line in file:
        line = line.strip()
        if line.startswith('miscale_ble_'):
            name, value = line.split('=')
            globals()[name.strip()] = value.strip()
miscale_ble_time = int(miscale_ble_time)
unique_dev_addresses = []

# Reading data from a scale using a BLE scanner
class miScale(btle.DefaultDelegate):
    def __init__(self):
        btle.DefaultDelegate.__init__(self)
        self.address = miscale_ble_mac.lower()
    def handleDiscovery(self, dev, isNewDev, isNewData):
        if dev.addr not in unique_dev_addresses:
            unique_dev_addresses.append(dev.addr)
            print(f"  BLE device found with address: {dev.addr}" + (" <= target device" if dev.addr == self.address else ", non-target device"))
        if dev.addr == self.address:
            for (adType, desc, value) in dev.getScanData():
                if dev.addr not in unique_dev_addresses:
                    unique_dev_addresses.append(dev.addr)
                    print(f"  BLE device found with address: {dev.addr} <= target device")
                if adType == 22:
                    data = bytes.fromhex(value[4:])
                    ctrlByte1 = data[1]
                    hasImpedance = ctrlByte1 & (1<<1)
                    if value[4:6] == '03':
                        lb_weight = int((value[28:30] + value[26:28]), 16) * 0.01
                        weight = round(lb_weight / 2.2046, 1)
                    else:
                        weight = (((data[12] & 0xFF) << 8) | (data[11] & 0xFF)) * 0.005
                    impedance = ((data[10] & 0xFF) << 8) | (data[9] & 0xFF)
                    unix_time = int(dt.timestamp(dt.strptime(f"{int((data[3] << 8) | data[2])},{int(data[4])},{int(data[5])},{int(data[6])},{int(data[7])},{int(data[8])}","%Y,%m,%d,%H,%M,%S")))
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Reading BLE data complete, finished BLE scan")
                    print(f"{unix_time};{weight:.1f};{impedance:.0f}" if hasImpedance else f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Reading BLE data incomplete, finished BLE scan")
                    exit()
    def run(self):

        # Verifying correct working of BLE device
        if not os.popen(f"hcitool dev | awk '/hci{miscale_ble_hci}/ {{print $2}}'").read():
            print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE device hci{miscale_ble_hci} not detected, restarting bluetooth service")
            os.system("sudo systemctl restart bluetooth.service")
        else:
            while True:
                try:
                    scanner = btle.Scanner(miscale_ble_hci)
                    scanner.withDelegate(self)
                    scanner.start()
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Starting BLE scan:")
                    scanner.process(miscale_ble_time)
                    scanner.stop()
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * Finished BLE scan")
                    break

                # Verifying correct working of BLE connection
                except btle.BTLEManagementError:
                    print(f"{dt.now().strftime('%d.%m.%Y-%H:%M:%S')} * BLE connection error, restarting device hci{miscale_ble_hci}")
                    os.system(f"sudo hciconfig hci{miscale_ble_hci} down && sudo hciconfig hci{miscale_ble_hci} up")
                    break

# Main program loop
if __name__ == "__main__":
    scale = miScale()
    scale.run()