"""Tính nhu cầu năng lượng (BMR, TDEE), mục tiêu calo, macro và phân bổ theo bữa.

BMR theo Mifflin-St Jeor (1990):
    nam: 10*kg + 6.25*cm - 5*tuổi + 5
    nữ : 10*kg + 6.25*cm - 5*tuổi - 161
"""
from dataclasses import dataclass, field

from diets import DIETS

ACTIVITY_FACTORS = {
    "it_van_dong": 1.2,      # ngồi nhiều, không tập
    "nhe": 1.375,            # tập 1-3 buổi/tuần
    "vua": 1.55,             # tập 3-5 buổi/tuần
    "nhieu": 1.725,          # tập 6-7 buổi/tuần
    "rat_nhieu": 1.9,        # lao động nặng, vận động viên
}

# Điều chỉnh calo so với TDEE theo mục tiêu (kcal/ngày)
GOAL_ADJUSTMENT = {"giam_can": -400, "giu_can": 0, "tang_can": 300}

# Đạm theo mục tiêu (g/kg cân nặng)
PROTEIN_PER_KG = {"giam_can": 1.6, "giu_can": 1.2, "tang_can": 1.8}

# Ngưỡng calo tối thiểu nhóm đặt ra để không gợi ý chế độ ăn quá khắt khe
MIN_CALORIES = {"nam": 1500, "nu": 1200}

KCAL_PER_G = {"protein": 4, "carb": 4, "fat": 9}
# Chia calo theo số bữa người dùng chọn (2-6 bữa/ngày)
MEAL_SPLITS = {
    2: {"trua": 0.50, "toi": 0.50},
    3: {"sang": 0.30, "trua": 0.40, "toi": 0.30},
    4: {"sang": 0.25, "trua": 0.35, "toi": 0.30, "phu": 0.10},
    5: {"sang": 0.25, "phu_sang": 0.10, "trua": 0.30, "phu_chieu": 0.10, "toi": 0.25},
    6: {"sang": 0.20, "phu_sang": 0.10, "trua": 0.25, "phu_chieu": 0.10, "toi": 0.25, "phu_toi": 0.10},
}
MEAL_SPLIT = MEAL_SPLITS[4]


@dataclass
class Profile:
    sex: str            # "nam" | "nu"
    age: int            # năm
    weight_kg: float
    height_cm: float
    activity: str       # khóa trong ACTIVITY_FACTORS
    goal: str           # khóa trong GOAL_ADJUSTMENT
    diet: str = "can_bang"  # khóa trong diets.DIETS
    meals: int = 4      # số bữa mỗi ngày, 2-6

    def validate(self):
        if self.sex not in MIN_CALORIES:
            raise ValueError(f"giới tính không hợp lệ: {self.sex}")
        if not 18 <= self.age <= 80:
            raise ValueError("chỉ hỗ trợ người trưởng thành 18-80 tuổi")
        if not 30 <= self.weight_kg <= 250 or not 120 <= self.height_cm <= 230:
            raise ValueError("cân nặng hoặc chiều cao ngoài khoảng hợp lý")
        if self.activity not in ACTIVITY_FACTORS:
            raise ValueError(f"mức vận động không hợp lệ: {self.activity}")
        if self.goal not in GOAL_ADJUSTMENT:
            raise ValueError(f"mục tiêu không hợp lệ: {self.goal}")
        if self.diet not in DIETS:
            raise ValueError(f"chế độ ăn không hợp lệ: {self.diet}")
        if self.meals not in MEAL_SPLITS:
            raise ValueError("số bữa phải từ 2 đến 6")


@dataclass
class EnergyPlan:
    bmr: float
    tdee: float
    target_kcal: float
    protein_g: float
    fat_g: float
    carb_g: float
    floor_applied: bool
    meals: dict = field(default_factory=dict)   # bữa -> kcal


def bmr_mifflin(sex, age, weight_kg, height_cm):
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if sex == "nam" else base - 161


def plan_energy(p: Profile) -> EnergyPlan:
    p.validate()
    bmr = bmr_mifflin(p.sex, p.age, p.weight_kg, p.height_cm)
    tdee = bmr * ACTIVITY_FACTORS[p.activity]

    target = tdee + GOAL_ADJUSTMENT[p.goal]
    floor_applied = target < MIN_CALORIES[p.sex]
    target = max(target, MIN_CALORIES[p.sex])

    diet = DIETS[p.diet]
    protein_g = PROTEIN_PER_KG[p.goal] * p.weight_kg
    if diet.carb_share is not None:  # ít tinh bột, keto: cố định tinh bột, béo là phần còn lại
        carb_g = target * diet.carb_share / KCAL_PER_G["carb"]
        if diet.carb_cap_g is not None:
            carb_g = min(carb_g, diet.carb_cap_g)
        fat_kcal = target - protein_g * KCAL_PER_G["protein"] - carb_g * KCAL_PER_G["carb"]
        if fat_kcal < 0:
            raise ValueError("đạm và tinh bột vượt tổng calo mục tiêu")
        fat_g = fat_kcal / KCAL_PER_G["fat"]
    else:
        fat_g = target * diet.fat_share / KCAL_PER_G["fat"]
        carb_kcal = target - protein_g * KCAL_PER_G["protein"] - fat_g * KCAL_PER_G["fat"]
        if carb_kcal < 0:
            raise ValueError("đạm và béo vượt tổng calo mục tiêu")
        carb_g = carb_kcal / KCAL_PER_G["carb"]

    meals = {m: target * share for m, share in MEAL_SPLITS[p.meals].items()}
    return EnergyPlan(bmr, tdee, target, protein_g, fat_g, carb_g, floor_applied, meals)


if __name__ == "__main__":
    demo = Profile(sex="nu", age=22, weight_kg=55, height_cm=160, activity="nhe", goal="giam_can")
    e = plan_energy(demo)
    print(f"BMR {e.bmr:.0f} | TDEE {e.tdee:.0f} | mục tiêu {e.target_kcal:.0f} kcal")
    print(f"Đạm {e.protein_g:.0f} g | Béo {e.fat_g:.0f} g | Tinh bột {e.carb_g:.0f} g")
    print("Theo bữa:", {k: round(v) for k, v in e.meals.items()})
