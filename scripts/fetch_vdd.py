"""Tải bảng thành phần thực phẩm từ trang tra cứu của Viện Dinh dưỡng.

Nguồn: https://viendinhduong.vn/vi/cong-cu-va-tien-ich/gia-tri-dinh-duong-thuc-pham
Trang này gọi endpoint JSON công khai bên dưới; giá trị tính trên 100 g phần ăn được.

Kết quả:
    data/raw/vdd_foods.json      dữ liệu gốc đầy đủ
    data/ingredients_vdd.csv     bảng rút gọn: năng lượng và các chất chính
"""
import csv
import json
import time
import urllib.request
from pathlib import Path

API = "https://viendinhduong.vn/api/fe/foodNatunal/getPageFoodData?page={page}&pageSize={size}"
PAGE_SIZE = 200
ROOT = Path(__file__).resolve().parent.parent

# Khóa trong dữ liệu gốc -> tên cột trong bảng rút gọn
NUTRIENTS = {
    "protein": "protein_g",
    "total-lipid-fat": "fat_g",
    "carbohydrate-by-difference": "carb_g",
    "fibre-total-dietary": "fiber_g",
    "water": "water_g",
}


def fetch_page(page):
    req = urllib.request.Request(API.format(page=page, size=PAGE_SIZE),
                                 headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.load(resp)


def main():
    foods, page = [], 1
    while True:
        data = fetch_page(page)
        foods.extend(data["data"])
        if len(foods) >= data["total"] or not data["data"]:
            break
        page += 1
        time.sleep(1)  # không gửi dồn dập

    raw = ROOT / "data" / "raw" / "vdd_foods.json"
    raw.parent.mkdir(parents=True, exist_ok=True)
    raw.write_text(json.dumps(foods, ensure_ascii=False, indent=1), encoding="utf-8")

    out = ROOT / "data" / "ingredients_vdd.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["code", "name_vi", "name_en", "category", "energy_kcal", *NUTRIENTS.values()])
        for food in sorted(foods, key=lambda x: int(x["code"]) if x["code"].isdigit() else 0):
            values = {n["key"]: n["value"] for n in food.get("nutrition", [])}
            w.writerow([food["code"], food["name_vi"], food.get("name_en", ""), food["category"],
                        food.get("energy", ""), *(values.get(k, "") for k in NUTRIENTS)])
    print(f"{len(foods)} thực phẩm -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
