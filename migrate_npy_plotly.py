"""One-off migration of pickled plotly figures in datas/*.npy and extras/*.npy.

plotly 6 dropped the `heatmapgl` and `pointcloud` trace types. Figures saved by
plotly 5.16 embed the whole `plotly_dark` template (which holds default styles
for every trace type), so unpickling them under plotly 7 raises
`ValueError: Bad property path: heatmapgl`.

plotly pickles a figure as `(Figure, (figure_dict,))`, so the raw spec can be
captured without validation, cleaned with `skip_invalid=True` and re-validated
strictly before being written back.

Usage:  python migrate_npy_plotly.py [--root DIR] (--check | --apply)
"""

import argparse
import glob
import os
import sys

import numpy as np
import plotly.graph_objs as go
import plotly.graph_objs._figure as _figure_mod


class CaptureFigure:
    """Stands in for plotly.graph_objs._figure.Figure during unpickling."""

    def __init__(self, props=None, *args, **kwargs):
        self.props = props


def template_keys(spec):
    try:
        return set(spec["layout"]["template"]["data"].keys())
    except (KeyError, TypeError):
        return set()


def migrate(path):
    """Return (array_of_strict_figures, dropped_keys)."""
    real_figure = _figure_mod.Figure
    _figure_mod.Figure = CaptureFigure
    try:
        captured = np.load(path, allow_pickle=True)
    finally:
        _figure_mod.Figure = real_figure

    cleaned, dropped = [], set()
    for item in captured:
        spec = item.props if isinstance(item, CaptureFigure) else item.to_plotly_json()
        tolerant = go.Figure(spec, skip_invalid=True)
        strict = go.Figure(tolerant.to_plotly_json())  # must validate without skip_invalid
        dropped |= template_keys(spec) - template_keys(strict.to_plotly_json())
        cleaned.append(strict)
    return np.array(cleaned, dtype=object), dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/home/alexkuz60/emolab")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true", help="report only")
    group.add_argument("--apply", action="store_true", help="rewrite the files")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.root, "datas", "*.npy"))) + \
        sorted(glob.glob(os.path.join(args.root, "extras", "*.npy")))
    print(f"{len(files)} files, mode={'APPLY' if args.apply else 'CHECK'}")

    readable = migrated = failed = 0
    all_dropped = set()
    for path in files:
        rel = os.path.relpath(path, args.root)
        try:
            np.load(path, allow_pickle=True)
            readable += 1
            continue
        except Exception:
            pass

        try:
            arr, dropped = migrate(path)
        except Exception as exc:
            failed += 1
            print(f"  FAILED  {rel}: {type(exc).__name__}: {exc}")
            continue

        all_dropped |= dropped
        migrated += 1
        print(f"  {'rewrote' if args.apply else 'would rewrite'} {rel}: {arr.shape[0]} figures")
        if args.apply:
            np.save(path, arr, allow_pickle=True)

    print(f"already readable={readable}  {'migrated' if args.apply else 'to migrate'}={migrated}  failed={failed}")
    if all_dropped:
        print(f"template entries dropped (unknown to plotly 7): {sorted(all_dropped)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
