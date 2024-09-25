import pandas as pd
from datetime import datetime
from app import app 
from db import db
from models import Store, BusinessHours, PollData


def load_data():
    with app.app_context():
        
        store_timezone_df = pd.read_csv('data/bq-results-20230125-202210-1674678181880.csv')
        for _, row in store_timezone_df.iterrows():
            store = Store(store_id=row['store_id'], timezone_str=row['timezone_str'])
            db.session.add(store)

        business_hours_df = pd.read_csv('data/Menu-hours.csv')
        for _, row in business_hours_df.iterrows():
            
            start_time_obj = datetime.strptime(row['start_time_local'], '%H:%M:%S').time()
            end_time_obj = datetime.strptime(row['end_time_local'], '%H:%M:%S').time()

            business_hour = BusinessHours(
                store_id=row['store_id'], 
                day_of_week=row['day'], 
                start_time_local=start_time_obj, 
                end_time_local=end_time_obj
            )
            db.session.add(business_hour)	
	
        
        store_status_df = pd.read_csv('data/store-status.csv')
        for _, row in store_status_df.iterrows():
            status_poll_data = PollData(
                store_id=row['store_id'], 
                timestamp_utc=pd.to_datetime(row['timestamp_utc']), 
                status=row['status']
            )
            db.session.add(status_poll_data)
        
        db.session.commit()

if __name__ == '__main__':
    load_data()
