import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from diets import DIETS, compatible, dish_groups, food_groups  # noqa: E402
from shopping import pantry_coverage, shopping_list  # noqa: E402

ING = {
    "1004": {"name": "Gạo, trắng, tẻ, xát máy, sống", "category": "Ngũ cốc và sản phẩm chế biến"},
    "9012": {"name": "Trứng gà công nghiệp", "category": "Trứng và sản phẩm chế biến"},
    "8024": {"name": "Cá rô phi, tươi", "category": "Thủy sản và sản phẩm chế biến"},
    "7003": {"name": "Thịt bò, loại I, tươi", "category": "Thịt và sản phẩm chế biến"},
    "3025": {"name": "Đậu phụ, sống", "category": "Hạt, quả giàu đạm, béo và sản phẩm chế biến"},
    "13017": {"name": "Nước mắm cá", "category": "Gia vị, nước chấm"},
    "4016": {"name": "Cải xanh, tươi", "category": "Rau, quả, củ dùng làm rau"},
}


class TestShopping(unittest.TestCase):
    def test_aggregates_and_subtracts_pantry(self):
        lines = [("1004", 80), ("1004", 80), ("9012", 100), ("4016", 150)]
        rows = {r["code"]: r for r in shopping_list(lines, ING, pantry={"1004": 1000, "9012": 50})}
        self.assertEqual(rows["1004"]["need_g"], 160)
        self.assertEqual(rows["1004"]["buy_g"], 0)          # đủ gạo trong nhà
        self.assertEqual(rows["9012"]["from_pantry_g"], 50)
        self.assertEqual(rows["9012"]["buy_g"], 50)
        self.assertEqual(rows["4016"]["buy_g"], 150)

    def test_rounds_up_to_10g(self):
        rows = shopping_list([("4016", 143)], ING)
        self.assertEqual(rows[0]["buy_g"], 150)

    def test_pantry_coverage(self):
        rows = shopping_list([("1004", 100), ("4016", 100)], ING, pantry={"1004": 100})
        self.assertAlmostEqual(pantry_coverage(rows), 0.5)


class TestDiets(unittest.TestCase):
    def test_ten_diets(self):
        self.assertEqual(len(DIETS), 10)

    def test_groups(self):
        self.assertIn("thit_do", food_groups("Thịt bò, loại I, tươi", "Thịt và sản phẩm chế biến"))
        self.assertIn("thuy_san", food_groups("Nước mắm cá", "Gia vị, nước chấm"))
        self.assertIn("dau_do", food_groups("Đậu phụ, sống", "Hạt, quả giàu đạm, béo và sản phẩm chế biến"))

    def test_compatibility(self):
        tofu_tomato = dish_groups([("3025", 150), ("13017", 5)], ING)   # có nước mắm
        self.assertTrue(compatible(tofu_tomato, "an_chay") is False)    # nước mắm là thủy sản
        self.assertTrue(compatible(tofu_tomato, "chay_co_ca"))
        self.assertFalse(compatible(tofu_tomato, "paleo"))              # đậu phụ là đậu đỗ
        fish = dish_groups([("8024", 150)], ING)
        self.assertTrue(compatible(fish, "chay_co_ca"))
        self.assertFalse(compatible(fish, "an_chay"))
        rice = dish_groups([("1004", 80)], ING)
        self.assertFalse(compatible(rice, "keto"))
        self.assertTrue(compatible(rice, "thuan_chay"))


if __name__ == "__main__":
    unittest.main()
