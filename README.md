# Applied economics portfolio

Small, complete, tested projects in applied microeconomics, antitrust, finance and data work. Each project lives in its own folder with a README, data sources, tests and a one command entry point.

| # | Project | Problem | Methods | Link |
|---|---|---|---|---|
| 01 | Merger screen toolkit | Flag mergers that trip the 2023 US Merger Guidelines concentration presumption | HHI and change in HHI, 30 percent share test, proportional diversion, GUPPI and UPP | [projects/01-merger-screen](projects/01-merger-screen) |
| 02 | Pakistan tehsil crosswalk, Census 2017 to 2023 | Move tehsil and district data between Pakistan's 2017 and 2023 census frames with population and area weights | Exact population balancing on PBS restatements, transportation LP for transfers, published-area weights, conservation checks | [projects/02-pakistan-tehsil-crosswalk](projects/02-pakistan-tehsil-crosswalk) |

## Running a project

```bash
cd projects/<project-folder>
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
pytest
```

Licensed under the MIT License (see `LICENSE`).
