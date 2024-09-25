from flask import jsonify
from db import db
from models import Store, BusinessHours, PollData
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

def store_activity_report(store_id):
    store = db.session.get(Store, store_id)
    if not store:
        return jsonify({"error": "Store not found."}), 404

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30)

    store_data = Store.query.options(
        joinedload(Store.business_hours),
        joinedload(Store.status_poll_data.and_(
            PollData.timestamp_utc.between(start_date, end_date)
        ))
    ).filter_by(store_id=store_id).first()

    if not store_data.status_poll_data:
        return jsonify({"error": "Poll Data not found for the store."}), 404

    if not store_data.business_hours:
        return jsonify({"error": "Buisness hours not found for the store."}), 404

    report = generate_activity_report(store_data, start_date, end_date)
    return jsonify(report)

def generate_activity_report(store_data, start_date, end_date):
    report_data = []

    for business_hour in store_data.business_hours:
        day = business_hour.day_of_week
        current_date = start_date
        while current_date <= end_date:
            if current_date.weekday() == day:
                start_time = datetime.combine(current_date, business_hour.start_time_local)
                end_time = datetime.combine(current_date, business_hour.end_time_local)
                offline_online_periods = find_offline_online_periods(store_data.status_poll_data, start_time, end_time)
                report_data.append({
                    "date": current_date.strftime('%Y-%m-%d'),
                    "dayOfWeek": day,
                    "offline_online_periods": offline_online_periods,
                })
            current_date += timedelta(days=1)

    return report_data

def find_offline_online_periods(status_poll_data, start_time, end_time):
    offline_online_periods = []
    offline_start = None
    online_start = None

    for poll in sorted(status_poll_data, key=lambda x: x.timestamp_utc):
        if start_time <= poll.timestamp_utc <= end_time:
            if poll.status == 'inactive' and not offline_start:
                offline_start = poll.timestamp_utc
            elif poll.status == 'active' and not online_start:
                online_start = poll.timestamp_utc
            elif poll.status == 'active' and offline_start:
                offline_online_periods.append({"status": "Offline", "start": offline_start, "end": poll.timestamp_utc})
                offline_start = None
            elif poll.status == 'inactive' and online_start:
                offline_online_periods.append({"status": "Online", "start": online_start, "end": poll.timestamp_utc})
                online_start = None

    if offline_start:
        offline_online_periods.append({"status": "Offline", "start": offline_start, "end": end_time})
    if online_start:
        offline_online_periods.append({"status": "Online", "start": online_start, "end": end_time})


    return offline_online_periods

def monitored_data():
    total_stores = Store.query.count()
    total_business_hours = BusinessHours.query.count()
    total_polls = PollData.query.count()

    return f"Stores: {total_stores}, Business Hours: {total_business_hours}, Poll Data: {total_polls}"

