import math
from mediapipe.python.solutions.hands import HandLandmark
import time
 


# This file implements the gestures and motions.
# It is explicitly seperated from the gesture_recognizer.py file to make it easier to add new gestures and motions.
# To add a new gesture or motion, add a new gesture name and implement the gesture / motion function.
# Then add the gesture / motion function to the functions list at the bottom of the file 
# so it will be checked for recognition every frame by the gesture recognizer.
# TODO: Making thresholds dynamic based on hand size


class GestureResult():
    def __init__(self, was_gesture_recognized=False, gesture_name="No gesture recognized"):
        self.was_gesture_recognized = was_gesture_recognized
        self.gesture_name = gesture_name


# ----------------------------- Helper functions ----------------------------- #
def calculate_distance(point1, point2):
    return math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)


def are_fingers_extended(hand_landmarks, extended_threshold=0.1):
    tips = [
        HandLandmark.THUMB_TIP,
        HandLandmark.INDEX_FINGER_TIP,
        HandLandmark.MIDDLE_FINGER_TIP,
        HandLandmark.RING_FINGER_TIP,
        HandLandmark.PINKY_TIP
    ]
    
    mcps = [
        HandLandmark.THUMB_CMC,  # For thumb, use CMC as a base
        HandLandmark.INDEX_FINGER_MCP,
        HandLandmark.MIDDLE_FINGER_MCP,
        HandLandmark.RING_FINGER_MCP,
        HandLandmark.PINKY_MCP
    ]
    
    finger_extended = {}

    for tip, mcp in zip(tips, mcps):
        # Calculate Euclidean distance between the tip and MCP
        distance_tip_mcp = calculate_distance(hand_landmarks.landmark[tip], hand_landmarks.landmark[mcp])

        # Check if the tip is farther than the threshold from the MCP
        finger_extended[tip] = distance_tip_mcp > extended_threshold

    return finger_extended


def is_thumb_and_index_touching(hand_landmarks, distance_threshold=0.04):
    thumb_tip = hand_landmarks.landmark[HandLandmark.THUMB_TIP]
    index_tip = hand_landmarks.landmark[HandLandmark.INDEX_FINGER_TIP]

    # Check if the thumb tip and index tip are close to each other
    if calculate_distance(thumb_tip, index_tip) < distance_threshold:
        return True
    
    return False


# --------------------------- Single frame gestures -------------------------- #
def gesture_ok(multi_hand_landmarks):
    for hand_landmarks in multi_hand_landmarks:
        if is_thumb_and_index_touching(hand_landmarks):
            return GestureResult(True, "ok")
        
    return GestureResult()


# --------------------------- Multi frame gestures --------------------------- #
class MultiFrameState:
    def __init__(self, gesture_duration_threshold=2.0, max_dropout_frames=5):
        self.start_time = None
        self.gesture_active = False
        self.dropout_count = 0
        self.gesture_duration_threshold = gesture_duration_threshold
        self.max_dropout_frames = max_dropout_frames
        self.multi_hand_landmarks_list = [] # Store multi_hand_landmarks here for gesture analysis (e.g. tracking hand positions)

    def reset(self):
        self.start_time = None
        self.gesture_active = False
        self.dropout_count = 0
        self.multi_hand_landmarks_list = []


class MultiFrameStateHandler:
    def __init__(self):
        self.states = []
    
    def increase_dropout_count_all(self):
        for state in self.states:
            state.dropout_count += 1
            if state.dropout_count > state.max_dropout_frames:
                print("Reset because no landmarks detected")
                state.reset()

    def increase_dropout_count(self, state):
        state.dropout_count += 1
        if state.dropout_count > state.max_dropout_frames:
            state.reset()

    def add_state(self, state):
        self.states.append(state)

multi_frame_state_handler = MultiFrameStateHandler()


toggle_freeze_state =  MultiFrameState(2, 5)
multi_frame_state_handler.add_state(toggle_freeze_state)

def gesture_toggle_freeze(multi_hand_landmarks):
    state = toggle_freeze_state

    if len(multi_hand_landmarks) < 2:
        multi_frame_state_handler.increase_dropout_count(state)
        return GestureResult()
    
    # If hands are detected, reset dropout count
    state.dropout_count = 0

    both_hands_open = all([are_fingers_extended(hand_landmarks) for hand_landmarks in multi_hand_landmarks])

    if both_hands_open:
        # Start timing if not already active
        if state.start_time is None:
            state.start_time = time.time()
            state.gesture_active = True
        
        # Check if gesture has been active for long enough
        elapsed_time = time.time() - state.start_time
        if elapsed_time > state.gesture_duration_threshold:
            state.reset()
            print("Reset because threshold not reached")
            return GestureResult(True, "toggle_freeze")
        else:
            return GestureResult()

    # If gesture is not recognized, reset timing
    state.reset()
    print("Reset because not both hands open")
    return GestureResult()


switch_content_state = MultiFrameState(2, 5)
multi_frame_state_handler.add_state(switch_content_state)

def gesture_switch_content(multi_hand_landmarks):
    state = switch_content_state

    # If hands are detected, reset dropout count
    state.dropout_count = 0

    left_hand_open = False
    right_hand_open = False

    if len(multi_hand_landmarks) >= 1:
        left_hand_open = are_fingers_extended(multi_hand_landmarks[0])
    if len(multi_hand_landmarks) >= 2:
        right_hand_open = are_fingers_extended(multi_hand_landmarks[1])

    # Reset if both hands are open
    if left_hand_open and right_hand_open:
        state.reset()
        return GestureResult()
    
    # Check if gesture is active
    if left_hand_open or right_hand_open:
        if state.start_time is None:
            state.start_time = time.time()
            state.gesture_active = True
        
        # Check if gesture has been active for long enough
        elapsed_time = time.time() - state.start_time
        if elapsed_time > state.gesture_duration_threshold:
            state.reset()
            if left_hand_open:
                return GestureResult(True, "switch_content_previous")
            if right_hand_open:
                return GestureResult(True, "switch_content_next")
        else:
            return GestureResult()

    # If gesture is not recognized, reset timing
    state.reset()
    return GestureResult()


# ------------------------------ Gestures to analyze ------------------------------ #
functions = [
    # Single frame gestures
    gesture_ok,

    # Multi frame gestures
    gesture_toggle_freeze,
    gesture_switch_content,
]


def analyze_multi_hand_landmarks(multi_hand_landmarks) -> GestureResult:
    # Check for all gestures
    for function in functions:
        gesture_result = function(multi_hand_landmarks)
        if gesture_result.was_gesture_recognized:
            return gesture_result
    
    # No gesture recognized
    return GestureResult()
