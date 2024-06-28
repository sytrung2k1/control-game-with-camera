import socket
import time
import cv2
from detect_actions import Actions, Status, DetectActions
import threading
import select

stop_event = threading.Event()

def handle_communication(sock):
    while not stop_event.is_set():
        ready_to_read, _, _ = select.select([sock], [], [], 0.1)
        if ready_to_read:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode()
                print("Received message from Unity:", message)
                if message == "START":
                    # Xử lý dữ liệu nhận được từ Unity ở đây
                    pose_estimation.prev_center_x = pose_estimation.center_x(frame, results)
                    pose_estimation.prev_center_y = pose_estimation.center_y(frame, results)
                    pose_estimation.save_shoulder_line_y(frame, results)

                if message == "CLOSE":
                    stop_event.set()
            except Exception as e:
                # print("Error:", str(e))
                pass

pose_estimation = DetectActions()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
# cap.set(cv2.CAP_PROP_FPS, 30)

# Khởi tạo socket UDP
server_address = ('localhost', 12345)

with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.setblocking(0)

    # Gửi message tới Unity
    for i in range(10):
        message = b"READY"
        sock.sendto(message, server_address)

        # Nhận phản hồi từ Unity
        ready_to_read, _, _ = select.select([sock], [], [], 0.1)
        if ready_to_read:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode()
                print("Received message from Unity:", message)
                if message == "OK":
                    break  # Dừng vòng lặp khi nhận được phản hồi từ Unity
            except Exception as e:
                # print("Error:", str(e))
                pass

    print("Received OK message, continuing with the rest of the code...")

    communication_thread = threading.Thread(target=handle_communication, args=(sock,))
    communication_thread.start()

    LCR_last_actions = ""
    JSD_last_actions = ""
    stop_duration = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        frame, results, actions, status = pose_estimation.detect_pose(frame)

        if status == Status.STOP.value:
            stop_duration += 1
            if stop_duration == 20:
                actions = "STOP"
                stop_duration = 0
            else:
                actions = ""
        elif status == Status.ACTIVE.value:
            if actions != Actions.NONE.value:
                LCR_actions, JSD_actions = actions.split(";")
                LCR_actions = Actions(LCR_actions).value
                JSD_actions = Actions(JSD_actions).value
            
                if LCR_actions != LCR_last_actions or JSD_actions != JSD_last_actions:
                    actions = f"{LCR_actions};{JSD_actions}"
                    LCR_last_actions = LCR_actions
                    JSD_last_actions = JSD_actions
                else:
                    actions = ""
            
                cv2.putText(frame, LCR_actions, (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2, cv2.LINE_AA)
                cv2.putText(frame, JSD_actions, (5, 100), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 2, cv2.LINE_AA)

                cv2.circle(frame, (pose_estimation.prev_center_x, pose_estimation.prev_center_y), 5, (0, 0, 255), -1)
                cv2.line(frame, (0, pose_estimation.shoulder_line_y), (frame.shape[1], pose_estimation.shoulder_line_y), (0, 255, 255), 2)

        if actions:
            message = bytes(actions, "utf-8")
            sock.sendto(message, server_address)

        cv2.imshow("Controller", cv2.resize(frame, (640, 360)))
        if (cv2.waitKey(1) & 0xFF == ord('q')) or stop_event.is_set():
            stop_event.set()
            break

    cap.release()
    cv2.destroyAllWindows()

communication_thread.join()