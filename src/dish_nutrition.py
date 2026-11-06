"""Tính dinh dưỡng một khẩu phần món ăn từ công thức và bảng của Viện Dinh dưỡng.

Mọi định lượng trong công thức là khối lượng sống, phần ăn được (đúng đơn vị của bảng
Viện Dinh dưỡng: giá trị trên 100 g phần ăn được). Ô trống trong bảng được coi là 0.
"""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("energy_kcal", "protein_g", "fat_g", "carb_g")


def load_ingredients(paths=(ROOT / "data" / "ingredients_vdd.csv", ROOT / "data" / "ingredients_supplement.csv")):
    """Bảng Viện Dinh dưỡng là nguồn chính; bảng bổ sung (USDA) chỉ thêm mã mới."""
    table = {}
    for path in paths:
        if not Path(path).exists():
            continue
        with open(path, encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                if row["code"] in table:
                    raise ValueError(f"mã nguyên liệu trùng: {row['code']}")
                table[row["code"]] = {k: float(row[k] or 0) for k in FIELDS} | {"name": row["name_vi"], "category": row["category"]}
    return table


def load_recipes(path=ROOT / "data" / "recipes_sample.csv"):
    recipes = defaultdict(list)
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            recipes[row["ma_mon"]].append((row["ma_vdd"], float(row["gam_mac_dinh"])))
    return dict(recipes)


def dish_nutrition(lines, ingredients, scale=1.0):
    """lines: [(mã VDD, gam)] -> tổng kcal, đạm, béo, tinh bột cho khẩu phần đã nhân scale."""
    total = dict.fromkeys(FIELDS, 0.0)
    for code, grams in lines:
        ing = ingredients[code]  # KeyError nếu công thức dùng mã không có trong bảng
        for k in FIELDS:
            total[k] += ing[k] * grams * scale / 100
    return total


def load_catalog(path=ROOT / "data" / "dishes_catalog.csv"):
    with open(path, encoding="utf-8-sig") as f:
        return {row["ma_mon"]: row for row in csv.DictReader(f)}


if __name__ == "__main__":
    ing, rec, cat = load_ingredients(), load_recipes(), load_catalog()
    print(f"{'Mã':5} {'Món':26} {'kcal':>6} {'Đạm':>6} {'Béo':>6} {'TB':>6}")
    for code, lines in rec.items():
        n = dish_nutrition(lines, ing)
        print(f"{code:5} {cat[code]['ten_mon']:26} {n['energy_kcal']:6.0f} {n['protein_g']:6.1f} "
              f"{n['fat_g']:6.1f} {n['carb_g']:6.1f}")
