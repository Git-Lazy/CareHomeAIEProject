carehome/
├── app.py                  # Flask app entry point
├── db.py                   # Database initialisation and helpers
├── anomaly.py              # Anomaly detection rules
├── scheduler.py            # APScheduler jobs (reminders, anomaly checks)
├── routes/
│   ├── events.py           # /event endpoints
│   ├── alerts.py           # /alerts endpoints
│   └── devices.py          # /device endpoints
├── templates/
│   ├── simulator.html      # Sensor simulator panel
│   ├── tablet.html         # Elderly resident UI
│   └── caregiver.html      # Family/caregiver dashboard
├── static/
│   ├── style.css
│   └── main.js
├── carehome.db             # SQLite database file (auto-generated)
└── requirements.txt