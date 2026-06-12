# Task 0

TASK 0 : Batch job --> load YAML --> Read csv --> compute rolling mean --> generate binary signal --> metricJSON +logs --> runs locally

It does these things:

1. Loads config from 'config.yaml'
2. Read 'data.csv'
3. Uses the 'close' column
4. Compute rolling mean
5. Creates a signal column
6. Writes output - 'metrics.json'
7. Writes logs - run.log'
8. Can run locally and with Docker

## Files

- run.py - main file
- config.yaml - seed, window, and version
- data.csv - input OHLCV data
- requirements.txt - Python dependenies
- Dockerfile - Docker setup
- metrics.json - sample output
- run.log - sample logs

## Config

config.yaml:
seed: 42
window: 5
version: "v1"

## Local Run

Install packages:
pip install -r requirements.txt

Run the job:
python run.py --input data.csv --config config.yaml --output metrics.json --log-file run.log

## Docker Run

Build Docker image:
docker build -t mlops-task .

Run Docker container:
docker run --rm mlops-task

## Output

The program prints the final metrics JSON and also saves it in metrics.json.
{
  "version": "v1",
  "rows_processed": 10000,
  "metric": "signal_rate",
  "value": 0.4991,
  "latency_ms": 18,
  "seed": 42,
  "status": "success"
}

## Error handling
- The code checks that the csv file exists.
- it checks if the window is<=0.
- it checks that the close column exists.
- The first 'window - 1' rows have no rolling mean, so they are not used for calculating signal_rate.
- If there is an error, the program still writes metrics.json with error details.
