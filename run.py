"""Run all processing stages or render the poster from existing result tables."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STAGES = ("driver", "tips", "compare", "figures", "poster")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", choices=("all", *STAGES), default="all")
    parser.add_argument(
        "--data", type=Path, default=Path(os.getenv("TAXI_DATA", ROOT / "data"))
    )
    parser.add_argument(
        "--work", type=Path, default=Path(os.getenv("TAXI_WORK", ROOT / "work"))
    )
    args = parser.parse_args()
    scratch = args.work.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    for name in ["tables", "figures"]:
        (ROOT / name).mkdir(exist_ok=True)
    env = dict(os.environ, TAXI_DATA=str(args.data.resolve()), TAXI_WORK=str(scratch))
    env.setdefault("MPLCONFIGDIR", str(scratch / "matplotlib"))
    for stage in (STAGES if args.stage == "all" else (args.stage,)):
        print(f"Running {stage}", flush=True)
        subprocess.run(
            [sys.executable, str(ROOT / "code" / f"{stage}.py")], check=True, env=env
        )


if __name__ == "__main__":
    main()
