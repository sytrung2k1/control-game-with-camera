import cv2
import pyautogui
import argparse
from CentralPosPose import CentralPosPose
from ShoulderPosPose import ShoulderPosPose
from DetectPose import DetectPose
from take_action import  take_action

ap = argparse.ArgumentParser()
ap.add_argument('--option', type=str, default='combine', help='Pose estimator to use: "central" or "shoulder" or "combine')
args = vars(ap.parse_args())

# Choose the pose estimator based on the argument
if args["option"] == 'central':
    pose_estimator = CentralPosPose()
elif args["option"] == 'shoulder':
    pose_estimator = ShoulderPosPose()
elif args["option"] == 'combine':
    pose_estimator = DetectPose()
else:
    raise ValueError('Invalid pose estimator. Choose "central" or "shoulder".')

move = take_action()
FRAME_PER_ACTION = 3
frame_count = 0  # Số frame đã xử lý

# Khởi tạo camera
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 960)

while cap.isOpened():
    ret, image = cap.read()
    if not ret:
        break

    image = cv2.flip(image, 1)
    image, results = pose_estimator.detectPose(image)

    if results.pose_landmarks:
        if move.game_start:
            if frame_count % FRAME_PER_ACTION == 0:
                if args["option"] == 'central':
                    image, LCR= pose_estimator.checkPose_LCR(image, results)
                    image, JSD = pose_estimator.checkPose_JSD(image, results)
                elif args["option"] == 'shoulder':
                    image, LCR = pose_estimator.checkPose_LCR(image, results)
                    image, JSD = pose_estimator.checkPose_JSD(image, results)
                elif args["option"] == 'combine':
                    image, LCR = pose_estimator.checkPose_LCR(image, results)
                    image, JSD = pose_estimator.checkPose_JSD(image, results)

                move.move(LCR, JSD)

            frame_count += 1

            cv2.putText(image, LCR, (5, image.shape[0] - 10), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)
            cv2.putText(image, JSD, (5, image.shape[0] - 50), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 3)

            if args["option"] == 'central':
                cv2.circle(image, (pose_estimator.prev_center_x, pose_estimator.prev_center_y), 5, (0, 0, 255), -1)
            elif args["option"] == 'shoulder':
                cv2.line(image, (image.shape[1] // 2, 0), (image.shape[1] // 2, image.shape[0]), (255, 255, 255), 2)
                cv2.line(image, (0, pose_estimator.shoudler_line_y), (image.shape[1], pose_estimator.shoudler_line_y), (0, 255, 255), 2)
            elif args["option"] == 'combine':
                cv2.circle(image, (pose_estimator.prev_center_x, pose_estimator.prev_center_y), 5, (0, 0, 255), -1)
                cv2.line(image, (0, pose_estimator.shoudler_line_y), (image.shape[1], pose_estimator.shoudler_line_y),
                     (0, 255, 255), 2)

        else:
            cv2.putText(image, "Clap your hand to start!", (5, image.shape[0] - 10), cv2.FONT_HERSHEY_PLAIN, 2, (255,255,0), 3)

        image, CLAP = pose_estimator.checkPose_Clap(image, results)
        if CLAP == "Clap":
            move.clap_duration += 1
            if move.clap_duration == 10:
                if move.game_start:
                    # Reset
                    move.x_position = 1
                    move.y_position = 1

                    if args["option"] == 'central':
                        pose_estimator.prev_center_x = pose_estimator.center_x(image, results)
                        pose_estimator.prev_center_y = pose_estimator.center_y(image, results)
                    elif args["option"] == 'shoulder':
                        pose_estimator.save_shoulder_line_y(image, results)
                    elif args["option"] == 'combine':
                        pose_estimator.prev_center_x = pose_estimator.center_x(image, results)
                        pose_estimator.save_shoulder_line_y(image, results)

                    pyautogui.press('space')

                else:
                    # New Game
                    move.game_start = True

                    if args["option"] == 'central':
                        pose_estimator.prev_center_x = pose_estimator.center_x(image, results)
                        pose_estimator.prev_center_y = pose_estimator.center_y(image, results)
                    elif args["option"] == 'shoulder':
                        pose_estimator.save_shoulder_line_y(image, results)
                    elif args["option"] == 'combine':
                        pose_estimator.prev_center_x = pose_estimator.center_x(image, results)
                        pose_estimator.save_shoulder_line_y(image, results)

                    pyautogui.click(x=720, y=560, button="left")

                move.clap_duration = 0
        else:
            move.clap_duration = 0

    cv2.imshow("Pose Estimation", image)

    # Điều khiển phím thoát (bấm 'q' để thoát)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()