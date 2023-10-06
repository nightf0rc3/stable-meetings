from math import radians, sin, cos, sqrt, atan2
from os.path import expanduser

import polyline
import psycopg2
import requests
from flask import Flask

sql_query_template_wifi = """
WITH Distances AS (
  SELECT
    coords.input_latitude,
    coords.input_longitude,
    wifi.latitude AS wifi_latitude,
    wifi.longitude AS wifi_longitude,
    wifi.download,
    wifi.upload,
    wifi.link_ping,
    SQRT(
      POW(69.1 * (wifi.latitude - coords.input_latitude), 2) +
      POW(69.1 * (coords.input_longitude - wifi.longitude) * COS(wifi.latitude / 57.3), 2)
    ) AS distance
  FROM wifi_on_ice_cleaned_final AS wifi
  CROSS JOIN LATERAL (VALUES
    (50.95729, 7.01305),
(51.00055, 7.01854),
(51.04609, 7.01251),
(51.09114, 7.00869),
(51.13501, 6.99893),
(51.17963, 7.00155),
(51.21446, 7.01899),
(51.23683, 7.07899),
(51.25181, 7.14207),
(51.27079, 7.20593),
(51.28691, 7.27366),
(51.29948, 7.34059),
(51.33176, 7.38092),
(51.35075, 7.44631),
(51.38893, 7.44692),
(51.39037, 7.38108),
(51.42616, 7.34943),
(51.46355, 7.32165),
(51.49746, 7.36559),
(51.51008, 7.42963)
  ) AS coords(input_latitude, input_longitude)
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
    coords.input_latitude,
    coords.input_longitude,
    SQRT(
      POW(69.1 * (celltowers.latitude - coords.input_latitude), 2) +
      POW(69.1 * (coords.input_longitude - celltowers.longitude) * COS(celltowers.latitude / 57.3), 2)
    ) AS distance
  FROM (
    SELECT input_latitude, input_longitude
    FROM (VALUES (50.95984, 7.01442),
(51.00322, 7.01859),
(51.04797, 7.01217),
(51.09361, 7.00816),
(51.1375, 6.99958),
(51.1838, 6.99984),
(51.2151, 7.02575),
(51.23943, 7.0848),
(51.25424, 7.14801),
(51.27288, 7.21322),
(51.2889, 7.28069),
(51.30441, 7.34367),
(51.33362, 7.38767),
(51.35285, 7.45282),
(51.38971, 7.43976),
(51.4198, 7.44501),
(51.45698, 7.44532),
(51.49044, 7.45477)) AS coords(input_latitude, input_longitude)
  ) AS coords
  JOIN celltowers
  ON true  -- This is used to create a Cartesian product without a CROSS JOIN
  WHERE celltowers.radio != 'GSM'
  AND celltowers.radio != 'UMTS'
  AND celltowers.mcc = 262
  AND mnc IN (1, 2, 3, 7, 8, 9, 10, 12, 16, 20, 43)
) AS Distances
GROUP BY input_latitude, input_longitude
ORDER BY input_latitude, input_longitude;
"""

app = Flask(__name__)

home = expanduser('~')
# if you want to use ssh password use - ssh_password='your ssh password', bellow

sql_username = 'postgres'
sql_password = 'postgres'
sql_main_database = 'postgres'

conn = psycopg2.connect(
    database='postgres',
    user='postgres',
    password='postgres',
    host='database-1.c18atxd28p1u.eu-central-1.rds.amazonaws.com',
    port=5432
)


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

        results_wifi = cursor.fetchall()  # Use fetchall() to get all results

        print(results_wifi)

        cursor.execute(sql_query_cell)
        conn.commit()

        results_cell = cursor.fetchall()  # Use fetchall() to get all results

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
