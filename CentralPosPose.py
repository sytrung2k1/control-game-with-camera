import mediapipe as mp
import cv2
import math

class CentralPosPose():
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mp_drawing = mp.solutions.drawing_utils
        self.prev_center_x = -1
        self.prev_center_y = -1

    def center_x(self, image, results):
        return int((results.pose_landmarks.landmark[11].x +
                            results.pose_landmarks.landmark[12].x +
                            results.pose_landmarks.landmark[23].x +
                            results.pose_landmarks.landmark[24].x) / 4 * image.shape[1])

    def center_y(self, image, results):
        return int((results.pose_landmarks.landmark[11].y +
                            results.pose_landmarks.landmark[12].y +
                            results.pose_landmarks.landmark[23].y +
                            results.pose_landmarks.landmark[24].y) / 4 * image.shape[0])

    def detectPose(self, image):
        # Convert RGB
        imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Get the results from the pose model
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
        new_center_y = self.center_y(image, results)
        delta_y = new_center_y - self.prev_center_y

        if delta_y < -20:
            JSD = "Jump"
        elif delta_y > 20:
            JSD = "Down"
        else:
            JSD = "Stand"

        self.prev_center_y = new_center_y

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