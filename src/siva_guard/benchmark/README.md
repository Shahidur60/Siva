# SIVA Judge Benchmark Pack (Template)

This folder helps you create a **defensible standard evaluator** for Judge v1.

## What this benchmark is
A labeled set of cases where you know the ground truth *for your ceremony setting*:
- Legit identities (known participants / known real accounts)
- Attacker-generated ephemeral impostor identities (you create these)

This lets you evaluate how often the Judge returns:
- FAKE when it should
- REAL when it should
- and when it abstains (LOW certainty)

## Files
- `cases_template.csv` : Fill this with cases (URLs/handles + label)
- `run_benchmark.py` : Runs /verify then /judge and writes results

## Quick start
1) Run the server:
```bash
uvicorn siva_guard.api.server:app --reload --port 8000
