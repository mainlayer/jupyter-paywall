"""
Mainlayer Jupyter Magic Extension

Provides the %%mainlayer_paid cell magic that gates cell execution
behind a Mainlayer license check.

Usage:
    %load_ext mainlayer_jupyter

    %%mainlayer_paid
    # This cell requires a premium license
    import pandas as pd
    df = pd.read_parquet("s3://my-bucket/premium-dataset.parquet")
    df.describe()

    # Pass key inline (overrides env/config):
    %%mainlayer_paid --key mlk_xxxxxxxx
    print("Premium content")
"""

from __future__ import annotations

import argparse
import sys
from typing import Optional

try:
    from IPython.core.magic import register_cell_magic, needs_local_scope
    from IPython.core.interactiveshell import InteractiveShell
    IPYTHON_AVAILABLE = True
except ImportError:
    IPYTHON_AVAILABLE = False

from .paywall import require_license, PaywallError


def _parse_args(line: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="%%mainlayer_paid",
        description="Execute cell only if a valid Mainlayer license is present",
        add_help=False,
    )
    parser.add_argument(
        "--key", "-k",
        dest="license_key",
        default=None,
        help="Mainlayer license key (overrides MAINLAYER_LICENSE env)",
    )
    parser.add_argument(
        "--silent",
        action="store_true",
        default=False,
        help="Suppress paywall message on failure",
    )
    try:
        return parser.parse_args(line.split() if line.strip() else [])
    except SystemExit:
        return argparse.Namespace(license_key=None, silent=False)


def mainlayer_paid_magic(line: str, cell: str, local_ns: dict) -> None:
    """
    Cell magic: %%mainlayer_paid [--key <license_key>] [--silent]

    Verifies a Mainlayer license before executing the cell body.
    """
    args = _parse_args(line)

    try:
        require_license(args.license_key)
    except PaywallError as e:
        if not args.silent:
            print(str(e), file=sys.stderr)
        return

    # License is valid — execute the cell
    if IPYTHON_AVAILABLE:
        ip = InteractiveShell.instance()
        ip.run_cell(cell, store_history=False, silent=False)
    else:
        exec(compile(cell, "<mainlayer_paid>", "exec"), local_ns)


def load_ipython_extension(ipython: "InteractiveShell") -> None:
    """
    Called by %load_ext mainlayer_jupyter
    Registers the %%mainlayer_paid cell magic.
    """
    if not IPYTHON_AVAILABLE:
        print("Warning: IPython is not available. Magic not registered.", file=sys.stderr)
        return

    ipython.register_magic_function(
        mainlayer_paid_magic,
        magic_kind="cell",
        magic_name="mainlayer_paid",
    )

    print("Mainlayer Jupyter extension loaded.")
    print("Use %%mainlayer_paid to gate cells behind a premium license.")
    print("Get a license at: https://mainlayer.fr")


def unload_ipython_extension(ipython: "InteractiveShell") -> None:
    """Called by %unload_ext mainlayer_jupyter"""
    pass
