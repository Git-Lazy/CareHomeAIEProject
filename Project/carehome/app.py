from flask import Flask, render_template
import db
import scheduler

app = Flask(__name__)
app.teardown_appcontext(db.close_db)

# ── blueprints ────────────────────────────────────────────────────────────────
from routes.events  import bp as events_bp
from routes.alerts  import bp as alerts_bp
from routes.devices import bp as devices_bp

app.register_blueprint(events_bp)
app.register_blueprint(alerts_bp)
app.register_blueprint(devices_bp)

# ── page routes ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("caregiver.html")


@app.route("/tablet")
def tablet():
    return render_template("tablet.html")


@app.route("/simulator")
def simulator():
    devices = [dict(d) for d in db.get_all_devices()]
    return render_template("simulator.html", devices=devices)


# ── startup ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    db.init_db()
    scheduler.start_scheduler(app)
    app.run(debug=True, use_reloader=False)
