import socket, traceback, subprocess, json, os, hashlib, time
from subprocess import PIPE, Popen
from threading import Thread
import threading

host = '127.0.0.1'
port = 9930
WINDOWS_PLATFORM = 1
if (WINDOWS_PLATFORM == 1):
    MCU_PROGRAM_EXE = 'C:\\TI\\MSP430Flasher_1.3.7\\MSP430Flasher.exe'
    PSCP_EXE = 'pscp.exe'
#    FW_MD5_FILE = 'C:\\MCU_Program\\md5.txt'
#    FW_FILE = 'C:\\MCU_Program\\fw.txt'
else:
    MCU_PROGRAM_EXE = '/home/jason/MSP430Flasher_1.3.7/MSP430Flasher'
    PSCP_EXE = '/usr/bin/pscp'

FW_MD5_FILE = 'fw_md5.txt'
FW_FILE = 'fw.txt'
SERVER_IP_FILE = 'ip_address.txt'

#command list
usb_found_cmd = "{\"jsonrpc\":\"2.0\", \"method\":\"dut.connect\",\"params\":{\"dutId\":\"1234567\",\"testId\":\"0\"}}"

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#to do: when socket not availabe need to reconnect

def main():
    #connect to PI
    fet_stop = threading.Event()
    pause_event = threading.Event()
    while 1:
        try:
            s.connect((host, port))
            #ret = s.sendto(usb_found_cmd, addr)
            print 'connect successful'
            break
        except:
            sleep(1)
            print 'reconnect to server'

    #open thread to monitor FET device
    create_FET_monitor_task(fet_stop, pause_event)

    while 1:
        try:
            buf = s.recv(2048)
            print buf
            j = json.loads(buf)
            print j['method']
            if j['method'] == 'test.start':
                pause_event.set()
                time.sleep(1)
                ret = mcu_flash()
                
                if (ret == 1):
                    s.sendto("{\"jsonrpc\":\"2.0\", \"method\":\"test.done\",\"params\":{\"status\":\"PASS\"}}", addr)
                else:
                    s.sendto("{\"jsonrpc\":\"2.0\", \"method\":\"test.done\",\"params\":{\"status\":\"FAIL\"}}", addr)

                time.sleep(1)
                pause_event.clear()
            elif j['method'] == 'firmware.request':
                md5 = get_firmware_md5()
                md5_cmd = "{\"jsonrpc\":\"2.0\", \"method\":\"firmware.response\",\"params\":{\"checksum\":\"" + md5 + "\"}}"
                print md5_cmd
                s.sendto(md5_cmd, addr)
            elif j['method'] == 'firmware.new':
                url = j['params']['url']
                checksum = j['params']['checksum']
                full_url = host + ":" + url
                rsp = download_firmware(full_url, checksum)
                s.sendto(rsp, addr)
        except (KeyboardInterrupt, SystemExit):
            stop_FET_monitor_task(fet_stop)
            raise
        except:
            traceback.print_exc()
def create_FET_monitor_task(fet_stop,pause):
    fet_stop.clear()
    fet_thread = Thread(target = monitor_FET_device_task, args=(1,fet_stop,pause))       
    fet_thread.start()

def stop_FET_monitor_task(fet_stop):
    fet_stop.set()

def monitor_FET_device_task(arg1, stop_event, pause_event):
    #deadloop to check FET device status, stupid, need to be improved
    last_state = 0 # 0 - not found , 1 - found
    while (not stop_event.is_set()):
        try:
            if (not pause_event.is_set()):
                ret = get_device_status()
                if (ret == 1):
                    if (last_state == 0):
                        print 'Send usb found to server'
                        s.sendto(usb_found_cmd, addr)
                        last_state = 1
                else:
                    last_state = 0

            #time.sleep(1)
            stop_event.wait(1)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            traceback.print_exc()


def get_device_status():
    print 'get device status' 
    DeviceConnected = 0
    p = subprocess.Popen(MCU_PROGRAM_EXE, stdout=PIPE, stderr=PIPE)
    while 1:
        line = p.stdout.readline().strip('\n')
        if ("* Reading device information...done" in line):
            while 1:
                line = p.stdout.readline()
                if ("* Driver      : closed (No error)" in line):
                    #the deive is connected with no error
                    DeviceConnected = 1
                    break
                if (line == ''):
                    #deviece is connected but has error
                    break
            break
        if (line == ''):
            break

    return DeviceConnected

def mcu_flash():
    ret = 0
    print 'MCU programing start' 
    p = subprocess.Popen([MCU_PROGRAM_EXE, '-w', FW_FILE, '-v', '-z', '[VCC]'], stdout=PIPE, stdin=PIPE)
#    p = subprocess.Popen(MCU_PROGRAM_EXE, stdout=PIPE, stderr=PIPE)
    while 1:
        line = p.stdout.readline().strip('\n')
        print line
        if (line == ''):
            break
        if ("* Driver      : closed (No error)" in line):
            ret = 1
            break
    
    return ret

def get_firmware_md5():
    try:
        fd = open(FW_MD5_FILE, 'rb')
        line = fd.read().strip('\n')
        return line
    except:
        print 'can not open md5 file'
        return "0"

#    return open(FW_MD5_FILE, 'rb').read()

def download_firmware(url, checksum):
    retrys = 5
    while (retrys > 0):
#        p = subprocess.Popen([PSCP_EXE, '-l', 'jason', '-pw', 'JASONliu11!', url, FW_FILE])
        p = subprocess.Popen([PSCP_EXE, '-l', 'root', url, FW_FILE])
        p.communicate()

        md5 = hashlib.md5(open(FW_FILE, 'rb').read()).hexdigest()
        if (md5 == checksum):
            break
        retrys -= 1

    if (retrys > 0):
        fp = open(FW_MD5_FILE, 'w')
        try:
            fp.write(md5)
        finally:
            fp.close()
        ret = "{\"jsonrpc\":\"2.0\", \"method\":\"firmware.dlok\"}}"
    else:
        ret = "{\"jsonrpc\":\"2.0\", \"method\":\"firmware.dlfail\"}}"
    return ret

#    s.sendto(dl_ok_cmd, addr)

def get_server_ip():
    try:
        fd = open(SERVER_IP_FILE, 'rb')
        line = fd.read().strip('\n')
        return line
    except:
        print 'can not open ip file'
        return "127.0.0.1"

def test():
    fet_stop = threading.Event()
    pause = threading.Event()
    create_FET_monitor_task(fet_stop,pause)
    time.sleep(2)
    print 'pause 5 sec'
    pause.set()
    time.sleep(5)
    
    print 'start again'
    pause.clear()
    time.sleep(5)
    print 'stop'
    stop_FET_monitor_task(fet_stop)
            
#    download_firmware("127.0.0.1:/teknique/ambausb/share/fw.txt", "8d855ac8c0a7ef74b98f69dbfacbaf51")
#    ret = get_device_status()
#    if (ret == 1):
#        ret = mcu_flash()
#        print ret

host = get_server_ip()
addr = (host, port)
main()

#test()
