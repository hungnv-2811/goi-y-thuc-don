# Hệ thống gợi ý thực đơn cá nhân hóa dựa trên học máy và tối ưu hóa dinh dưỡng

Đồ án môn Học máy nâng cao – Khoa Công nghệ Thông tin, Trường Đại học Xây dựng Hà Nội.
Giảng viên hướng dẫn: Nguyễn Đình Quý. Thời gian: 02/11 – 06/12/2026 (5 tuần).

Người dùng nói nhu cầu ăn uống bằng tiếng Việt; hệ thống tính nhu cầu năng lượng theo 1 trong 10 chế độ ăn,
đề xuất thực đơn món Việt theo ngày hoặc tuần (2–6 bữa) kèm gam từng nguyên liệu, ưu tiên thực phẩm có sẵn
và lập danh sách đi chợ. Học máy chọn món (M1 PhoBERT, M2 gợi ý hybrid, M4 LinUCB), tối ưu hóa tính gam (M3 MILP).

## Cấu trúc

| Thư mục / tệp | Nội dung |
|---|---|
| `src/` | `tdee.py` (BMR, TDEE, macro theo chế độ ăn, số bữa), `diets.py` (10 chế độ ăn), `dish_nutrition.py`, `shopping.py` (danh sách đi chợ trừ đồ có sẵn) |
| `scripts/` | Tải và làm sạch dữ liệu, kiểm tra thực đơn mẫu, gán nhãn NLP, vẽ sơ đồ |
| `tests/` | Kiểm thử đơn vị (17 ca) |
| `data/` | Bảng dinh dưỡng Viện Dinh dưỡng (853 thực phẩm), bổ sung USDA, danh mục 100 món, 15 công thức, 40 câu gán nhãn |
| `docs/so-do/` | Sơ đồ phân tích thiết kế (PNG, SVG) |
| `tai-lieu/` | Đề cương, báo cáo tiến độ tuần 1, phiếu đăng ký – theo dõi tiến độ, tập sơ đồ (Word) |

## Chạy

Cần Python 3.11. Các mô-đun trong `src/` chỉ dùng thư viện chuẩn.

```bash
python tests/test_tdee.py
python tests/test_shopping_diets.py
python scripts/check_sample_day.py
```

Tạo lại dữ liệu:

```bash
python scripts/fetch_vdd.py              # bảng thành phần thực phẩm của Viện Dinh dưỡng
python scripts/fetch_usda_supplement.py  # ức gà, cơm chín từ USDA FoodData Central
python scripts/check_ingredients.py      # gắn cờ dòng dữ liệu lỗi
```

Dữ liệu Food.com không nằm trong repo vì quá lớn: tải `archive.zip` từ Kaggle
(shuyangli94/food-com-recipes-and-user-interactions), giải nén `RAW_interactions.csv` và `RAW_recipes.csv`
vào `data/foodcom/raw/`, rồi chạy `python scripts/prepare_foodcom.py` và `python scripts/baseline_popularity.py`.

Vẽ lại sơ đồ cần `pymupdf`: `python scripts/ve_so_do.py`.

## Nguồn dữ liệu

- Viện Dinh dưỡng – Tra cứu giá trị dinh dưỡng thực phẩm: https://viendinhduong.vn
- USDA FoodData Central: https://fdc.nal.usda.gov
- Majumder và cộng sự (2019), Generating Personalized Recipes from Historical User Preferences, EMNLP-IJCNLP – bộ dữ liệu Food.com
