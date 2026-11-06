import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from tdee import MEAL_SPLIT, MEAL_SPLITS, Profile, bmr_mifflin, plan_energy  # noqa: E402
from diets import DIETS  # noqa: E402


class TestBMR(unittest.TestCase):
    def test_female_example(self):
        # 10*55 + 6.25*160 - 5*22 - 161 = 1279
        self.assertAlmostEqual(bmr_mifflin("nu", 22, 55, 160), 1279)

    def test_male_example(self):
        # 10*70 + 6.25*175 - 5*30 + 5 = 1648.75
        self.assertAlmostEqual(bmr_mifflin("nam", 30, 70, 175), 1648.75)


class TestPlan(unittest.TestCase):
    def test_weight_loss_female(self):
        e = plan_energy(Profile("nu", 22, 55, 160, "nhe", "giam_can"))
        self.assertAlmostEqual(e.tdee, 1279 * 1.375)
        self.assertAlmostEqual(e.target_kcal, 1279 * 1.375 - 400)
        self.assertAlmostEqual(e.protein_g, 88.0)
        self.assertFalse(e.floor_applied)

    def test_macros_add_up_to_target(self):
        e = plan_energy(Profile("nam", 30, 70, 175, "vua", "tang_can"))
        total = e.protein_g * 4 + e.fat_g * 9 + e.carb_g * 4
        self.assertAlmostEqual(total, e.target_kcal)

    def test_meals_add_up_to_target(self):
        e = plan_energy(Profile("nam", 30, 70, 175, "vua", "giu_can"))
        self.assertAlmostEqual(sum(e.meals.values()), e.target_kcal)
        self.assertEqual(set(e.meals), set(MEAL_SPLIT))

    def test_calorie_floor(self):
        # người nhỏ, ít vận động, giảm cân -> dưới 1200 thì giữ ở 1200
        e = plan_energy(Profile("nu", 60, 42, 148, "it_van_dong", "giam_can"))
        self.assertTrue(e.floor_applied)
        self.assertEqual(e.target_kcal, 1200)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            plan_energy(Profile("nu", 15, 50, 155, "nhe", "giu_can"))
        with self.assertRaises(ValueError):
            plan_energy(Profile("nu", 25, 50, 155, "cuc_nhieu", "giu_can"))
        with self.assertRaises(ValueError):
            plan_energy(Profile("khac", 25, 50, 155, "nhe", "giu_can"))
        with self.assertRaises(ValueError):
            plan_energy(Profile("nu", 25, 50, 155, "nhe", "giu_can", diet="an_kieng_la"))
        with self.assertRaises(ValueError):
            plan_energy(Profile("nu", 25, 50, 155, "nhe", "giu_can", meals=7))


class TestDietsAndMeals(unittest.TestCase):
    def test_all_diets_add_up(self):
        for key in DIETS:
            e = plan_energy(Profile("nu", 22, 55, 160, "nhe", "giam_can", diet=key))
            total = e.protein_g * 4 + e.fat_g * 9 + e.carb_g * 4
            self.assertAlmostEqual(total, e.target_kcal, msg=key)
            self.assertGreater(e.carb_g, 0, key)

    def test_keto_carb_under_50g(self):
        e = plan_energy(Profile("nam", 30, 70, 175, "vua", "giu_can", diet="keto"))
        self.assertLessEqual(e.carb_g, 50)
        self.assertGreater(e.fat_g * 9 / e.target_kcal, 0.5)

    def test_low_carb_share(self):
        e = plan_energy(Profile("nu", 22, 55, 160, "nhe", "giu_can", diet="it_tinh_bot"))
        self.assertAlmostEqual(e.carb_g * 4 / e.target_kcal, 0.25)

    def test_every_meal_count(self):
        for n, split in MEAL_SPLITS.items():
            self.assertAlmostEqual(sum(split.values()), 1.0, msg=n)
            e = plan_energy(Profile("nu", 22, 55, 160, "nhe", "giu_can", meals=n))
            self.assertEqual(len(e.meals), n)
            self.assertAlmostEqual(sum(e.meals.values()), e.target_kcal)


if __name__ == "__main__":
    unittest.main()
