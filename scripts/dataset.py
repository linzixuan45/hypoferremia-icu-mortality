from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
import pandas as pd
import pickle
import os
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import numpy as np
from sklearn.neighbors import NearestNeighbors
from typing import Tuple, List, Optional, Union
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 常量定义
DEFAULT_K = 5
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42
DEFAULT_MAX_ITER = 5
AGE_MIN, AGE_MAX = 18, 100
LOS_ICU_MIN = 1
MISSING_THRESHOLD = 0.8
MIMIC3_THRESHOLD = 0.1

# 编码字典
RACE_DICT = {"white": 0, "black": 1, "asian": 2, "hispanic": 3, "other": 4}
GENDER_DICT = {"M": 0, "F": 1, "other": 2}

# 缺失特征列表
MIMIC3_MISSING_FEATURES = [
    "fio2_chartevents_mean",
    "pao2fio2ratio_mean",
    "icu_expire_flag",
]


def SMOTE(
    pd_X: pd.DataFrame, pd_y: pd.Series, N: int, k: int = DEFAULT_K
) -> Tuple[pd.DataFrame, pd.Series]:
    """
    合成少数类过采样技术（SMOTE）

    Args:
        pd_X: 包含数据点的特征矩阵
        pd_y: 对应的标签数组（多数类为0，少数类为1）
        N: 生成的合成样本数量
        k: 考虑的最近邻居数量，默认为5

    Returns:
        X_balanced: 包含生成样本的合成特征矩阵
        y_balanced: 合成样本对应的标签数组

    Raises:
        ValueError: 当少数类样本数量不足时
    """
    X = pd_X.values
    y = pd_y.values

    # 分离多数类和少数类样本
    X_majority = X[y == 0]
    X_minority = X[y == 1]

    if len(X_minority) == 0:
        raise ValueError("没有找到少数类样本")

    # 计算每个少数类样本需要生成的合成样本数量
    N_per_sample = max(1, N // len(X_minority))

    # 如果k大于少数样本数量，则将其减少到可能的最大值
    k = min(k, len(X_minority) - 1)
    if k < 1:
        k = 1

    # 初始化列表以存储合成样本和相应的标签
    synthetic_samples = []
    synthetic_labels = []

    # 在少数类样本上拟合k近邻
    knn = NearestNeighbors(n_neighbors=k)
    knn.fit(X_minority)

    for minority_sample in X_minority:
        # 查找当前少数类样本的k个最近邻居
        _, indices = knn.kneighbors(minority_sample.reshape(1, -1), n_neighbors=k)

        # 随机选择k个邻居并创建合成样本
        for _ in range(N_per_sample):
            neighbor_index = np.random.choice(indices[0])
            neighbor = X_minority[neighbor_index]

            # 计算当前少数类样本和邻居之间的差异
            difference = neighbor - minority_sample

            # 生成一个0到1之间的随机数
            alpha = np.random.random()

            # 创建一个合成样本作为少数类样本和邻居的线性组合
            synthetic_sample = minority_sample + alpha * difference

            # 将合成样本及其标签追加到列表中
            synthetic_samples.append(synthetic_sample)
            synthetic_labels.append(1)

    # 将列表转换为numpy数组
    X_synthetic = np.array(synthetic_samples)
    y_synthetic = np.array(synthetic_labels)

    # 将原始多数类样本与合成样本合并
    X_balanced = np.concatenate((X_majority, X_synthetic), axis=0)
    y_balanced = np.concatenate((np.zeros(len(X_majority)), y_synthetic), axis=0)

    X_balanced = pd.DataFrame(X_balanced, columns=pd_X.columns)
    y_balanced = pd.Series(y_balanced)

    return X_balanced, y_balanced


def encoder_race(select_pd: pd.DataFrame) -> pd.DataFrame:
    """
    对人种进行编码

    Args:
        select_pd: 需要处理的数据集

    Returns:
        处理后的数据集
    """

    def clean_race(x):
        """清理和标准化人种数据"""
        if pd.isna(x):
            return "other"
        x_str = str(x).lower().strip()
        # 处理包含 "-" 或 "/" 的情况
        for separator in ["-", "/"]:
            if separator in x_str:
                x_str = x_str.split(separator)[0].strip()
        return x_str

    select_pd = select_pd.copy()
    select_pd["race"] = select_pd["race"].apply(clean_race)
    select_pd["race"] = select_pd["race"].apply(lambda x: RACE_DICT.get(x, 4))

    return select_pd


def encoder_gender(select_pd: pd.DataFrame) -> pd.DataFrame:
    """
    对性别进行编码

    Args:
        select_pd: 需要处理的数据集

    Returns:
        处理后的数据集
    """
    select_pd = select_pd.copy()
    select_pd["gender"] = select_pd["gender"].apply(lambda x: GENDER_DICT.get(x, 2))
    return select_pd


class DATASET:
    """数据集处理类"""

    def __init__(self, config):
        self.task_name = config.task_name
        self.data_path = config.data_path
        self.model_weight_dir = config.model_save_dir
        self.first_features: List[str] = []
        self.scaler: Optional[StandardScaler] = None
        self.stand_encoder_path = (
            Path(self.model_weight_dir) / "stand_encoder.pkl"
        )  # 修改为Path对象

        # 尝试加载已有的标准化器
        self._load_scaler()

    def _load_scaler(self) -> None:
        """加载已有的标准化器"""
        try:
            if self.stand_encoder_path.exists():
                with open(self.stand_encoder_path, "rb") as f:
                    self.scaler = pickle.load(f)
                    logger.info("成功加载已有的标准化器")
        except Exception as e:
            logger.warning(f"加载标准化器失败: {e}")
            self.scaler = None

    def _save_scaler(self, scaler: StandardScaler) -> None:
        """保存标准化器"""
        try:
            with open(self.stand_encoder_path, "wb") as f:
                pickle.dump(scaler, f)
            self.scaler = scaler
            logger.info("标准化器保存成功")
        except Exception as e:
            logger.error(f"保存标准化器失败: {e}")

    def _impute_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """使用多重插补填充缺失值"""
        try:
            imputer = IterativeImputer(
                max_iter=DEFAULT_MAX_ITER, random_state=DEFAULT_RANDOM_STATE
            )
            imputed_data = imputer.fit_transform(df)
            return pd.DataFrame(imputed_data, columns=df.columns)
        except Exception as e:
            logger.error(f"多重插补失败: {e}")
            raise

    def refresh_encode_and_data(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
        """
        刷新编码和数据

        Returns:
            X: 特征矩阵
            X_scaled: 标准化后的特征矩阵
            Y: 标签
        """
        if "hospital_expire_flag" not in df.columns:
            raise ValueError("数据集中缺少 'hospital_expire_flag' 列")

        # 填充缺失值
        model_data = self._impute_missing_values(df)

        # 分离特征和标签
        X = model_data.drop("hospital_expire_flag", axis=1)
        Y = model_data["hospital_expire_flag"]

        # 标准化特征
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=X.columns)

        # 保存标准化器
        self._save_scaler(scaler)

        return X, X_scaled, Y

    def encoder_data(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
        """编码数据"""
        if self.scaler is not None:
            return self.using_weight2encode(df)
        else:
            return self.refresh_encode_and_data(df)

    def using_weight2encode(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series]:
        """
        使用已有的编码器进行编码

        Returns:
            X: 特征矩阵
            X_scaled: 标准化后的特征矩阵
            Y: 标签
        """
        if self.scaler is None:
            raise ValueError("没有可用的标准化器，请先调用 refresh_encode_and_data")

        if "hospital_expire_flag" not in df.columns:
            raise ValueError("数据集中缺少 'hospital_expire_flag' 列")

        try:
            # 防止传入的数据，存在多个列
            stander_feature_ls = self.scaler.__dict__["feature_names_in_"].tolist()
            if "hospital_expire_flag" not in stander_feature_ls:
                stander_feature_ls.append("hospital_expire_flag")
            model_data = df[stander_feature_ls]
            # 填充缺失值
            model_data = self._impute_missing_values(model_data)

        except KeyError as e:
            print(f"KeyError: {e}")
            print("请检查输入数据的列名是否与标准化器，训练时一致")

        # 分离特征和标签
        X = model_data.drop("hospital_expire_flag", axis=1)
        Y = model_data["hospital_expire_flag"]

        # 标准化特征
        X_scaled = self.scaler.transform(X)

        X_scaled = pd.DataFrame(X_scaled, columns=X.columns)

        return X, X_scaled, Y

    def inverse_transform_X(self, X_scaled: pd.DataFrame) -> pd.DataFrame:
        """对标准化后的特征矩阵进行还原"""
        if self.scaler is None:
            raise ValueError("没有可用的标准化器")

        # 获取标准化器在训练时使用的特征名称
        original_feature_names = getattr(self.scaler, "feature_names_in_", None)

        # 找出 X_scaled 中存在于原始特征中的列
        if original_feature_names is not None:
            valid_columns = [
                col for col in X_scaled.columns if col in original_feature_names
            ]
            valid_X_scaled = X_scaled[valid_columns]
        else:
            valid_columns = X_scaled.columns
            valid_X_scaled = X_scaled

        # 对有效的特征进行逆变换
        X_original = self.scaler.inverse_transform(valid_X_scaled)
        return pd.DataFrame(X_original, columns=valid_columns)

    def train_test_split(
        self,
        X: pd.DataFrame,
        Y: pd.Series,
        test_size: float = DEFAULT_TEST_SIZE,
        random_state: int = DEFAULT_RANDOM_STATE,
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """划分训练集和测试集"""
        X_train, X_test, Y_train, Y_test = train_test_split(
            X, Y, test_size=test_size, random_state=random_state, stratify=Y
        )

        logger.info(f"训练集大小: {X_train.shape}")
        logger.info(f"测试集大小: {X_test.shape}")
        logger.info(f"训练集标签分布: {Y_train.value_counts().to_dict()}")
        logger.info(f"测试集标签分布: {Y_test.value_counts().to_dict()}")

        return X_train, X_test, Y_train, Y_test

    def data_preprocess(
        self,
        select_feature: Optional[List[str]] = None,
        downsample_ratio: float = 0.0,
        use_handle_select: bool = False,
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """数据预处理"""
        try:
            # 读取数据
            select_name = f"select_{self.task_name.split('_')[1]}"

            mimic4 = pd.read_excel(
                self.data_path, sheet_name=f"mimic4_{self.task_name}"
            )
            mimic3 = pd.read_excel(
                self.data_path, sheet_name=f"mimic3_{self.task_name}"
            )
            feature_sheet = pd.read_excel(self.data_path, sheet_name="Feature_names")[
                :132
            ]

            # 数据清洗
            mimic4 = self._clean_dataset(mimic4, MISSING_THRESHOLD)
            mimic3 = self._clean_dataset(mimic3, MIMIC3_THRESHOLD)

            # 特征选择
            select_feature = self._select_features(
                mimic4,
                mimic3,
                feature_sheet,
                select_name,
                select_feature,
                use_handle_select,
            )

            # 应用特征选择
            mimic4 = mimic4[select_feature]
            mimic3 = mimic3[select_feature]

            # 数据预处理
            mimic4, mimic3 = self._apply_preprocessing(mimic4, mimic3, select_feature)

            # 下采样
            if downsample_ratio != 0:
                mimic4 = self.downsample_data(
                    mimic4, flag_value=1, ratio=downsample_ratio
                )
                mimic3 = self.downsample_data(
                    mimic3, flag_value=1, ratio=downsample_ratio
                )

            return mimic4, mimic3

        except Exception as e:
            logger.error(f"数据预处理失败: {e}")
            raise

    def downsample_data(
        self, data: pd.DataFrame, flag_value: int = 1, ratio: float = 1.0
    ) -> pd.DataFrame:
        """
        从数据集中采样，保持正负样本数量平衡

        Args:
            data: 数据集
            flag_value: hospital_expire_flag 的值
            ratio: 正负样本的比例

        Returns:
            采样后的数据集
        """
        if "hospital_expire_flag" not in data.columns:
            raise ValueError("数据集中缺少 'hospital_expire_flag' 列")

        # 真值样本
        true_data = data[data["hospital_expire_flag"] == flag_value]
        length_true = len(true_data)

        # 假值样本
        false_data = data[data["hospital_expire_flag"] != flag_value]
        length_false = len(false_data)

        logger.info(f"正样本数量: {length_true}, 负样本数量: {length_false}")

        # 保持真假样本数量一致
        sample_num = int(min(length_true, length_false) * ratio)

        if length_true > length_false:
            sampled_data = pd.concat(
                [
                    true_data.sample(n=sample_num, random_state=DEFAULT_RANDOM_STATE),
                    false_data,
                ]
            )
        else:
            sampled_data = pd.concat(
                [
                    true_data,
                    false_data.sample(n=sample_num, random_state=DEFAULT_RANDOM_STATE),
                ]
            )

        return sampled_data

    def _clean_dataset(self, df: pd.DataFrame, threshold: float) -> pd.DataFrame:
        """清理数据集，去除缺失值过多的列"""
        return df.dropna(thresh=df.shape[0] * threshold, axis=1)

    def _select_features(
        self,
        mimic4: pd.DataFrame,
        mimic3: pd.DataFrame,
        feature_sheet: pd.DataFrame,
        select_name: str,
        select_feature: Optional[List[str]],
        use_handle_select: bool,
    ) -> List[str]:
        """特征选择逻辑"""
        mimic4_features = set(mimic4.columns)
        mimic3_features = set(mimic3.columns) - set(MIMIC3_MISSING_FEATURES)

        if select_feature is not None:
            # 使用指定的特征
            select_feature = (
                set(mimic3_features) & set(mimic4_features) & set(select_feature)
            )
        elif use_handle_select:
            # 使用处理选择的特征
            handle_features = feature_sheet[feature_sheet[select_name].isnull()][
                "subject_id"
            ].tolist()
            handle_features.extend(["race", "gender", "los_icu"])
            if "sofa_score" in handle_features:
                handle_features.remove("sofa_score")
            select_feature = (
                set(handle_features) & set(mimic3_features) & set(mimic4_features)
            )
        else:
            # 使用交集特征
            select_feature = set(mimic3_features) & set(mimic4_features)
            self.first_features = list(select_feature)

        select_feature = list(select_feature)
        logger.info(f"选择的特征数量: {len(select_feature)}")

        # 保存初筛的特征
        result_dir = Path("result")
        result_dir.mkdir(exist_ok=True)
        pd.DataFrame(select_feature).to_csv(
            result_dir / f"first_select_feature_{self.task_name}.csv", index=False
        )

        return select_feature

    def _apply_preprocessing(
        self, mimic4: pd.DataFrame, mimic3: pd.DataFrame, select_feature: List[str]
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """应用数据预处理步骤"""
        # 年龄限制
        if "admission_age" in select_feature:
            mimic4["admission_age"] = mimic4["admission_age"].clip(AGE_MIN, AGE_MAX)
            mimic3["admission_age"] = mimic3["admission_age"].clip(AGE_MIN, AGE_MAX)

        # 编码处理
        if "race" in select_feature:
            mimic4 = encoder_race(mimic4)
            mimic3 = encoder_race(mimic3)

        if "gender" in select_feature:
            mimic4 = encoder_gender(mimic4)
            mimic3 = encoder_gender(mimic3)

        # ICU住院时长限制
        if "los_icu" in select_feature:
            mimic4 = mimic4[mimic4["los_icu"] >= LOS_ICU_MIN]
            mimic3 = mimic3[mimic3["los_icu"] >= LOS_ICU_MIN]

        return mimic4, mimic3
