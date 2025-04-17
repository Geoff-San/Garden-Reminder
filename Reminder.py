# 1. [DONE-ISH] LOGIC: IF/ELSE statements to define whether I need to be notified if it's been two days since last precipitation over 1 inch
    # - Will need edits when I keep adding to the script
# 2. [DONE-ish] SMTP server stuff/sending emails
    # - need to secure the app password
# 3. [DONE] Need to get datetime of system, then edit start & end date to be the two days before
# 4. Figure out how to run this every morning @ 6 am
# 5. When will I clean up and organize the code? Such as setting classes.

## Later: consider storing all values in a sql database and then pulling from there? 
## Later: consider giving the option to select location and/or insert lat/longitude
## Later: need input for when I water plants

import openmeteo_requests

import requests_cache
import pandas as pd
from retry_requests import retry
import smtplib
from datetime import datetime
### --------------------- DateTime variables ---------------------- ###
today = datetime.now()
end_day = today.day - 1
end_date = today.strftime(f"%Y-%m-{end_day}")

start_day = today.day - 2
start_date = today.strftime(f"%Y-%m-{start_day}")

### --------------------- Weather API Data Retrieval ---------------------- ###
# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = 3600)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 29.65465625376178,
	"longitude": -82.3209970418961,
	"daily": ["precipitation_sum"],
	"timezone": "America/New_York",
	"wind_speed_unit": "mph",
	"temperature_unit": "fahrenheit",
	"precipitation_unit": "inch",
	"start_date": f"{start_date}",
	"end_date": f"{end_date}"
}
responses = openmeteo.weather_api(url, params=params)

# Process first location. Add a for-loop for multiple locations or weather models
response = responses[0]
print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
print(f"Elevation {response.Elevation()} m asl")
print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

# Process daily data. The order of variables needs to be the same as requested.
daily = response.Daily()
daily_precipitation_sum = daily.Variables(0).ValuesAsNumpy()

daily_data = {"date": pd.date_range(
	start = pd.to_datetime(daily.Time(), unit = "s", utc = True),
	end = pd.to_datetime(daily.TimeEnd(), unit = "s", utc = True),
	freq = pd.Timedelta(seconds = daily.Interval()),
	inclusive = "left"
)}

daily_data["precipitation_sum"] = daily_precipitation_sum

daily_dataframe = pd.DataFrame(data = daily_data)
print(daily_dataframe) # example of printing just one value: print(daily_dataframe["precipitation_sum"])

### --------------------- Message Logic ---------------------- ###
# LOGIC # - OPTIMIZE LATER - # - Set up in different File later -
num_days = 0
water_msg_init = f"""\
    It rained {(daily_precipitation_sum[0] + daily_precipitation_sum[1]):2f} inches per sq ft. within the past 2 days. 
    
    NO NEED to water."""
inches_limit = 0.9

for x in daily_dataframe["precipitation_sum"]:
    if x >= inches_limit and x == daily_precipitation_sum[1]: # 1 day ago
        # x == ... means that x matches the SECOND entry
        num_days = 1
        print(water_msg_init)
        exit
    elif x >= inches_limit: # 2 days ago
        num_days = 2
        print(water_msg_init)
        exit
    elif daily_precipitation_sum[0] < inches_limit and daily_precipitation_sum[1] < inches_limit:
        water_msg_init = f"""\
            It rained {(daily_precipitation_sum[0] + daily_precipitation_sum[1]):2f} inches per sq ft over the past 2 days.

            It's time to water some plants!
            """
        print(water_msg_init) # not enough water for the last 2 days
        exit

### --------------------- SMTP/Email stuff ---------------------- ###
# EMAIL SETUP # - Set up as a class? in different File later -
	# requires "import smtplib" applied to top of script

port = 587  # For starttls
smtp_server = "smtp.gmail.com"
sender_email = "gardeningreminderbot@gmail.com"
receiver_email = "" #INSERT EMAIL
app_password = "" #INSERT SENDERS APP PASSWORD ### !!! Make secure later!!! ###
message = f"""\
Subject: Precipitation Report

Hello and good morning!

{water_msg_init}

This message was sent from Python."""

try:
    server = smtplib.SMTP(smtp_server, port)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(sender_email, app_password)
    server.sendmail(sender_email, receiver_email, message)
except Exception as e:
    # prints errors
    print(e)
finally:
    server.quit()
