# Telecom Revenue & Customer Behavior Analytics

This project analyzes Megaline customer behavior, monthly service usage, plan economics, revenue patterns, and statistical differences between service plans.

## Capabilities

- Aggregate calls, messages, and internet sessions to observed customer-month rows.
- Apply plan allowances and transparent overage billing.
- Compare usage and revenue by plan and region.
- Run Welch two-sample t-tests for plan and regional revenue differences.
- Reuse the analysis through `src/megaline_analytics.py`.
- Validate billing behavior with automated tests.

## Data access

The source CSV files are intentionally **not included** in this public repository. The project files do not document redistribution rights for the Megaline/educational source data, so the raw data is excluded as a precaution.

To run the analysis locally, place these files in `data/`:

```text
data/
├── megaline_users.csv
├── megaline_calls.csv
├── megaline_messages.csv
├── megaline_internet.csv
└── megaline_plans.csv
```

The raw files are local inputs and remain excluded from Git.

## Setup and validation

```bash
python -m pip install -r requirements.txt
pytest
```

The primary analysis notebook is `notebooks/telecom_revenue_analysis.ipynb`. Run all cells from the project root or from the `notebooks/` directory. It discovers the repository root from the project layout and does not embed raw records.

## Project structure

```text
telecom-revenue-analytics/
├── data/                         # local, ignored source CSVs
├── notebooks/
│   └── telecom_revenue_analysis.ipynb
├── src/
│   ├── __init__.py
│   └── megaline_analytics.py
├── tests/
│   └── test_billing.py
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## Billing rules

Calls are rounded up per call before monthly summation. Internet usage is summed in MB per customer-month and then rounded up to whole GB. Overage quantities are clipped at zero, and monthly revenue is the plan fee plus minute, message, and data overages.

## Verified results

The supplied local data produces 2,293 observed customer-month rows: 1,573 Surf rows and 720 Ultimate rows. Mean monthly revenue is $60.71 for Surf and $72.31 for Ultimate. Welch's t-test for plan revenue gives t = -7.9521 and p = 3.17e-15.

For the regional comparison, the NY-NJ metropolitan area versus all other regions gives t = -2.1309 and p = 0.03353. These results support a difference in average observed monthly revenue for both comparisons at the 5% level.

## Limitations

The data is a historical sample and the analysis is descriptive. Customer-month rows represent months with recorded activity, not every calendar month in a customer's tenure. Statistical tests compare observed monthly rows and do not establish causation.

## License

The reusable source code is released under the MIT License. The raw input datasets are excluded and remain subject to their original source terms.
