# jupyter-paywall

[![CI](https://github.com/mainlayer/jupyter-paywall/actions/workflows/ci.yml/badge.svg)](https://github.com/mainlayer/jupyter-paywall/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/jupyter-paywall.svg)](https://badge.fury.io/py/jupyter-paywall)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Gate Jupyter notebook cells behind a **Mainlayer payment wall**. Share notebooks publicly, keep premium cells protected.

## Installation

```bash
pip install jupyter-paywall
```

## Quick Start

```python
# At the top of your notebook:
%load_ext mainlayer_jupyter

# Free cells run normally...
import pandas as pd
df = pd.DataFrame({"x": [1, 2, 3]})

# Premium cells require a license:
%%mainlayer_paid
# Only runs with a valid Mainlayer license
print("Premium analysis running...")
df_advanced = df.groupby("category").agg({"revenue": ["sum", "mean", "std"]})
```

## License Setup

Set your license key using one of these methods:

```bash
# Environment variable (recommended for CI/CD)
export MAINLAYER_LICENSE=your_license_key

# Or pass inline:
%%mainlayer_paid --key your_license_key
print("Premium content")
```

Or store permanently in `~/.mainlayer/config.json`:
```json
{ "api_key": "your_license_key" }
```

## Magic Options

```
%%mainlayer_paid [--key LICENSE_KEY] [--silent]

Options:
  --key, -k    License key (overrides env/config)
  --silent     Suppress paywall error message
```

## Example Notebooks

- [examples/basic_notebook.ipynb](examples/basic_notebook.ipynb) — Free content, no license needed
- [examples/premium_analysis.ipynb](examples/premium_analysis.ipynb) — Premium cells with paywall

## Sell Access to Your Notebooks

1. Create a resource on [mainlayer.fr](https://mainlayer.fr)
2. Set a price per license or subscription
3. Share the notebook publicly — the `%%mainlayer_paid` magic gates execution
4. Customers buy a license key and use it to unlock premium cells

## Architecture

```
src/
├── mainlayer_jupyter.py  # IPython magic extension (%%mainlayer_paid)
└── paywall.py            # License verification + caching
```
