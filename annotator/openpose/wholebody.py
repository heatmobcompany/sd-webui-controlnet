# Copyright (c) OpenMMLab. All rights reserved.
import cv2
import numpy as np

from .cv_ox_det import inference_detector
from .cv_ox_pose import inference_pose

from typing import List, Optional
from .types import PoseResult, BodyResult, Keypoint
from .pose_optimize import adjust_keypoints


class Wholebody:
    def __init__(self, onnx_det: str, onnx_pose: str):
        # Always loads to CPU to avoid building OpenCV.
        device = 'cpu'
        backend = cv2.dnn.DNN_BACKEND_OPENCV if device == 'cpu' else cv2.dnn.DNN_BACKEND_CUDA
        # You need to manually build OpenCV through cmake to work with your GPU.
        providers = cv2.dnn.DNN_TARGET_CPU if device == 'cpu' else cv2.dnn.DNN_TARGET_CUDA

        self.session_det = cv2.dnn.readNetFromONNX(onnx_det)
        self.session_det.setPreferableBackend(backend)
        self.session_det.setPreferableTarget(providers)

        self.session_pose = cv2.dnn.readNetFromONNX(onnx_pose)
        self.session_pose.setPreferableBackend(backend)
        self.session_pose.setPreferableTarget(providers)
    
    def __call__(self, oriImg, include_hand = True, include_face = True) -> Optional[np.ndarray]:
        det_result = inference_detector(self.session_det, oriImg)
        if det_result is None:
            return None

        keypoints, scores = inference_pose(self.session_pose, det_result, oriImg)

        keypoints_info = np.concatenate(
            (keypoints, scores[..., None]), axis=-1)
        # compute neck joint
        neck = np.mean(keypoints_info[:, [5, 6]], axis=1)
        # neck score when visualizing pred
        neck[:, 2:4] = np.logical_and(
            keypoints_info[:, 5, 2:4] > 0.3,
            keypoints_info[:, 6, 2:4] > 0.3).astype(int)
        new_keypoints_info = np.insert(
            keypoints_info, 17, neck, axis=1)
        mmpose_idx = [
            17, 6, 8, 10, 7, 9, 12, 14, 16, 13, 15, 2, 1, 4, 3
        ]
        openpose_idx = [
            1, 2, 3, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17
        ]
        new_keypoints_info[:, openpose_idx] = \
            new_keypoints_info[:, mmpose_idx]
        keypoints_info = new_keypoints_info

        return keypoints_info

    @staticmethod
    def format_result(keypoints_info: Optional[np.ndarray], include_hand = True, include_face = True) -> List[PoseResult]:
        def format_keypoint_part(
            part: np.ndarray,
        ) -> Optional[List[Optional[Keypoint]]]:
            keypoints = [
                Keypoint(x, y, score, i) if score >= 0.3 else None
                for i, (x, y, score) in enumerate(part)
            ]
            return (
                None if all(keypoint is None for keypoint in keypoints) else keypoints
            )

        def total_score(keypoints: Optional[List[Optional[Keypoint]]]) -> float:
            return (
                sum(keypoint.score for keypoint in keypoints if keypoint is not None)
                if keypoints is not None
                else 0.0
            )

        pose_results = []
        sort_values = []

        if keypoints_info is None:
            return pose_results

        for instance in keypoints_info:
            body_keypoints = format_keypoint_part(instance[:18]) or ([None] * 18)
            left_hand = format_keypoint_part(instance[92:113]) if include_hand else None
            right_hand = format_keypoint_part(instance[113:134]) if include_hand else None
            face = format_keypoint_part(instance[24:92]) if include_face else None
            
            nkeypoints = [
                {
                    "x": keypoint.x,
                    "y": keypoint.y,
                } if keypoint is not None else None for keypoint in body_keypoints
            ]
            new_keypoints, d_neck_hip = adjust_keypoints(nkeypoints)

            # Openpose face consists of 70 points in total, while DWPose only
            # provides 68 points. Padding the last 2 points.
            if face is not None:
                # left eye
                face.append(body_keypoints[14])
                # right eye
                face.append(body_keypoints[15])

            body = BodyResult(
                [
                    Keypoint(
                        x=keypoint["x"],
                        y=keypoint["y"],
                    ) if keypoint is not None else None
                    for keypoint in new_keypoints
                ], total_score(body_keypoints), len(body_keypoints)
            )
            pose_results.append(PoseResult(body, left_hand, right_hand, face))
            sort_values.append(d_neck_hip)
        
        # Sort the results by the distance from neck to hip
        combined_list = list(zip(pose_results, sort_values))
        combined_list.sort(key=lambda x: x[1], reverse=True)
        sorted_results = [item[0] for item in combined_list]
        return sorted_results
