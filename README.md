#Config the Windows PC environment
1. Install all tools in tools folder
    1) Install python-2.7.11.amd64.msi
    2) Install MSP430Flasher-1_03_07_00-windows-installer.exe
        NOTE1: Do not change the default installed folder(shoule be C:\TI\MSP430Flasher_1.3.7)
        NOTE2: MSP430Flasher will ask user to download USB FET drivers which is already in this tools folder, so ignore this
    3) Install MSP430Drivers-1_00_00_01-windows-installer.exe
    4) Reboot PC

2. Config environment
    1) Modify ip_address.txt in src folder, the PI's ip address should be store into this file

3. How to use 
    1) Double click to open mcu_client.py in src folder
    2) Connect FET and Crosby board to PC
    3) MCU will be upgraded automatically

