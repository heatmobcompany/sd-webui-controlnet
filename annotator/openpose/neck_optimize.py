import math

# Static keypoint names
keypoint_names = [
    "nose",
    "neck",
    "right_shoulder",
    "right_elbow",
    "right_wrist",
    "left_shoulder",
    "left_elbow",
    "left_wrist",
    "right_hip",
    "right_knee",
    "right_ankle",
    "left_hip",
    "left_knee",
    "left_ankle",
    "right_eye",
    "left_eye",
    "right_ear",
    "left_ear",
]

# Define standard ratio
nose_to_neck_ratio = 1/2.2

def calculate_distance(point1, point2):
    # Calculate the Euclidean distance between two points
    return math.sqrt((point1["x"] - point2["x"]) ** 2 + (point1["y"] - point2["y"]) ** 2)

def calculate_translation_vector(original_position, new_position):
    # Calculate the translation vector from the original position to the new position
    return {
        "x": new_position["x"] - original_position["x"],
        "y": new_position["y"] - original_position["y"],
    }

def adjust_keypoints(keypoints):
    # Find the indices of neck and nose in the keypoint_names list
    neck_index = keypoint_names.index("neck")
    nose_index = keypoint_names.index("nose")
    
    keypoint_neck = keypoints[neck_index]
    keypoint_nose = keypoints[nose_index]
    if keypoint_neck is None or keypoint_nose is None:
        return keypoints

    # Calculate the distance from neck to nose
    d_neck_nose = calculate_distance(keypoint_neck, keypoint_nose)
    
    # Calculate the distance from neck to hip
    d_neck_hip = calculate_distance(keypoint_neck, keypoints[keypoint_names.index("right_hip")])
    
    # Calculate the rotation
    rotation = d_neck_nose / d_neck_hip
    
    if rotation > nose_to_neck_ratio:
        desired_d_neck_nose = nose_to_neck_ratio * d_neck_hip
        scale_factor = desired_d_neck_nose / d_neck_nose
        
        # Calculate the translation vector for the nose
        translation_vector = calculate_translation_vector(
            keypoint_nose,
            {
                "x": keypoint_neck["x"] + (keypoint_nose["x"] - keypoint_neck["x"]) * scale_factor,
                "y": keypoint_neck["y"] + (keypoint_nose["y"] - keypoint_neck["y"]) * scale_factor,
            }
        )
        
        # Apply the same translation vector to the eyes and ears
        for point_name in ["nose", "right_eye", "left_eye", "right_ear", "left_ear"]:
            point_index = keypoint_names.index(point_name)
            keypoints[point_index]["x"] += translation_vector["x"]
            keypoints[point_index]["y"] += translation_vector["y"]
    
    return keypoints
