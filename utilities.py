
from datetime import datetime, timezone, timedelta

#* Function to convert timestamp(int) to string(Human readable format)
def timestamp2string(timestamp):
    # Convert milliseconds to seconds for datetime
    timestamp_seconds = timestamp / 1000.0

    # Create a datetime object from the timestamp
    dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)

    # Format the datetime object as a string
    formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S:%f')[:-3]  # Keep only milliseconds
    
    return formatted_timestamp

#* Function to convert timestamp(int) to datetime object
def timestamp2datetime(timestamp):
    # Convert milliseconds to seconds for datetime
    timestamp_seconds = timestamp / 1000.0

    # Create a datetime object from the timestamp
    dt = datetime.fromtimestamp(timestamp_seconds, tz=timezone.utc)
    
    return dt