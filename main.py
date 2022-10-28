import time
import datetime
import socket
import pyautogui

# HOST = '192.168.20.10'
PORT = 8501
DMResults = {'T1': '6501',
             'T2': '6601',
             'D1': '6701',
             'D2': '6801'}

DMScanners = {'T1': '6001',
              'T2': '6101',
              'D1': '6201',
              'D2': '6301'}

'''
DM starts at 01 thru 04:
01 - front screen ready sets to 1
02 - test program on top sets to 1
03 - pass screen sets to 1
04 - fail screen sets to 1

1. when test program is not on top  :   0 0 0 0
2. when front screen is ready       :   1 1 0 0
3. when pass screen is appeared     :   0 1 1 0
4. when fail screen is appeared     :   0 1 0 1

'''
case = {'disappear': '0 0 0 0',
        'ready': '1 1 0 0',
        'pass': '0 1 1 0',
        'fail': '0 1 0 1'}
HOST = pyautogui.prompt(text='请输入PLC IP 地址:', title='IP Address')
machineID = pyautogui.prompt(text='请输入电脑ID:\n(T1/T2/D1/D2)', title='PLC DM号')
DMResult = DMResults[machineID]
DMScanner = DMScanners[machineID]


def sendByte(mach, command):
    return bytes(" ".join(["WRS", f"DM{mach}", "4", f"{command}\r"]), "UTF-8")


while True:
    t1 = datetime.datetime.now()
    fail = pyautogui.locateCenterOnScreen('fail.png', confidence=0.4)
    ok = pyautogui.locateCenterOnScreen('pass.png', confidence=0.4)
    front = pyautogui.locateCenterOnScreen('front.png', confidence=0.4)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.connect((HOST, PORT))
            if fail is not None:
                pyautogui.press('enter')
                print(datetime.datetime.now(), 'fail found!')
                s.sendall(sendByte(DMResult, case['fail']))

            elif ok is not None:
                pyautogui.press('enter')
                print(datetime.datetime.now(), 'pass found!')
                s.sendall(sendByte(DMResult, case['pass']))
            elif front is not None:
                print(datetime.datetime.now(), 'ready')
                s.sendall(sendByte(DMResult, case['ready']))
                s.sendall(bytes(' '.join(['RD', f'DM{DMScanner}\r'])))
                scannerActive = s.recv(5)
                startScanTime = datetime.datetime.now()
                while scannerActive == '00001':
                    print('扫描枪活激')
                    testing = pyautogui.locateCenterOnScreen('testing.png', confidence=0.4)
                    if testing is not None:
                        print(f'测试中！{datetime.datetime.now() - startScanTime}')
                        s.sendall(bytes(' '.join(['WR', f'DM{DMScanner}, 0\r'])))
                        break
                    elif (datetime.datetime.now() - startScanTime).total_seconds() > 10:
                        print('测试程序出错！')
                        s.sendall(sendByte(DMResult, case['disappear']))

            else:
                print('Test Program disappeared')
                s.sendall(sendByte(DMResult, case['disappear']))
        except Exception as e:
            print(e)
        finally:
            print('time elapsed:' + str(datetime.datetime.now() - t1))

    time.sleep(0.2)
