# Carehome

## Description

Carehome is a Flask-based smart-home monitoring system for elderly care.
Sensor events from devices around the home (motion, door, temperature, bed
occupancy, panic button) are collected through a REST API, stored in SQLite,
and analysed for anomalies such as panic-button presses, suspicious night-time
door activity, abnormal temperatures, and prolonged inactivity. The app serves
three web views: a caregiver dashboard, a large-button resident tablet view,
and a sensor simulator for testing.

## Team

- Samuel Elesho

## Technologies

- Python 3.11+
- Flask 3.x
- APScheduler 3.x
- SQLite
- HTML / CSS / JavaScript

## Setup

```powershell
cd Project\carehome
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

The app starts on `http://127.0.0.1:5000`. On first launch the SQLite database
`carehome.db` is created and seeded automatically.
