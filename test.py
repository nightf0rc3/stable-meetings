from math import radians, sin, cos, sqrt, atan2
from os.path import expanduser

import polyline
import psycopg2
import requests
from flask import Flask


sql_query_template_wifi = """
WITH Distances AS (
  SELECT
    wifi.latitude AS wifi_latitude,
    wifi.longitude AS wifi_longitude,
    wifi.download,
    wifi.upload,
    wifi.link_ping,
    SQRT(
      POW(69.1 * (wifi.latitude - input_latitude), 2) +
      POW(69.1 * (input_longitude - wifi.longitude) * COS(input_latitude / 57.3), 2)
    ) AS distance
  FROM wifi_on_ice_cleaned_final AS wifi
  WHERE (wifi.latitude, wifi.longitude) IN ({coordinate_values})
)
SELECT
  input_latitude,
  input_longitude,
  wifi_latitude,
  wifi_longitude,
  download,
  upload,
  link_ping,
  MIN(distance) AS nearest_distance
FROM Distances
GROUP BY input_latitude, input_longitude, wifi_latitude, wifi_longitude, download, upload, link_ping
ORDER BY input_latitude, input_longitude, nearest_distance;
"""

sql_query_template_cell = """
SELECT
  input_latitude,
  input_longitude,
  CASE WHEN MIN(distance) < 5000 THEN TRUE ELSE FALSE END AS tower_within_5000
FROM (
  SELECT
    SQRT(
      POW(69.1 * (celltowers.latitude - input_latitude), 2) +
      POW(69.1 * (input_longitude - celltowers.longitude) * COS(celltowers.latitude / 57.3), 2)
    ) AS distance
  FROM celltowers
  WHERE celltowers.radio != 'GSM'
  AND celltowers.radio != 'UMTS'
  AND celltowers.mcc = 262
  AND mnc IN (1, 2, 3, 7, 8, 9, 10, 12, 16, 20, 43)
  AND (celltowers.latitude, celltowers.longitude) IN ({coordinate_values})
) AS Distances
GROUP BY input_latitude, input_longitude
ORDER BY input_latitude, input_longitude;
"""

app = Flask(__name__)

def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Radius of the Earth in kilometers
    radius = 6371.0

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = radius * c

    return distance


def get_route_coordinates(origin, destination, api_key, mode='transit', distance_interval=10):
    url = f'https://maps.googleapis.com/maps/api/directions/json'

    params = {
        'origin': origin,
        'destination': destination,
        'key': api_key,
        'mode': mode,
        'alternatives': 'true'
    }
    response = requests.get(url, params=params)

    data = response.json()
    coordinates = []
    if 'routes' in data and data['routes']:
        route = data['routes'][0]
        for leg in route['legs']:
            for step in leg['steps']:
                points = polyline.decode(step['polyline']['points'])
                coordinates.extend(points)
    total_distance = 0
    previous_point = None
    filtered_coordinates = []

    for point in coordinates:
        if previous_point is not None:
            distance = haversine(previous_point[0], previous_point[1], point[0], point[1])
            total_distance += distance

            if total_distance >= distance_interval:
                filtered_coordinates.append(point)
                total_distance = 0  # Reset the accumulated distance

        previous_point = point

    return filtered_coordinates


def get_route(origin, destination):
    distance_interval = 5
    mode = 'transit'
    api_key = 'AIzaSyCtPeBlGL_cmAUcc8ljVyB-hzwFTB4ofmU'

    route_coordinates = get_route_coordinates(origin, destination, api_key, mode, distance_interval)

    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            database='postgres',
            user='postgres',
            password='postgres',
            host='database-1.c18atxd28p1u.eu-central-1.rds.amazonaws.com',
            port=5432
        )
        cursor = conn.cursor()

        coordinate_values = ",\n".join(["({}, {})".format(coord[0], coord[1]) for coord in route_coordinates])
        sql_query_wifi = sql_query_template_wifi.format(coordinate_values=coordinate_values)
        sql_query_cell = sql_query_template_cell.format(coordinate_values=coordinate_values)

        print(sql_query_wifi)

        cursor.execute(sql_query_wifi)
        conn.commit()

        results_wifi = cursor.fetchall()

        print(results_wifi)

        cursor.execute(sql_query_cell)
        conn.commit()

        results_cell = cursor.fetchall()

        print(results_cell)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


origin = 'Köln, Germany'
destination = 'Dortmund, Germany'
get_route(origin, destination)
