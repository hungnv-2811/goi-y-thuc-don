"""Kiểm tra khả thi: ghép tay một thực đơn ngày bằng khẩu phần mặc định rồi so với mục tiêu.

Mục đích tuần 1: xác nhận dữ liệu và công thức chạy thông suốt từ hồ sơ người dùng đến tổng
dinh dưỡng; độ lệch so với mục tiêu là việc bộ tối ưu (tuần 3) phải xử lý.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from dish_nutrition import dish_nutrition, load_catalog, load_ingredients, load_recipes  # noqa: E402
from tdee import Profile, plan_energy  # noqa: E402

MENU = {
    "sang": ["M053"],                    # bánh mỳ trứng ốp la
    "trua": ["M042", "M043", "M044"],    # cơm, ức gà áp chảo, rau muống luộc
    "toi": ["M042", "M045", "M046"],     # cơm, cá rô phi kho, canh cải
    "phu": ["M052"],                     # sữa chua chuối
}

if __name__ == "__main__":
    profile = Profile(sex="nu", age=22, weight_kg=55, height_cm=160, activity="nhe", goal="giam_can")
    plan = plan_energy(profile)
    ing, rec, cat = load_ingredients(), load_recipes(), load_catalog()

    day = dict.fromkeys(("energy_kcal", "protein_g", "fat_g", "carb_g"), 0.0)
    for meal, dishes in MENU.items():
        kcal = 0.0
        for d in dishes:
            n = dish_nutrition(rec[d], ing)
            kcal += n["energy_kcal"]
            for k in day:
                day[k] += n[k]
        target = plan.meals[meal]
        print(f"{meal:5} {kcal:6.0f} kcal / mục tiêu {target:4.0f} ({(kcal - target) / target:+.0%})")

    targets = {"energy_kcal": plan.target_kcal, "protein_g": plan.protein_g,
               "fat_g": plan.fat_g, "carb_g": plan.carb_g}
    for k, t in targets.items():
        print(f"{k:12} {day[k]:7.1f} / {t:7.1f} ({(day[k] - t) / t:+.0%})")
