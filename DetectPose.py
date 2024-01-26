import mediapipe as mp
import cv2
import math

class DetectPose():
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mp_drawing = mp.solutions.drawing_utils
        self.prev_center_x = -1
        self.prev_center_y = -1
        self.shoudler_line_y = 0

    def center_x(self, image, results):
        return int((results.pose_landmarks.landmark[11].x +
                            results.pose_landmarks.landmark[12].x +
                            results.pose_landmarks.landmark[23].x +
                            results.pose_landmarks.landmark[24].x) / 4 * image.shape[1])

    def detectPose(self, image):
        # Chuyển RGB
        imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Lấy kết quả đầu ra qua model
        results = self.pose.process(imageRGB)

        if results.pose_landmarks:
            self.mp_drawing.draw_landmarks(image, landmark_list=results.pose_landmarks,
                                           connections=self.mp_pose.POSE_CONNECTIONS,
                                           landmark_drawing_spec=self.mp_drawing.DrawingSpec(color=(255, 225, 255),
                                                                                             thickness=3,
                                                                                             circle_radius=3),
                                           connection_drawing_spec=self.mp_drawing.DrawingSpec(color=(0, 0, 255),
                                                                                               thickness=2))

        return image, results

    def checkPose_LCR(self, image, results):
        new_center_x = self.center_x(image, results)
        delta_x = new_center_x - self.prev_center_x

        if delta_x < -20:
            LCR = "Left"
        elif delta_x > 20:
            LCR = "Right"
        else:
            LCR = "Center"

        self.prev_center_x = new_center_x

        return image, LCR

    def checkPose_JSD(self, image, results):
        image_height, image_width, _ = image.shape

        leftShoulder_y = int(results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_height)
        rightShoulder_y = int(results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_height)

        centerShoulder_y = abs(leftShoulder_y + rightShoulder_y) // 2

        jump_threshold = 30
        down_threshold = 15

        if (centerShoulder_y < self.shoudler_line_y - jump_threshold):
            JSD = "Jump"
        elif (centerShoulder_y > self.shoudler_line_y + down_threshold):
            JSD = "Down"
        else:
            JSD = "Stand"

        return image, JSD

    def checkPose_Clap(self, image, results):

        image_height, image_width, _ = image.shape

        left_hand = (results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST].x * image_width,
                     results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST].y * image_height)

        right_hand = (results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST].x * image_width,
                      results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST].y * image_height)

        distance = int(math.hypot(left_hand[0] - right_hand[0], left_hand[1] - right_hand[1]))

        clap_threshold = 100
        if distance < clap_threshold:
            CLAP = "Clap"
        else:
            CLAP = "NoClap"

        cv2.putText(image, CLAP, (10, 30), cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 0), 3)

        return image, CLAP

    def save_shoulder_line_y(self, image, results):
        image_height, image_width, _ = image.shape

        leftShoulder_y = int(results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_height)
        rightShoulder_y = int(
            results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_height)

        self.shoudler_line_y = abs(leftShoulder_y + rightShoulder_y) // 2
        return