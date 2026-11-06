"""Bổ sung thực phẩm mà bảng Viện Dinh dưỡng không có, lấy từ USDA FoodData Central (SR Legacy).

Mã nguyên liệu dạng "USDA-<fdcId>" để không trùng mã Viện Dinh dưỡng; cột nguon ghi rõ nguồn.
Khóa API: biến môi trường FDC_API_KEY, mặc định DEMO_KEY (giới hạn số lượt gọi mỗi giờ).
"""
import csv
import json
import os
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.nal.usda.gov/fdc/v1/food/{id}?api_key={key}&format=abridged"

# fdcId -> (tên tiếng Việt, nhóm)
FOODS = {
    171077: ("Ức gà, bỏ da, sống", "Thịt và sản phẩm chế biến"),
    168878: ("Cơm trắng (gạo tẻ hạt dài), đã nấu", "Ngũ cốc và sản phẩm chế biến"),
}
NUTRIENTS = {"208": "energy_kcal", "203": "protein_g", "204": "fat_g", "205": "carb_g", "291": "fiber_g", "255": "water_g"}


def main():
    key = os.environ.get("FDC_API_KEY", "DEMO_KEY")
    out = ROOT / "data" / "ingredients_supplement.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["code", "name_vi", "name_en", "category", *NUTRIENTS.values(), "nguon"])
        for fdc_id, (name_vi, category) in FOODS.items():
            with urllib.request.urlopen(API.format(id=fdc_id, key=key), timeout=60) as resp:
                food = json.load(resp)
            values = {n.get("number"): n.get("amount") for n in food.get("foodNutrients", [])}
            w.writerow([f"USDA-{fdc_id}", name_vi, food["description"], category,
                        *(values.get(k, "") for k in NUTRIENTS), f"USDA FoodData Central, {food['dataType']}, fdcId {fdc_id}"])
            print(fdc_id, food["description"])
    print(f"-> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
