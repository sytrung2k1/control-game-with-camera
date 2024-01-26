import pyautogui

class take_action():
    def __init__(self):
        self.game_start = False
        self.clap_duration = 0;
        self.x_position = 1 # 0: Left: 1: Center; 2: Right
        self.y_position = 1 # 0: Down: 1: Stand, 2: Junp

    def move(self, LCR, JSD):

        # if LCR == "Left":
        #     # pyautogui.press('left')
        #     # self.x_position -= 1
        #     for _ in range(self.x_position):
        #         pyautogui.press('left')
        #     self.x_position = 0
        # elif LCR == "Right":
        #     # pyautogui.press('right')
        #     # self.x_position += 1
        #     for _ in range(2, self.x_position, -1):
        #         pyautogui.press('right')
        #     self.x_position = 2
        # else:
        #     # pass
        #     if self.x_position == 0:
        #         pyautogui.press('right')
        #     elif self.x_position == 2:
        #         pyautogui.press('left')
        #
        #     self.x_position = 1

        if LCR == "Left" and self.x_position != 0:
            pyautogui.press('left')
            self.x_position -= 1
        elif LCR == "Right" and self.x_position != 2:
            pyautogui.press('right')
            self.x_position += 1
        else:
            pass

        if JSD == "Jump" and self.y_position == 1:
            pyautogui.press('up')
            self.y_position = 2
        elif JSD == "Down" and self.y_position == 1:
            pyautogui.press('down')
            self.y_position = 0
        elif JSD == "Stand" and self.y_position != 1:
            self.y_position = 1

        return