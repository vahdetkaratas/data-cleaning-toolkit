# Data

Demo datasets for the Data Cleaning Toolkit.

## Contents

| Folder           | File               | Description |
|------------------|--------------------|-------------|
| `demo_sales/`    | `sales_messy.csv`  | Sales demo with intentional issues: mixed date formats, missing `amount`, duplicate `order_id`, inconsistent `region` (North/NORTH/north). |
| `demo_customer/` | `customer_messy.csv` | Customer demo with intentional issues: mixed date formats, missing `lifetime_value`, duplicate `customer_id`, inconsistent `segment` (Gold/gold/GOLD/Premium). |

## Regenerating demo data

Run **`notebooks/02_prepare_demo_data.ipynb`** from the project root to overwrite these files with freshly generated messy data from clean templates.

## Schema (for reference)

- **Sales:** `order_id`, `order_date`, `product_id`, `amount`, `quantity`, `region`, `customer_id`
- **Customer:** `customer_id`, `signup_date`, `segment`, `lifetime_value`, `tenure`
