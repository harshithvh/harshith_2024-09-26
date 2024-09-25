import pandas as pd
from db import db
import math
from models import Store, BusinessHours, PollData
from datetime import datetime, timedelta
from sqlalchemy import func

def calculate_uptime_downtime(start, end, polls):
    uptime = downtime = 0
    last_status = "inactive"
    last_time = start

    for poll in polls:
        if poll.timestamp_utc < start or poll.timestamp_utc > end:
            continue
        delta = (poll.timestamp_utc - last_time).total_seconds() / 60 
        if last_status == "active":
            uptime += delta
        else:
            downtime += delta
        last_status = poll.status
        last_time = poll.timestamp_utc

    final_delta = (end - last_time).total_seconds() / 60
    if last_status == "active":
        uptime += final_delta
    else:
        downtime += final_delta

    return uptime, downtime   


def generate_report(report_id, tasks):
 
    stores = db.session.query(Store.store_id, Store.timezone_str).all()
    max_timestamp = db.session.query(func.max(PollData.timestamp_utc)).scalar() or datetime.utcnow()

    report_data = []
    for store_id, timezone in stores:
        end_time = max_timestamp
        start_times = {
            'last_hour': end_time - timedelta(hours=1),
            'last_day': end_time - timedelta(days=1),
            'last_week': end_time - timedelta(weeks=1),
        }

        uptimes = {'last_hour': 0, 'last_day': 0, 'last_week': 0}
        downtimes = {'last_hour': 0, 'last_day': 0, 'last_week': 0}

        for period, start_time in start_times.items():
            business_hours = BusinessHours.query.filter(
                BusinessHours.store_id == store_id,
                BusinessHours.start_time_local <= end_time.time(),
                BusinessHours.end_time_local >= start_time.time()
            ).all()

            polls = PollData.query.filter(
                PollData.store_id == store_id,
                PollData.timestamp_utc >= start_time,
                PollData.timestamp_utc <= end_time
            ).order_by(PollData.timestamp_utc.asc()).all()

            for bh in business_hours:
                bh_start = datetime.combine(end_time.date(), bh.start_time_local)
                bh_end = datetime.combine(end_time.date(), bh.end_time_local)
                uptime, downtime = calculate_uptime_downtime(bh_start, bh_end, polls)
                uptimes[period] += uptime
                downtimes[period] += downtime

        report_row = {
            "store_id": store_id,
            "uptime_last_hour": math.ceil(uptimes['last_hour']),
            "uptime_last_day": math.ceil(uptimes['last_day'] / 60),
            "uptime_last_week": math.ceil(uptimes['last_week'] / 60),
            "downtime_last_hour": math.ceil(downtimes['last_hour']),
            "downtime_last_day": math.ceil(downtimes['last_day'] / 60),
            "downtime_last_week": math.ceil(downtimes['last_week'] / 60),
        }
        report_data.append(report_row)

    report_df = pd.DataFrame(report_data)
    report_filename = f'reports/report_{report_id}.csv'
    report_df.to_csv(report_filename, index=False)

    tasks[report_id] = 'Complete'
    print(f"Report generated: {report_filename}")
    
    
def generate_report_in_thread(app, report_id, tasks):
    with app.app_context():
        generate_report(report_id, tasks)

