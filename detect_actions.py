import cv2
from enum import Enum
import mediapipe as mp
import numpy as np

# Define the possible actions as an enumeration
class Actions(Enum):
    LEFT = "Left"
    RIGHT = "Right"
    CENTER = "Center"
    JUMP = "Jump"
    DOWN = "Down"
    STAND = "Stand"
    NONE = "None"

# Define the possible statuses as an enumeration
class Status(Enum):
    ACTIVE = "Active"
    STOP = "Stop"

class DetectActions:
    # 30, 100 là cuar 1280x720 
    # Có thể sẽ phải giảm xuống 1 nửa vì kích thước frame đã giảm 1 nửa
    THRESHOLD_LCR = 30  # Threshold for left, center, right actions
    THRESHOLD_JSD = 100  # Threshold for jump, stand, down actions

    # Define drawing specifications for landmarks and connections
    LANDMARKS_DRAWING_SPEC = mp.solutions.drawing_utils.DrawingSpec(color=(121, 22, 75), thickness=2, circle_radius=4)
    CONNECTION_DRAWING_SPEC = mp.solutions.drawing_utils.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2)

    def __init__(self):
        # Initialize pose detection
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose()
        self.mp_drawing = mp.solutions.drawing_utils
        self.prev_center_x = -1  # Previous center x coordinate
        self.prev_center_y = -1  # Previous center y coordinate
        self.shoulder_line_y = 0  # Y coordinate of the shoulder line

    # Calculate the average of the x or y coordinates of the landmarks
    def calculate_average(self, image, results, axis):
        if results.pose_landmarks is None:
            return -1
        landmarks = results.pose_landmarks.landmark
        coordinates = np.array([landmarks[i].x if axis == 'x' else landmarks[i].y for i in [11, 12, 23, 24]])
        coordinates = [landmarks[i].x if axis == 'x' else landmarks[i].y for i in [11, 12, 23, 24]]
        return int(np.mean(coordinates) * (image.shape[1] if axis == 'x' else image.shape[0]))
    
    # Calculate the center x coordinate
    def center_x(self, image, results):
        return self.calculate_average(image, results, 'x')
    
    # Calculate the center y coordinate
    def center_y(self, image, results):
        return self.calculate_average(image, results, 'y')
    
    # Detect the pose in the image
    def detect_pose(self, image):
        # image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image)
        if results.pose_landmarks:
            self.draw_landmarks(image, results)
        if self.check_skeleton(results):
            status = Status.ACTIVE
            image, LCR_actions = self.check_actions_LCR(image, results)
            image, JSD_actions = self.check_actions_JSD(image, results)
            actions = str(LCR_actions) + ";" + str(JSD_actions)
        else:
            status = Status.STOP
            actions = ""
        return image, results, actions, status.value
    
    # Draw the landmarks and connections on the image
    def draw_landmarks(self, image, results):
        self.mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=self.LANDMARKS_DRAWING_SPEC,
            connection_drawing_spec=self.CONNECTION_DRAWING_SPEC
        )
        
    # Check if the necessary points are visible in the skeleton
    def check_skeleton(self, results):
        if results.pose_landmarks is None:
            return False

        necessary_points = [11, 12, 23, 24]
        landmarks = results.pose_landmarks.landmark

        return all(landmarks[point].visibility >= 0.5 for point in necessary_points)
        
    # Check for step left, center/ no step, step right actions
    def check_actions_LCR(self, image, results):
        new_center_x = self.center_x(image, results)
        new_center_y = self.center_y(image, results)
        delta = new_center_x - self.prev_center_x

        if delta < -self.THRESHOLD_LCR:
            LCR = Actions.LEFT
        elif delta > self.THRESHOLD_LCR:
            LCR = Actions.RIGHT
        else:
            LCR = Actions.CENTER
        
        self.prev_center_x = new_center_x
        self.prev_center_y = new_center_y

        return image, LCR.value
    
    # Check for jump, stand, down actions
    def check_actions_JSD(self, image, results):
        image_height, image_width, _ = image.shape

        left_shoulder_y = int(results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_height)
        right_shoulder_y = int(results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_height)

        center_shoulder_y = int(abs(left_shoulder_y + right_shoulder_y) // 2)

        if center_shoulder_y < (self.shoulder_line_y - self.THRESHOLD_JSD):
            JSD = Actions.JUMP
        elif center_shoulder_y > (self.shoulder_line_y + self.THRESHOLD_JSD):
            JSD = Actions.DOWN
        else:
            JSD = Actions.STAND
        
        return image, JSD.value
    
    # Save the y coordinate of the shoulder line
    def save_shoulder_line_y(self, image, results):
        image_height, image_width, _ = image.shape

        left_shoulder_y = int(results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER].y * image_height)
        right_shoulder_y = int(results.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER].y * image_height)

        self.shoulder_line_y = int(abs(left_shoulder_y + right_shoulder_y) // 2)
        return