import requests
import pandas as pd
from pandas import json_normalize
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

auth_url = "https://www.strava.com/oauth/token"
activities_url = "https://www.strava.com/api/v3/athlete/activities"

payload = {
    'client_id': "108066",
    'client_secret': '180ed4c95ebaa767b36e50d66beca4cd3c65e4fe',
    'refresh_token': 'f628bd884169671b69d2a2c7bbd4e4cdb4296bf4',
    'grant_type': "refresh_token",
    # 'code': 'va86e9e25ce2a2d1021964eb54eb0047b5bd81457',
    'f': 'json'
}

print("Requesting Token...\n")
res = requests.post(auth_url, data=payload, verify=False)
access_token = res.json()['access_token']
print("Access Token = {}\n".format(access_token))

header = {'Authorization': 'Bearer ' + access_token}
param = {'per_page': 200, 'page': 1}
strava_activities_data = requests.get(activities_url, headers=header, params=param).json()

# JSON data to flat table
activities = json_normalize(strava_activities_data)

if "activities" in locals(): print("Requested data.\n")

# Seaborn is a data visualization library.
import seaborn as sns
# Matplotlib is a data visualization library. 
# Seaborn is actually built on top of Matplotlib. 
import matplotlib.pyplot as plt
# Numpy will help us handle some work with arrays.
import numpy as np
# Datetime will allow Python to recognize dates as dates, not strings.
from datetime import datetime
import numpy as np
import time
import matplotlib.pyplot as plt
import folium
import polyline
import base64
from tqdm import tqdm

# Create new df with relevant columns
# cols = ['name', 'upload_id', 'type', 'distance', 'moving_time',   
#         'average_speed', 'max_speed','total_elevation_gain',
#         'start_date_local', 'map.summary_polyline'
#       ]
# activities = activities[cols]

# break date into start time and date
activities['start_date_local'] = pd.to_datetime(activities['start_date_local'])
activities['start_time'] = activities['start_date_local'].dt.time
activities['start_date_local'] = activities['start_date_local'].dt.date

# switch speed to km/h
activities['average_speed_kmh'] = activities['average_speed'] * 3.6
activities['average_speed_mph'] = activities['average_speed'] * 2.237

# add decoded summary polylines
activities['map.polyline'] = activities['map.summary_polyline'].apply(polyline.decode)

# define function to get elevation data using the open-elevation API
# def get_elevation(latitude, longitude):
#     base_url = 'https://api.open-elevation.com/api/v1/lookup'
#     payload = {'locations': f'{latitude},{longitude}'}
#     r = requests.get(base_url, params=payload).json()['results'][0]
#     return r['elevation']

# # get elevation data
# elevation_data = list()
# for idx in tqdm(activities.index):
#     activity = activities.loc[idx, :]
#     elevation = [get_elevation(coord[0], coord[1]) for coord in activity['map.polyline']]
#     elevation_data.append(elevation)
# # add elevation data to dataframe
# activities['map.elevation'] = elevation_data

# drop irrelevant columns
activities.drop(
    [
        'map.summary_polyline', 'resource_state','external_id','upload_id',
        'location_city', 'location_state', 'has_kudoed', 'start_date', 'athlete.resource_state', 
        'utc_offset','map.resource_state', 'athlete.id', 'visibility', 'heartrate_opt_out', 'upload_id_str',
        'from_accepted_tag', 'map.id', 'manual', 'private', 'flagged',
    ], 
    axis=1, 
    inplace=True
)

# separate out activities of interest
# runs = activities.loc[activities['type'] == 'Run']

rides = activities.loc[activities['type'] == 'Ride']
rides = rides.loc[rides['max_speed'] > 0] # only rides with max speed > 0 (because they also have gps data)

# set index based on start date
rides.set_index('start_date_local', inplace=True)

# plot map
which_ride = 'last'
# select one activity
if which_ride == 'longest':
    my_ride = rides[rides.distance == rides.distance.max()].squeeze() # longest ride
elif which_ride == 'last':
    my_ride = rides.iloc[0, :] # first activity (most recent)

# plot ride on map
centroid = [ # center get coordinate
    np.mean([coord[0] for coord in my_ride['map.polyline']]),  #[0]
    np.mean([coord[1] for coord in my_ride['map.polyline']]) #[0]
]
ride_map = folium.Map(location=centroid, zoom_start=10)
folium.PolyLine(my_ride['map.polyline'], color='red').add_to(ride_map) # add route as layer
ride_map.fit_bounds(ride_map.get_bounds(), padding=(20, 20)) # zoom in to route
display(ride_map)

ride_map.save("ride_map.html")



