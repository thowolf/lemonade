# create_weave_dashboard.py

Usage and notes for `scripts/create_weave_dashboard.py`.

Overview
--------
This script generates an offline, self-contained HTML report for benchmark results and can optionally log summary metrics and charts to Weights & Biases (W&B) and create a Weave saved view.

Dependencies
------------
- Python 3.10+
- matplotlib
- pillow (optional; used to attach images to W&B runs)
- wandb (optional; required for `--weave` to upload charts and create a Weave view)
- weave (optional; required to create Weave saved views programmatically)

Install e.g.:

```bash
pip install matplotlib pillow wandb weave
```

Basic usage
-----------
Generate an offline HTML report from the latest JSON results in `evaluation_results_large/`:

```bash
python scripts/create_weave_dashboard.py
```

Specify a particular results file:

```bash
python scripts/create_weave_dashboard.py --file evaluation_results_large/large_benchmark_1766.json
```

Output directory
----------------
By default the report is saved in `reports/lemonade_quick_benchmark_overview.html`.

Weave / W&B integration
-----------------------
To upload summary metrics and chart images to W&B and create a Weave saved view, use the `--weave` flag and optionally set `--project`:

```bash
python scripts/create_weave_dashboard.py --weave --project lemonade-ryzenai-evals-demo
```

Notes
-----
- The script will attempt to log metrics and images to W&B and create a Weave view only if `--weave` is provided and the `wandb`/`weave` packages are available and you are authenticated.
- The generated HTML report is self-contained and can be opened offline in a web browser.

Development
-----------
- Tests are located in `tests/test_create_weave_dashboard.py` (if present).
- To run tests:

```bash
pytest tests/test_create_weave_dashboard.py
```
