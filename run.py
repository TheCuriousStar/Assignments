import argparse
import csv
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import yaml


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--log-file", required=True)
    return parser.parse_args()


def setup_logging(log_file):
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        force=True,
    )


def load_config(path):
    logging.info("loading config: %s", path)

    if not Path(path).exists():
        raise ValueError("config file not found")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    if not isinstance(config, dict):
        raise ValueError("invalid config structure")

    for key in ["seed", "window", "version"]:
        if key not in config:
            raise ValueError(f"config missing required field: {key}")

    seed = int(config["seed"])
    window = int(config["window"])
    version = config["version"]

    if window <= 0:
        raise ValueError("window should be positive")

    logging.info("config loaded: seed=%s window=%s version=%s", seed, window, version)
    return seed, window, version


def read_input_data(path):
    logging.info("reading csv: %s", path)

    if not Path(path).exists():
        raise ValueError("input file not found")

    try:
        df = pd.read_csv(path, quoting=csv.QUOTE_NONE)
    except pd.errors.EmptyDataError:
        raise ValueError("input csv is empty")
    except pd.errors.ParserError:
        raise ValueError("invalid csv format")

    df.columns = df.columns.str.strip('"')

    if df.empty:
        raise ValueError("input csv is empty")

    if "close" not in df.columns:
        raise ValueError("close column missing")

    logging.info("csv loaded: rows=%s columns=%s", len(df), list(df.columns))
    return df


def compute_rolling_mean(df, window):
    logging.info("computing rolling mean: window=%s", window)
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df["rolling_mean"] = df["close"].rolling(window).mean()
    return df


def generate_signal(df):
    logging.info("generating binary signal")
    df["signal"] = 0
    df.loc[df["close"] > df["rolling_mean"], "signal"] = 1
    return df


def build_metrics(df, version, seed, latency_ms):
    valid_df = df.dropna(subset=["rolling_mean"])
    signal_rate = valid_df["signal"].mean()

    return {
        "version": version,
        "rows_processed": len(df),
        "metric": "signal_rate",
        "value": round(float(signal_rate), 4),
        "latency_ms": latency_ms,
        "seed": seed,
        "status": "success",
    }


def write_metrics(path, result):
    logging.info("writing metrics json: %s", path)

    with open(path, "w") as f:
        json.dump(result, f, indent=2)


def get_version(config_path):
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        if isinstance(config, dict) and "version" in config:
            return config["version"]
    except Exception:
        pass

    return "unknown"


def run_job(args):
    start = time.perf_counter()
    logging.info("job started")

    seed, window, version = load_config(args.config)
    np.random.seed(seed)

    df = read_input_data(args.input)
    df = compute_rolling_mean(df, window)
    df = generate_signal(df)

    latency_ms = int((time.perf_counter() - start) * 1000)
    result = build_metrics(df, version, seed, latency_ms)

    write_metrics(args.output, result)
    logging.info("metrics summary: %s", result)
    logging.info("job finished")

    return result


def main():
    args = parse_args()
    setup_logging(args.log_file)

    try:
        result = run_job(args)
        print(json.dumps(result, indent=2))
        return 0

    except Exception as e:
        result = {
            "version": get_version(args.config),
            "status": "error",
            "error_message": str(e),
        }

        write_metrics(args.output, result)
        logging.exception("job failed")
        print(json.dumps(result, indent=2))
        return 1


if __name__ == "__main__":
    sys.exit(main())
