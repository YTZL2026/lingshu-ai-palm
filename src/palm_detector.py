# -*- coding: utf-8 -*-
"""
AI掌纹溯源 — 手掌检测与ROI提取模块
基于 MediaPipe Hands + OpenCV，实现手机拍照场景下的手掌检测与标准化
专利保护点：移动端掌纹图像标准化采集引导方法
"""
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode
from dataclasses import dataclass
from typing import Optional, Tuple, List
import math
import os

# ======================== MediaPipe 模型路径 ========================
MODEL_DIR = os.path.join(os.path.expanduser('~'), '.mediapipe_models')
MODEL_PATH = os.path.join(MODEL_DIR, 'hand_landmarker.task')


@dataclass
class HandDetectionResult:
    """手掌检测结果"""
    detected: bool                    # 是否检测到手掌
    handedness: str                   # 'Left' / 'Right'
    landmarks: Optional[np.ndarray]   # 21个关键点坐标 (21, 3) x,y,z
    confidence: float                 # 检测置信度
    quality_score: float              # 拍摄质量评分 0-100
    guidance_text: str                # 引导提示文字
    palm_roi: Optional[np.ndarray]    # 掌纹ROI区域（256x256）
    wrist_angle: float                # 手腕角度
    bounding_box: Tuple[int,int,int,int]  # (x, y, w, h)


class PalmDetector:
    """手掌检测器：定位手掌、质量评估、ROI提取"""

    # 21个关键点索引（MediaPipe Hand Landmarks）
    WRIST = 0
    THUMB_CMC = 1; THUMB_MCP = 2; THUMB_IP = 3; THUMB_TIP = 4
    INDEX_MCP = 5; INDEX_PIP = 6; INDEX_DIP = 7; INDEX_TIP = 8
    MIDDLE_MCP = 9; MIDDLE_PIP = 10; MIDDLE_DIP = 11; MIDDLE_TIP = 12
    RING_MCP = 13; RING_PIP = 14; RING_DIP = 15; RING_TIP = 16
    PINKY_MCP = 17; PINKY_PIP = 18; PINKY_DIP = 19; PINKY_TIP = 20

    # 掌纹ROI的关键点索引
    PALM_POINTS = [0, 1, 5, 9, 13, 17]  # 手腕 + 拇指根 + 四指根部

    def __init__(self, min_confidence=0.7, roi_size=256):
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=min_confidence,
            min_tracking_confidence=0.5
        )
        self.landmarker = HandLandmarker.create_from_options(options)
        self.roi_size = roi_size

    def detect(self, image: np.ndarray) -> HandDetectionResult:
        """
        检测图像中的手掌

        Args:
            image: BGR格式图像 (H, W, 3)

        Returns:
            HandDetectionResult 包含检测结果和ROI
        """
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w = image.shape[:2]
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self.landmarker.detect(mp_image)

        if not result.hand_landmarks:
            return HandDetectionResult(
                detected=False, handedness='', landmarks=None,
                confidence=0.0, quality_score=0.0,
                guidance_text='未检测到手掌，请将手掌平放在框内',
                palm_roi=None, wrist_angle=0.0,
                bounding_box=(0, 0, 0, 0)
            )

        # 获取第一个检测到的手
        hand_landmarks = result.hand_landmarks[0]
        handedness = result.handedness[0][0].category_name
        confidence = result.handedness[0][0].score

        # 提取坐标
        landmarks = np.array([[lm.x * w, lm.y * h, lm.z] for lm in hand_landmarks])

        # 计算外接矩形
        x_min = int(landmarks[:, 0].min())
        x_max = int(landmarks[:, 0].max())
        y_min = int(landmarks[:, 1].min())
        y_max = int(landmarks[:, 1].max())
        bbox = (x_min, y_min, x_max - x_min, y_max - y_min)

        # 质量评估
        quality, guidance = self._assess_quality(landmarks, (w, h))

        # 手腕角度计算
        wrist_angle = self._calc_wrist_angle(landmarks)

        # ROI提取
        roi = self._extract_roi(image, landmarks, (w, h))

        return HandDetectionResult(
            detected=True, handedness=handedness,
            landmarks=landmarks, confidence=confidence,
            quality_score=quality, guidance_text=guidance,
            palm_roi=roi, wrist_angle=wrist_angle,
            bounding_box=bbox
        )

    def _assess_quality(self, landmarks: np.ndarray, img_size: Tuple[int, int]) -> Tuple[float, str]:
        """
        评估拍照质量（专利：标准化采集引导）

        检查项：
        1. 手掌是否在画面中心
        2. 手掌大小是否合适（占画面 30-60%）
        3. 手指是否张开（利于掌纹识别）
        4. 手掌是否平放（掌心朝上/朝前）

        Returns:
            (quality_score 0-100, guidance_text)
        """
        w, h = img_size
        quality = 100.0
        tips = []

        # 1. 中心度
        palm_center = landmarks[self.PALM_POINTS].mean(axis=0)[:2]
        offset_x = abs(palm_center[0] - w/2) / (w/2)
        offset_y = abs(palm_center[1] - h/2) / (h/2)
        center_score = 100 - (offset_x + offset_y) * 50
        if center_score < 70:
            tips.append('请将手掌移到画面中央')
            quality -= 15

        # 2. 大小合适度
        x_range = landmarks[:, 0].max() - landmarks[:, 0].min()
        y_range = landmarks[:, 1].max() - landmarks[:, 1].min()
        area_ratio = (x_range * y_range) / (w * h)
        if area_ratio < 0.15:
            tips.append('手掌太小，请靠近一些')
            quality -= 20
        elif area_ratio > 0.6:
            tips.append('手掌太近，请离远一些')
            quality -= 20

        # 3. 手指张开度
        finger_tips = landmarks[[4, 8, 12, 16, 20]]
        finger_bases = landmarks[[2, 5, 9, 13, 17]]
        spread_dist = np.linalg.norm(finger_tips.std(axis=0))
        if spread_dist < 30:
            tips.append('请自然张开手指')
            quality -= 10

        # 4. 手腕角度（偏离水平太多说明手掌没放正）
        wrist_angle = abs(self._calc_wrist_angle(landmarks))
        if wrist_angle > 30:
            tips.append('请将手掌放正')
            quality -= 15

        guidance = '；'.join(tips) if tips else '✅ 拍摄质量良好'
        return max(0, quality), guidance

    def _calc_wrist_angle(self, landmarks: np.ndarray) -> float:
        """计算手腕相对于水平的角度"""
        wrist = landmarks[self.WRIST]
        middle_mcp = landmarks[self.MIDDLE_MCP]
        dx = middle_mcp[0] - wrist[0]
        dy = middle_mcp[1] - wrist[1]
        return math.degrees(math.atan2(dy, dx)) - 90

    def _extract_roi(self, image: np.ndarray, landmarks: np.ndarray, img_size: Tuple[int, int]) -> np.ndarray:
        """
        提取掌纹ROI区域

        利用 MediaPipe 关键点定位掌心区域，包含：
        - 大鱼际（thenar）：拇指根部
        - 小鱼际（hypothenar）：小指侧
        - 掌心（center palm）：中央凹陷
        - 三大主线覆盖区域

        Args:
            image: BGR原始图像
            landmarks: 21个关键点坐标
            img_size: (width, height)

        Returns:
            256x256 标准化掌纹ROI
        """
        h, w = image.shape[:2]

        # 以掌心为中心，用中指MCP到手腕距离作为缩放参考
        middle_mcp = landmarks[self.MIDDLE_MCP][:2]
        wrist = landmarks[self.WRIST][:2]
        palm_height = np.linalg.norm(middle_mcp - wrist)

        # 掌心中心 = 食指MCP + 小指MCP 中点，向下偏移到手腕方向
        index_mcp = landmarks[self.INDEX_MCP][:2]
        pinky_mcp = landmarks[self.PINKY_MCP][:2]
        palm_center_x = (index_mcp[0] + pinky_mcp[0]) / 2
        palm_center_y = (index_mcp[1] + pinky_mcp[1]) / 2 + palm_height * 0.1

        # ROI 边长 = palm_height * 1.2（覆盖大鱼际+小鱼际）
        roi_side = int(palm_height * 1.2)

        # 裁剪正方形区域
        half = roi_side // 2
        cx, cy = int(palm_center_x), int(palm_center_y)

        # 边界处理
        x1 = max(0, cx - half)
        y1 = max(0, cy - half)
        x2 = min(w, cx + half)
        y2 = min(h, cy + half)

        roi = image[y1:y2, x1:x2].copy()

        # 标准化到 256x256
        roi = cv2.resize(roi, (self.roi_size, self.roi_size), interpolation=cv2.INTER_LANCZOS4)

        # 光照归一化（CLAHE）
        lab = cv2.cvtColor(roi, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        lab = cv2.merge([l, a, b])
        roi = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

        return roi

    def draw_landmarks(self, image: np.ndarray, result: HandDetectionResult) -> np.ndarray:
        """在图像上绘制关键点和引导框"""
        vis = image.copy()
        if result.detected and result.landmarks is not None:
            # 绘制ROI区域框
            h, w = image.shape[:2]
            landmarks = result.landmarks

            palm_center_x = int((landmarks[self.INDEX_MCP][0] + landmarks[self.PINKY_MCP][0]) / 2)
            palm_center_y = int((landmarks[self.INDEX_MCP][1] + landmarks[self.PINKY_MCP][1]) / 2)
            palm_height = int(np.linalg.norm(landmarks[self.MIDDLE_MCP][:2] - landmarks[self.WRIST][:2]))
            half = int(palm_height * 1.2 / 2)

            # 绿色ROI引导框
            cv2.rectangle(vis,
                         (palm_center_x - half, palm_center_y - half),
                         (palm_center_x + half, palm_center_y + half),
                         (0, 255, 0), 2)

            # 手掌中心十字
            cv2.drawMarker(vis, (palm_center_x, palm_center_y),
                          (0, 255, 0), cv2.MARKER_CROSS, 20, 2)

        return vis

    def close(self):
        self.landmarker.close()


# ======================== 测试代码 ========================
if __name__ == '__main__':
    import sys

    detector = PalmDetector()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        img = cv2.imread(path)
        if img is None:
            print(f'❌ 无法读取图片: {path}')
            sys.exit(1)

        result = detector.detect(img)
        print(f'检测: {result.detected}')
        print(f'手别: {result.handedness}')
        print(f'置信度: {result.confidence:.2f}')
        print(f'质量评分: {result.quality_score:.0f}/100')
        print(f'引导: {result.guidance_text}')
        print(f'手腕角度: {result.wrist_angle:.1f}°')
        print(f'ROI尺寸: {result.palm_roi.shape if result.palm_roi is not None else "N/A"}')

        if result.palm_roi is not None:
            vis = detector.draw_landmarks(img, result)
            cv2.imwrite('debug_detect.jpg', vis)
            cv2.imwrite('debug_roi.jpg', result.palm_roi)
            print('📷 调试图片已保存: debug_detect.jpg / debug_roi.jpg')
    else:
        print('用法: python palm_detector.py <手掌照片路径>')

    detector.close()
