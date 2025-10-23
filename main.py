#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自动化测试监控工具
功能：监控测试程序界面状态，与PLC通信并发送相应控制命令
版本：3.0
作者：TTestCheck Team
"""

import json  # 用于处理JSON配置文件
import time  # 用于延时操作
import datetime  # 用于获取当前时间
import socket  # 用于与PLC建立网络连接
import colorama  # 用于控制台彩色输出
import pyautogui  # 用于屏幕截图和自动化操作
import threading  # 用于多线程操作
from colorama import Back, Fore  # 导入颜色常量


# PLC通信配置
# HOST = '192.168.20.10'  # PLC主机IP地址（注释掉，通过用户输入获取）
PORT = 8501  # PLC通信端口

# 设备结果地址映射
# 不同设备类型对应的PLC数据存储地址
DMResults = {'T1': '6501',  # 测试设备1的结果地址
             'T2': '6601',  # 测试设备2的结果地址
             'D1': '6701',  # 显示设备1的结果地址
             'D2': '6801',  # 显示设备2的结果地址
             'NFC': '6901'  # NFC设备的结果地址
            }

# 设备扫描器地址映射
# 不同设备类型对应的PLC扫描器地址
DMScanners = {'T1': '6001',  # 测试设备1的扫描器地址
              'T2': '6101',  # 测试设备2的扫描器地址
              'D1': '6201',  # 显示设备1的扫描器地址
              'D2': '6301',  # 显示设备2的扫描器地址
              'NFC': '6401'  # NFC设备的扫描器地址
             }

# 心跳接收地址映射
# 不同设备类型对应的PLC心跳接收地址
heartbeat_recv = {'T1': '6010',  # 测试设备1的心跳接收地址
                  'T2': '6110',  # 测试设备2的心跳接收地址
                  'D1': '6210',  # 显示设备1的心跳接收地址
                  'D2': '6310',  # 显示设备2的心跳接收地址
                  'NFC': '6410'  # NFC设备的心跳接收地址
                 }

# 心跳发送地址映射
# 不同设备类型对应的PLC心跳发送地址
heartbeat_send = {'T1': '6510',  # 测试设备1的心跳发送地址
                  'T2': '6610',  # 测试设备2的心跳发送地址
                  'D1': '6710',  # 显示设备1的心跳发送地址
                  'D2': '6810',  # 显示设备2的心跳发送地址
                  'NFC': '6910'  # NFC设备的心跳发送地址
                 }


"""
DM状态位说明（每一位代表不同的屏幕状态）：
01 - 前屏幕就绪状态（就绪时设置为1）
02 - 测试程序在前台运行（运行时设置为1）
03 - 测试通过屏幕显示（通过时设置为1）
04 - 测试失败屏幕显示（失败时设置为1）

状态码含义：
1. 当测试程序不在前台:   0 0 0 0 (disappear)
2. 当前屏幕就绪:       1 1 0 0 (ready)
3. 当通过屏幕出现:     0 1 1 0 (pass)
4. 当失败屏幕出现:     0 1 0 1 (fail)
"""
case = {'disappear': '0 0 0 0',  # 测试程序不可见
        'ready': '1 1 0 0',     # 就绪状态
        'pass': '0 1 1 0',      # 测试通过
        'fail': '0 1 0 1'       # 测试失败
       }



def loadSettings():
    """
    加载配置文件
    
    返回值：
        dict: 包含defaultIP和defaultDM和NFCModel的配置字典
    """
    with open('settings.json', 'r') as settingsFile:
        return json.load(settingsFile)


def saveSettings(IP, DM, NFCModel):
    """
    保存配置到文件
    
    参数：
        IP (str): PLC的IP地址
        DM (str): 设备标识符（如'T1', 'T2'等）
        NFCModel (str): NFC模型（如'PN532'等）
    """
    with open('settings.json', 'w') as settingsFile:
        Settings = {'defaultIP': IP, 'defaultDM': DM, 'defaultNFCModel': NFCModel}
        json.dump(Settings, settingsFile)


def heartBeat(s_addr, r_addr):
    """
    心跳检测函数，用于维持与PLC的连接状态
    
    参数：
        s_addr (str): 心跳发送地址
        r_addr (str): 心跳接收地址
    """
    startHBTime = time.time()  # 记录心跳开始时间
    endHBTime = 0  # 心跳结束时间，初始化为0
    
    # 无限循环保持心跳
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as h:  # 创建TCP套接字
            try:
                if endHBTime != 0:  # 不是第一次执行心跳
                    startHBTime = endHBTime  # 更新开始时间
                
                h.connect((HOST, PORT))  # 连接到PLC
                # 发送读取命令，读取心跳接收地址的值
                h.sendall(bytes(' '.join(['RD', f'DM{r_addr}\r']), "UTF-8"))
                # 接收PLC返回的数据，取第2-4个字节
                heartBit = h.recv(5)[2:5]
                
                print(Fore.YELLOW + str(heartBit))  # 黄色输出心跳信号
                
                # 根据接收到的心跳信号，发送相反的信号
                if heartBit == b'100':
                    h.sendall(bytes(' '.join(['WR', f'DM{s_addr}', f'{b"200".decode()}\r']), "UTF-8"))
                elif heartBit == b'200':
                    h.sendall(bytes(' '.join(['WR', f'DM{s_addr}', f'{b"100".decode()}\r']), "UTF-8"))
                
                time.sleep(0.5)  # 等待0.5秒后再次发送心跳
                endHBTime = time.time()  # 更新结束时间
                
            except Exception as e:
                print(e)  # 打印异常信息
            finally:
                # 输出心跳时间间隔
                print(Fore.YELLOW + f'HeartBeat received/sent:, Time elapsed:{endHBTime - startHBTime}s')


def sendByte(mach, command):
    """
    生成PLC通信字节命令
    
    参数：
        mach (str): 目标设备地址
        command (str): 要发送的命令字符串
        
    返回值：
        bytes: 格式化后的字节命令
    """
    return bytes(" ".join(["WRS", f"DM{mach}", "4", f"{command}\r"]), "UTF-8")


def main():
    """
    主函数：监控屏幕状态并与PLC通信
    """
    # back = 0  # 注释掉的状态变量，可能用于跟踪测试程序状态
    
    # 无限循环进行监控
    while True:
        t1 = datetime.datetime.now()  # 记录循环开始时间
        
        # 在屏幕上查找关键图像，confidence参数控制匹配精度
        fail = pyautogui.locateCenterOnScreen('fail.png', confidence=0.6)  # 查找失败图像
        ok = pyautogui.locateCenterOnScreen('pass.png', confidence=0.6)   # 查找通过图像
        front = pyautogui.locateCenterOnScreen('front.png', confidence=0.4)  # 查找就绪图像
        nfcScreen = pyautogui.locateCenterOnScreen(f'{NFCModel}.png', confidence=0.6)  # 查找NFC图像
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # 创建TCP套接字
            try:
                s.connect((HOST, PORT))  # 连接到PLC
                
                # 根据屏幕检测结果发送相应命令
                if fail is not None:  # 检测到失败图像
                    pyautogui.press('enter')  # 自动按回车键
                    print(Back.RED + str(datetime.datetime.now()), 'fail found!')  # 红色输出失败信息
                    s.sendall(sendByte(DMResult, case['fail']))  # 发送失败状态命令
                    # back = 1

                elif ok is not None:  # 检测到通过图像
                    pyautogui.press('enter')  # 自动按回车键
                    print(Back.GREEN + str(datetime.datetime.now()), 'pass found!')  # 绿色输出通过信息
                    s.sendall(sendByte(DMResult, case['pass']))  # 发送通过状态命令
                    # back = 1
                
                elif front is not None:  # 检测到就绪图像
                    # 以下代码被注释掉，可能是自动导航功能
                    # if back == 1:
                    #     setup = pyautogui.locateCenterOnScreen('setup.png', confidence=0.6)
                    #     if setup is not None:
                    #         x, y = setup
                    #         pyautogui.click(x, y)
                    #     home = pyautogui.locateCenterOnScreen('home.png', confidence=0.6)
                    #     if home is not None:
                    #         xh, yh = home
                    #         pyautogui.moveTo(xh, yh, 1)
                    #         pyautogui.click()
                    #     back = 0
                    if machineID == 'NFC':
                        if nfcScreen is not None:
                            print(str(datetime.datetime.now()), 'ready')  # 输出就绪信息
                            s.sendall(sendByte(DMResult, case['ready']))
                        else:
                            print(Back.RED + str(datetime.datetime.now()), 'NFC model not match!')  # 输出NFC未找到信息
                            s.sendall(sendByte(DMResult, case['fail']))  # 发送NFC未找到状态命令
                   

                    print(str(datetime.datetime.now()), 'ready')  # 输出就绪信息
                    s.sendall(sendByte(DMResult, case['ready']))  # 发送就绪状态命令

                else:  # 未检测到任何关键图像
                    print(Back.BLUE + 'Test Program disappeared')  # 蓝色输出程序消失信息
                    s.sendall(sendByte(DMResult, case['disappear']))  # 发送程序不可见状态命令
                    
            except Exception as e:
                print(e)  # 打印异常信息
            finally:
                # 输出本次循环的执行时间
                print('time elapsed:' + str(datetime.datetime.now() - t1))

        time.sleep(0.5)  # 等待0.5秒后再次执行循环


if __name__ == '__main__':
    """
    程序入口
    """
    colorama.init(autoreset=True)  # 初始化colorama库，设置自动重置颜色
    
    # 加载配置文件
    settings = loadSettings()
    defaultIP = settings['defaultIP']  # 获取默认IP地址
    defaultDM = settings['defaultDM']  # 获取默认设备类型
    defaultNFCModel = settings['defaultNFCModel']  # 获取默认NFC模型
    
    # 通过对话框获取用户输入的IP和设备ID
    HOST = pyautogui.prompt(text='请输入PLC IP 地址:', title='IP Address', default=defaultIP)
    machineID = pyautogui.prompt(text='请输入电脑ID:\n(T1/T2/D1/D2/NFC)', title='PLC DM号', default=defaultDM)
    if machineID == 'NFC':
        NFCModel = pyautogui.prompt(text='请输入NFC模型:\n', title='NFC模型', default=defaultNFCModel)
    else:
        NFCModel = defaultNFCModel
     
    # 根据设备ID获取对应的地址
    DMResult = DMResults[machineID]
    DMScanner = DMScanners[machineID]
    
    # 保存用户设置
    saveSettings(HOST, machineID, NFCModel)

    # 创建并启动心跳线程
    heartbeat_thread = threading.Thread(target=heartBeat, args=(heartbeat_send[machineID], heartbeat_recv[machineID]))
    # 创建并启动主监控线程
    main_thread = threading.Thread(target=main)
    
    # 启动线程
    heartbeat_thread.start()
    main_thread.start()