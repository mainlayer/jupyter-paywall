# jupyter-paywall

[![CI](https://github.com/mainlayer/jupyter-paywall/actions/workflows/ci.yml/badge.svg)](https://github.com/mainlayer/jupyter-paywall/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/jupyter-paywall.svg)](https://badge.fury.io/py/jupyter-paywall)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Gate notebook cells behind a **Mainlayer paywall**. Share notebooks publicly, protect premium analysis with license checks. Readers buy access; you get paid. No payment code to build.

## Installation

```bash
pip install jupyter-paywall
```

### Requirements

- Python 3.7+
- Jupyter 5.3+

## 5-Minute Setup

### 1. Load the extension at the top of your notebook

```python
%load_ext mainlayer_jupyter
```

### 2. Free cells (run for everyone)

```python
import pandas as pd
df = pd.read_csv("data.csv")
print(f"Rows: {len(df)}")  # This runs for anyone
```

### 3. Premium cells (require a license)

```python
%%mainlayer_paid
# Only runs if user has a valid Mainlayer license
advanced_stats = df.describe(percentiles=[.25, .5, .75, .9, .99])
print(advanced_stats)
```

### 4. Share the notebook publicly

When someone without a license runs a premium cell, they see:

```
╔══════════════════════════════════════════════════════╗
║           PREMIUM CONTENT — LICENSE REQUIRED         ║
╠══════════════════════════════════════════════════════╣
║  This notebook cell requires a Mainlayer license.    ║
║                                                      ║
║  Get your license at: https://mainlayer.fr           ║
╚══════════════════════════════════════════════════════╝
```

They buy a license, set it, and re-run the cell. Done!

## License Configuration

### Method 1: Environment variable (recommended for CI/CD)

```bash
export MAINLAYER_LICENSE=ml_live_xxxxxxxxxxxxx
jupyter notebook
```

### Method 2: Pass inline to a cell

```python
%%mainlayer_paid --key ml_live_xxxxxxxxxxxxx
print("This runs with the inline key")
```

### Method 3: Store in config file (persistent)

```bash
mkdir -p ~/.mainlayer
cat > ~/.mainlayer/config.json << EOF
{ "api_key": "ml_live_xxxxxxxxxxxxx" }
EOF
```

Then use `%%mainlayer_paid` with no arguments.

## Magic Command Options

```python
%%mainlayer_paid [--key LICENSE_KEY] [--silent]
<cell code>
```

| Option | Description |
|--------|-------------|
| `--key, -k LICENSE_KEY` | Override env/config with this key |
| `--silent` | Suppress error message if license missing |

## Examples

### Basic free notebook (no setup needed)

```python
%load_ext mainlayer_jupyter

import pandas as pd
df = pd.read_csv("public_data.csv")
df.head()  # Everyone sees this
```

### Mixed free + premium cells

```python
%load_ext mainlayer_jupyter

# Free
df = pd.read_csv("data.csv")

# Premium
%%mainlayer_paid
df_ml_predictions = model.predict(df)  # Only with license
print(df_ml_predictions)
```

## Monetization Flow

1. **Create notebook** with free + premium cells
2. **Share publicly** on GitHub, nbviewer, or your site
3. **Create resource** on mainlayer.fr with a price
4. **Customers** buy a license key for $5-$500
5. **They set** `export MAINLAYER_LICENSE=...`
6. **Premium cells** unlock instantly
7. **You get paid** monthly via Mainlayer

## Architecture

```
src/
├── mainlayer_jupyter.py  # IPython magic (%%mainlayer_paid)
└── paywall.py            # License verification + 12h cache
```

License checks are cached for 12 hours — subsequent runs have zero API latency.
