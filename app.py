from flask import Flask, jsonify, send_file
import threading
from uuid import uuid4
from flask_cors import CORS
from db import db
import models
from report_generator import generate_report_in_thread
from store_activity import store_activity_report, monitored_data

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///loop_ai.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


db.init_app(app)

with app.app_context():
    db.create_all()

tasks = {}

@app.route('/trigger_report', methods=['POST'])
def trigger_report():
    report_id = str(uuid4())
    tasks[report_id] = 'Running'
    threading.Thread(target=lambda: generate_report_in_thread(app, report_id, tasks)).start()
    return jsonify({"report_id": report_id}), 202

@app.route('/get_report/<report_id>', methods=['GET'])
def get_report(report_id):
    status = tasks.get(report_id, None)
    if status is None:
        return jsonify({"error": "Report not found."}), 404
    elif status == 'Running':
        return jsonify({"status": "Running"}), 202
    elif status == 'Complete':
        return send_file(f'reports/report_{report_id}.csv', as_attachment=True)
    else:
        return jsonify({"error": "Unknown error."}), 500

@app.route('/get_monitored_data')
def get_monitored_data():
    return monitored_data()

@app.route('/report/store_activity/<int:store_id>', methods=['GET'])
def get_activity_report(store_id):
    return store_activity_report(store_id)

if __name__ == '__main__':
    app.run(debug=True)

