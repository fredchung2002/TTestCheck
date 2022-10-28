import time

import pyautogui as pg

while True:
    succeed = pg.locateCenterOnScreen('2.png', confidence=0.9)
    print(succeed)
    time.sleep(0.5)