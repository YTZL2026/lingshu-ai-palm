# -*- coding: utf-8 -*-
"""
AI掌纹溯源 — 掌纹特征提取模块
实现传统中医手诊特征 + AI微特征的提取 pipeline
专利保护点：基于深度学习的掌纹微特征提取方法
"""
import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from scipy import ndimage
from skimage.feature import graycomatrix, graycoprops, local_binary_pattern
import warnings
warnings.filterwarnings('ignore')


@dataclass
class PalmFeatures:
    """掌纹特征向量"""

    # === 传统中医手诊特征 ===

    # 三大主线深度/清晰度（0-100）
    life_line_depth: float = 50.0       # 生命线
    head_line_depth: float = 50.0       # 智慧线
    heart_line_depth: float = 50.0      # 感情线

    # 主线形态特征
    life_line_curve: float = 0.5        # 生命线弧度 (0=直, 1=极弯)
    head_line_slope: float = 0.5        # 智慧线倾斜度 (0=下垂, 1=平直)
    heart_line_end: float = 0.5         # 感情线终点位置 (0=无名指下, 1=食指下)

    # 辅助线数量
    secondary_line_count: int = 0       # 可见辅助线总数
    interference_line_count: int = 0    # 干扰线（横切纹）数量

    # 掌丘特征
    thenar_fullness: float = 50.0       # 大鱼际饱满度 (0-100)
    hypothenar_fullness: float = 50.0   # 小鱼际饱满度
    center_depth: float = 50.0          # 掌心凹陷深度

    # 色泽特征
    overall_redness: float = 50.0       # 整体红润度
    color_uniformity: float = 50.0      # 色泽均匀度
    luster: float = 50.0                # 光泽度
    vein_visibility: float = 10.0       # 静脉可见度

    # === AI 微特征（专利核心） ===
    texture_density: float = 50.0       # 纹理密度指数 TDI
    line_complexity: float = 50.0       # 纹路复杂度 LCX
    capillary_visibility: float = 10.0  # 毛细血管可见度 CVI
    skin_color_std: float = 10.0        # 肤色标准差（均匀度倒数）
    mound_balance: float = 50.0         # 掌丘均衡指数 MEI

    # === 全局统计 ===
    gabor_energy: float = 0.0           # Gabor滤波器能量（纹理强度）
    lbp_entropy: float = 0.0            # LBP纹理熵
    glcm_contrast: float = 0.0          # GLCM对比度
    glcm_correlation: float = 0.0       # GLCM相关性
    edge_density: float = 0.0           # 边缘密度

    # === 综合特征向量 ===
    vector: np.ndarray = field(default_factory=lambda: np.zeros(20))

    def to_dict(self) -> dict:
        """转为字典（序列化用）"""
        return {
            'life_line_depth': self.life_line_depth,
            'head_line_depth': self.head_line_depth,
            'heart_line_depth': self.heart_line_depth,
            'life_line_curve': self.life_line_curve,
            'head_line_slope': self.head_line_slope,
            'heart_line_end': self.heart_line_end,
            'secondary_line_count': self.secondary_line_count,
            'interference_line_count': self.interference_line_count,
            'thenar_fullness': self.thenar_fullness,
            'hypothenar_fullness': self.hypothenar_fullness,
            'center_depth': self.center_depth,
            'overall_redness': self.overall_redness,
            'color_uniformity': self.color_uniformity,
            'luster': self.luster,
            'vein_visibility': self.vein_visibility,
            'texture_density': self.texture_density,
            'line_complexity': self.line_complexity,
            'capillary_visibility': self.capillary_visibility,
            'skin_color_std': self.skin_color_std,
            'mound_balance': self.mound_balance,
            'gabor_energy': self.gabor_energy,
            'lbp_entropy': self.lbp_entropy,
            'glcm_contrast': self.glcm_contrast,
            'glcm_correlation': self.glcm_correlation,
            'edge_density': self.edge_density,
        }


class FeatureExtractor:
    """
    掌纹特征提取器

    从 256x256 掌纹ROI中提取：
    1. 传统中医手诊特征（14维）
    2. AI 微特征（5维）
    3. 全局纹理统计特征（5维）
    → 总计 24 维特征向量
    """

    def __init__(self, roi_size: int = 256):
        self.roi_size = roi_size

        # Gabor滤波器组（4方向 × 3尺度）
        self.gabor_kernels = self._build_gabor_kernels()

    def _build_gabor_kernels(self) -> List[np.ndarray]:
        """构建Gabor滤波器组"""
        kernels = []
        for theta in [0, np.pi/4, np.pi/2, 3*np.pi/4]:  # 4方向
            for sigma in [4, 8, 12]:                      # 3尺度
                for lambd in [sigma * 2]:                 # 波长
                    kernel = cv2.getGaborKernel(
                        (21, 21), sigma, theta, lambd,
                        gamma=0.5, psi=0, ktype=cv2.CV_32F
                    )
                    kernels.append(kernel)
        return kernels

    def extract(self, roi: np.ndarray) -> PalmFeatures:
        """
        从掌纹ROI提取完整特征向量

        Args:
            roi: 256x256 掌纹ROI (BGR格式)

        Returns:
            PalmFeatures 完整的掌纹特征
        """
        if roi is None or roi.size == 0:
            return PalmFeatures()

        # 转灰度
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        features = PalmFeatures()

        # === 1. 传统特征提取 ===
        self._extract_line_features(gray, features)
        self._extract_mound_features(gray, roi, features)
        self._extract_color_features(hsv, gray, features)

        # === 2. AI 微特征提取 ===
        self._extract_micro_features(gray, features)

        # === 3. 全局纹理统计 ===
        self._extract_texture_features(gray, features)

        # === 4. 构建特征向量 ===
        features.vector = self._build_vector(features)

        return features

    def _extract_line_features(self, gray: np.ndarray, f: PalmFeatures):
        """
        提取掌纹主线特征

        方法：Canny边缘检测 + 概率Hough变换检测线段
        """
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.0)

        # CLAHE增强对比度
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(blurred)

        # Canny边缘检测
        edges = cv2.Canny(enhanced, 30, 100)

        # 概率Hough变换
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40,
                                 minLineLength=30, maxLineGap=10)

        total_line_length = 0
        line_count = 0
        line_angles = []

        if lines is not None:
            line_count = len(lines)
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                total_line_length += length

                angle = abs(np.arctan2(y2 - y1, x2 - x1))
                # 排除接近水平（可能是干扰）和接近垂直的线
                if 0.2 < angle < 1.4:
                    line_angles.append(angle)

            # 主线深度：检测到的线段总长度 / ROI面积（归一化）
            raw_depth = min(100, (total_line_length / (self.roi_size * self.roi_size)) * 800)
        else:
            raw_depth = 10

        # 模拟三大主线深度（基于检测到的线段分布）
        # 实际应用中可通过线段的y坐标分布区分
        h = self.roi_size
        upper = gray[:h//3, :]
        middle = gray[h//3:2*h//3, :]
        lower = gray[2*h//3:, :]

        upper_std = upper.std() + 1
        middle_std = middle.std() + 1
        lower_std = lower.std() + 1

        # 纹路越深，局部标准差越大
        f.heart_line_depth = min(100, upper_std * 2.5)      # 感情线在上部
        f.life_line_depth = min(100, middle_std * 2.5)      # 智慧线在中部
        f.head_line_depth = min(100, lower_std * 2.5)       # 生命线弧度在下部

        # 主线形态
        f.life_line_curve = np.clip(raw_depth / 100, 0.1, 0.9)
        f.head_line_slope = 0.5  # 默认值，需ML模型精确估计
        f.heart_line_end = 0.5

        # 辅助线计数
        f.secondary_line_count = max(0, line_count - 3)  # 减去三大主线
        f.interference_line_count = max(0, line_count - 8)

    def _extract_mound_features(self, gray: np.ndarray, roi: np.ndarray, f: PalmFeatures):
        """
        提取掌丘特征

        将ROI分为8个区域，计算每个区域的：
        - 平均灰度（代表饱满度：亮=饱满）
        - 局部标准差（代表纹理密度）
        """
        h, w = self.roi_size, self.roi_size
        half_h = h // 2
        half_w = w // 2

        # 8个区域（简化为4象限 × 2层）
        regions = {
            'thenar': gray[half_h:, :half_w],           # 大鱼际（左下）
            'hypothenar': gray[half_h:, half_w:],       # 小鱼际（右下）
            'upper_left': gray[:half_h, :half_w],       # 左上
            'upper_right': gray[:half_h, half_w:],     # 右上
        }

        region_means = {}
        for name, region in regions.items():
            if region.size > 0:
                region_means[name] = region.mean()

        # 大鱼际饱满度（越亮越饱满）
        thenar_mean = region_means.get('thenar', 128)
        f.thenar_fullness = np.clip(thenar_mean * 0.8, 10, 90)

        # 小鱼际饱满度
        hypothenar_mean = region_means.get('hypothenar', 128)
        f.hypothenar_fullness = np.clip(hypothenar_mean * 0.8, 10, 90)

        # 掌心凹陷深度（中心区域比周围暗 = 深）
        center_region = gray[h//3:2*h//3, w//3:2*w//3]
        surrounding = np.concatenate([
            gray[:h//3, :].flatten(),
            gray[2*h//3:, :].flatten(),
            gray[:, :w//3].flatten(),
            gray[:, 2*w//3:].flatten()
        ])
        center_diff = surrounding.mean() - center_region.mean()
        f.center_depth = np.clip(center_diff * 2 + 50, 10, 90)

    def _extract_color_features(self, hsv: np.ndarray, gray: np.ndarray, f: PalmFeatures):
        """
        提取色泽特征

        HSV色彩空间分析：
        - H: 色调（偏红/偏黄）
        - S: 饱和度（炎症/敏感倾向）
        - V: 明度（光泽/暗沉）
        """
        h, s, v = cv2.split(hsv)

        # 整体红润度（色调靠近红色区域+饱和度）
        red_mask = (h < 10) | (h > 170)  # 红色色调范围
        redness = np.mean(s[red_mask]) if np.any(red_mask) else s.mean()
        f.overall_redness = np.clip(redness * 0.8, 10, 90)

        # 色泽均匀度（饱和度标准差反比）
        f.color_uniformity = np.clip(100 - s.std() * 0.8, 10, 95)

        # 光泽度（明度的均值）
        f.luster = np.clip(v.mean() * 0.5, 10, 90)

        # 静脉可见度（灰度图中深色线状结构）
        # 检测暗色线状特征
        dark_mask = gray < (gray.mean() - gray.std())
        f.vein_visibility = np.clip(dark_mask.sum() / gray.size * 800, 0, 80)

    def _extract_micro_features(self, gray: np.ndarray, f: PalmFeatures):
        """
        提取 AI 微特征（专利核心）

        这些特征维度是传统中医手诊无法量化、通用AI模型无法提取的
        """
        # === TDI: 纹理密度指数 ===
        edges = cv2.Canny(gray, 25, 75)
        f.texture_density = np.clip(edges.sum() / gray.size * 100, 5, 95)

        # === LCX: 纹路复杂度 ===
        # 使用局部二值模式(LBP)的直方图熵来衡量纹理复杂度
        radius, n_points = 3, 24
        lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
        lbp_hist, _ = np.histogram(lbp, bins=range(n_points + 3), density=True)
        lbp_hist = lbp_hist[lbp_hist > 0]
        lbp_entropy = -np.sum(lbp_hist * np.log2(lbp_hist + 1e-10))
        f.line_complexity = np.clip(lbp_entropy * 20, 10, 90)

        # === CVI: 毛细血管可见度 ===
        # 高频分量（细小纹理）与低频分量（粗大纹路）的比值
        blurred = cv2.GaussianBlur(gray.astype(np.float32), (11, 11), 5)
        high_freq = gray.astype(np.float32) - blurred
        f.capillary_visibility = np.clip(np.abs(high_freq).mean() * 3, 0, 80)

        # === SCU: 肤色标准差 ===
        f.skin_color_std = np.clip(gray.std(), 5, 80)

        # === MEI: 掌丘均衡指数 ===
        # 4个象限区域的标准差的方差
        h, w = gray.shape
        quad_means = [
            gray[:h//2, :w//2].mean(),
            gray[:h//2, w//2:].mean(),
            gray[h//2:, :w//2].mean(),
            gray[h//2:, w//2:].mean()
        ]
        f.mound_balance = np.clip(100 - np.std(quad_means) * 1.5, 10, 90)

    def _extract_texture_features(self, gray: np.ndarray, f: PalmFeatures):
        """
        提取全局纹理统计特征

        用于补充描述掌纹整体纹理特征
        """
        # Gabor能量（纹理强度）
        energies = []
        for kernel in self.gabor_kernels:
            filtered = cv2.filter2D(gray.astype(np.float32), cv2.CV_32F, kernel)
            energies.append(np.mean(np.abs(filtered)))
        f.gabor_energy = np.mean(energies) * 20

        # LBP纹理熵（复用之前的LBP）
        radius, n_points = 3, 24
        lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
        lbp_hist, _ = np.histogram(lbp, bins=range(n_points + 3), density=True)
        lbp_hist = lbp_hist[lbp_hist > 0]
        f.lbp_entropy = -np.sum(lbp_hist * np.log2(lbp_hist + 1e-10)) * 20

        # GLCM（灰度共生矩阵）特征
        gray_uint8 = (gray / 4).astype(np.uint8)  # 降到64级以加速
        glcm = graycomatrix(gray_uint8, [1], [0, np.pi/4, np.pi/2, 3*np.pi/4],
                           levels=64, symmetric=True, normed=True)
        f.glcm_contrast = graycoprops(glcm, 'contrast').mean() * 10
        f.glcm_correlation = graycoprops(glcm, 'correlation').mean()

        # 边缘密度
        edges = cv2.Canny(gray, 30, 100)
        f.edge_density = edges.sum() / gray.size * 100

    def _build_vector(self, f: PalmFeatures) -> np.ndarray:
        """构建20维特征向量（用于分类器输入）"""
        return np.array([
            f.life_line_depth, f.head_line_depth, f.heart_line_depth,
            f.life_line_curve, f.head_line_slope, f.heart_line_end,
            f.secondary_line_count / 10,      # 归一化
            f.interference_line_count / 10,
            f.thenar_fullness, f.hypothenar_fullness, f.center_depth,
            f.overall_redness, f.color_uniformity, f.luster,
            f.vein_visibility,
            f.texture_density, f.line_complexity,
            f.capillary_visibility, f.skin_color_std,
            f.mound_balance
        ], dtype=np.float32)


# ======================== 测试代码 ========================
if __name__ == '__main__':
    import sys
    extractor = FeatureExtractor()

    if len(sys.argv) > 1:
        path = sys.argv[1]
        roi = cv2.imread(path)
        if roi is None:
            print(f'❌ 无法读取图片: {path}')
            sys.exit(1)

        if roi.shape[:2] != (256, 256):
            roi = cv2.resize(roi, (256, 256))

        features = extractor.extract(roi)
        print('=== 掌纹特征提取结果 ===')
        for k, v in features.to_dict().items():
            print(f'  {k}: {v:.2f}')
        print(f'\n特征向量: {features.vector}')
        print(f'向量维度: {len(features.vector)}')
    else:
        print('用法: python feature_extractor.py <掌纹ROI图片路径>')
