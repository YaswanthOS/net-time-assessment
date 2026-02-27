# Net Playing Time in Professional Football (DFL Dataset)

This repository contains a reproducible data pipeline for estimating **net playing time (NPT)** in professional football using official DFL event and tracking data.

The work is part of a PhD application project focused on:

- temporal structure of football matches
- determinants of stoppages
- consequences of increased net playing time for workload and injury risk

---

## Project Structure
src/ → core processing scripts
notebooks/ → analysis notebooks (event-based, tracking-based)
docs/ → project documentation
requirements.txt → reproducible environment
---

## Data

The project uses official DFL data including:

- event logs (XML)
- tracking data (XML)
- match metadata

Data are not shared due to licensing restrictions.

---

## Methodology

### Step 1 — Event-based Net Playing Time

Stoppages are detected from event logs using:

- restart events (throw-ins, free kicks, corners, penalties)
- decision timestamps
- goal → next kickoff intervals
- VAR start–end timestamps

Net playing time:
NPT = Match duration − total stoppage duration


### Step 2 — Tracking-based Net Playing Time (in progress)

Ball-in-play phases will be derived from:

- ball velocity
- ball status
- possession signals

This enables frame-level NPT estimation.

---

## Reproducibility

Install environment:
pip install -r requirements.txt

Run: python src/event_npt_pipeline.py


---

## Author

Yaswanth O. S.  
PhD Applicant — Science & Health in Football  
Saarland University
