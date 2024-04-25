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

standard_pose = {
    "pose": {
        "nose": {"x": 263.49624144658446, "y": 150.46034732212615, "v": 1.0},
        "neck": {"x": 282.21698733170825, "y": 261.08293664331234, "v": 1.0},
        "right_shoulder": {"x": 202.2283458225429, "y": 255.9772786746422, "v": 1.0},
        "right_elbow": {"x": 174.99816998963558, "y": 405.74324575563287, "v": 1.0},
        "right_wrist": {"x": 140.96045019850135, "y": 536.7884669514992, "v": 1.0},
        "left_shoulder": {"x": 362.2056288408736, "y": 266.18859461198247, "v": 1.0},
        "left_elbow": {"x": 372.41694477821386, "y": 412.55078971385956, "v": 1.0},
        "left_wrist": {"x": 389.43580467378104, "y": 545.2978968992829, "v": 1.0},
        "right_hip": {"x": 200.52645983298612, "y": 506.15451913947845, "v": 1.0},
        "right_knee": {"x": 152.8736521253984, "y": 758.0336455938716, "v": 1.0},
        "right_ankle": {"x": 88.20198452224327, "y": 999.7014561109245, "v": 1.0},
        "left_hip": {"x": 316.25470712284243, "y": 514.6639490872622, "v": 1.0},
        "left_knee": {"x": 309.44716316461563, "y": 761.4374175729852, "v": 1.0},
        "left_ankle": {"x": 283.918873321265, "y": 984.3844822049141, "v": 1.0},
        "right_eye": {"x": 246.4773815510173, "y": 136.84525940567255, "v": 1.0},
        "left_eye": {"x": 282.2169873317083, "y": 131.73960143700242, "v": 1.0},
        "right_ear": {"x": 234.56417962412036, "y": 152.16223331168294, "v": 1.0},
        "left_ear": {"x": 323.06225108106935, "y": 143.65280336389947, "v": 1.0},
    },
    "width": 512,
    "height": 1152,
}


# Define standard ratio
nose_to_neck_ratio = 1/2.2
def calculate_distance(point1, point2):
    # Calculate the Euclidean distance between two points
    return math.sqrt((point1["x"] - point2["x"]) ** 2 + (point1["y"] - point2["y"]) ** 2)

def calculate_translation_vector(originaleft_position, new_position):
    # Calculate the translation vector from the original position to the new position
    return {
        "x": new_position["x"] - originaleft_position["x"],
        "y": new_position["y"] - originaleft_position["y"],
    }

def calculate_distance_neck_hip(pose):
    neck = pose["neck"]
    right_hip = pose["right_hip"]
    left_hip = pose["left_hip"]
    return calculate_distance(neck, {
        "x": (right_hip["x"] + left_hip["x"]) / 2,
        "y": (right_hip["y"] + left_hip["y"]) / 2,
    })

def generate_point_from_point(keypoint, key_point_from, key_point_from_coordinate, d_neck_hip, standard_pose):
    standard_keypoint_from = standard_pose["pose"][key_point_from]
    standard_keypoint = standard_pose["pose"][keypoint]
    scale_factor = d_neck_hip / calculate_distance_neck_hip(standard_pose["pose"])
    return {
        "x": key_point_from_coordinate["x"] + (standard_keypoint["x"] - standard_keypoint_from["x"]) * scale_factor,
        "y": key_point_from_coordinate["y"] + (standard_keypoint["y"] - standard_keypoint_from["y"]) * scale_factor,
    }

def generate_point_from_neck(keypoint, neck, d_neck_hip, standard_pose):
    standard_neck = standard_pose["pose"]["neck"]
    standard_keypoint = standard_pose["pose"][keypoint]
    scale_factor = d_neck_hip / calculate_distance_neck_hip(standard_pose["pose"])
    return {
        "x": neck["x"] + (standard_keypoint["x"] - standard_neck["x"]) * scale_factor,
        "y": neck["y"] + (standard_keypoint["y"] - standard_neck["y"]) * scale_factor,
    }

def generate_face(neck, d_neck_hip, standard_pose):
    generated_face = {
        "neck": generate_point_from_point("neck", "neck", neck, d_neck_hip, standard_pose),
        "nose": generate_point_from_point("nose", "neck", neck, d_neck_hip, standard_pose),
        "right_eye": generate_point_from_point("right_eye", "neck", neck, d_neck_hip, standard_pose),
        "left_eye": generate_point_from_point("left_eye", "neck", neck, d_neck_hip, standard_pose),
        "right_ear": generate_point_from_point("right_ear", "neck", neck, d_neck_hip, standard_pose),
        "left_ear": generate_point_from_point("left_ear", "neck", neck, d_neck_hip, standard_pose),
    }

    return generated_face

def adjust_keypoints(keypoints, fix_neck = False, add_pose_default = False, add_face = False, add_arm = False, add_leg = False, **kwargs):
    # Find the indices of neck and nose in the keypoint_names list
    neck_index = keypoint_names.index("neck")
    nose_index = keypoint_names.index("nose")
    righthip_index = keypoint_names.index("right_hip")
    leftthip_index = keypoint_names.index("left_hip")
    
    keypoint_neck = keypoints[neck_index]
    keypoint_nose = keypoints[nose_index]
    keypoint_righthip = keypoints[righthip_index]
    keypoint_lefthip = keypoints[leftthip_index]
    if keypoint_neck is None or keypoint_righthip is None or keypoint_lefthip is None:
        if add_pose_default:
            for keypoint in keypoint_names:
                index = keypoint_names.index(keypoint)
                keypoints[index] = standard_pose["pose"][keypoint]
        return keypoints, 0

    # Calculate the distance from neck to hip
    d_neck_hip = calculate_distance(keypoint_neck, {
        "x": (keypoint_righthip["x"] + keypoint_lefthip["x"]) / 2,
        "y": (keypoint_righthip["y"] + keypoint_lefthip["y"]) / 2,
    })

    face_exist = True
    face_keypoint = ["nose", "right_eye", "left_eye", "right_ear", "left_ear"]
    for keypoint in face_keypoint:
        index = keypoint_names.index(keypoint)
        if not keypoints[index]:
            face_exist = False
            break

    if fix_neck and face_exist and not add_face:
        # Calculate the distance from neck to nose
        d_neck_nose = calculate_distance(keypoint_neck, keypoint_nose)
        
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
                if keypoints[point_index] is None:
                    continue
                keypoints[point_index]["x"] += translation_vector["x"]
                keypoints[point_index]["y"] += translation_vector["y"]
            
    if add_face:
        face_keypoint = ["nose", "right_eye", "left_eye", "right_ear", "left_ear"]
        for keypoint in face_keypoint:
            index = keypoint_names.index(keypoint)
            keypoints[index] = generate_point_from_neck(keypoint, keypoints[neck_index], d_neck_hip, standard_pose)

    if add_arm:
        hand_keypoint = ["right_wrist", "right_elbow", "right_shoulder", "left_wrist", "left_elbow", "left_shoulder"]
        for keypoint in hand_keypoint:
            index = keypoint_names.index(keypoint)
            keypoints[index] = generate_point_from_neck(keypoint, keypoints[neck_index], d_neck_hip, standard_pose)
                
    if add_leg:
        leg_keypoint = ["right_ankle", "right_knee", "left_ankle", "left_knee"]
        for keypoint in leg_keypoint:
            index = keypoint_names.index(keypoint)
            if keypoints[index] is None:
                keypoints[index] = generate_point_from_neck(keypoint, keypoints[neck_index], d_neck_hip, standard_pose)
    return keypoints, d_neck_hip
