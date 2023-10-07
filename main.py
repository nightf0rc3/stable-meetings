from math import radians, sin, cos, sqrt, atan2
import geopandas
import pandas as pd
from shapely import wkt
from shapely.geometry import Point
import polyline
import psycopg2
import requests
from flask import Flask, request, jsonify, render_template
from flask import send_from_directory
from ics import Calendar, Event

sql_query_template_cell = """
SELECT
  input_latitude,
  input_longitude,
  CASE WHEN MIN(distance) < 3000 THEN TRUE ELSE FALSE END AS tower_within_3000
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
    FROM (VALUES {coordinate_values}) AS coords(input_latitude, input_longitude)
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

app = Flask(__name__, static_folder='dist')


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


def get_connection_level(waypoints):
    waypoint_coords = []
    for w in waypoints:
        waypoint_coords.append(Point(w[0], w[1]))
    points_layer = geopandas.GeoDataFrame(geometry=waypoint_coords)
    subset = geopandas.sjoin(df, points_layer, how='right', predicate='contains')
    subset['latitude'] = subset.geometry.x
    subset['longitude'] = subset.geometry.y
    subset = subset.drop(["geometry", "index_left"], axis=1)
    subset.loc[subset.upload_over_recommend == 1, 'quality_level'] = True
    subset.loc[subset.upload_under_recommend == 1, 'quality_level'] = False
    lats = subset.latitude.to_list()
    longs = subset.longitude.to_list()
    quality_level = subset.quality_level.to_list()
    output = {"meta": {}, "source": {}}
    data = []
    for index in range(0, len(lats)):
        data.append({"lat": lats[index], "lng": longs[index], "quality": quality_level[index]})
    output["source"] = data
    return output


@app.route('/get_route', methods=['GET'])
def get_route():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    mode = request.args.get('mode', 'transit')
    distance_interval = float(request.args.get('distance_interval', 5))

    api_key = 'AIzaSyCtPeBlGL_cmAUcc8ljVyB-hzwFTB4ofmU'

    route_coordinates = get_route_coordinates(origin, destination, api_key, mode, int(distance_interval))

    wifi_ice_results = get_connection_level(route_coordinates)

    for item in wifi_ice_results['source']:
        if item['quality'] is False:
            item['quality'] = 0
        elif item['quality'] is True:
            item['quality'] = 2

    print(wifi_ice_results)
    print(len(wifi_ice_results))

    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(
            database='postgres',
            user='postgres',
            password='postgres',
            host='database-2.c18atxd28p1u.eu-central-1.rds.amazonaws.com',
            port=5432
        )
        cursor = conn.cursor()

        coordinates_tuples = [(item['lat'], item['lng']) for item in wifi_ice_results['source']]
        coordinates_string = ','.join(['({}, {})'.format(lat, lng) for lat, lng in coordinates_tuples])
        print(len(coordinates_string))
        sql_query_cell = sql_query_template_cell.format(coordinate_values=coordinates_string)

        print(sql_query_cell)

        cursor.execute(sql_query_cell)
        conn.commit()

        results_cell = cursor.fetchall()
        # print(results_cell)
        print("New")

        for wifi_item in wifi_ice_results['source']:
            wifi_quality = wifi_item['quality']
            db_quality = results_cell[wifi_ice_results['source'].index(wifi_item)][2]

            if wifi_quality == 0 and db_quality:
                wifi_item['quality'] = 1

        print(wifi_ice_results)

        return wifi_ice_results

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@app.route('/demo', methods=['GET'])
def greet():
    response = send_from_directory(app.static_folder, 'indexDemo.html')
    # Remove Content-Security-Policy header
    response.headers.pop('Content-Security-Policy', None)
    # Allow the site to be framed from any origin (not recommended!)
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    # Disable XSS protection in browsers (not recommended!)
    response.headers['X-XSS-Protection'] = '0'
    # Disable content type sniffing (not recommended!)
    response.headers['X-Content-Type-Options'] = 'none'
    return response


@app.route('/getGeo', methods=['GET'])
def greet_me():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    mode = request.args.get('mode', 'transit')
    distance_interval = float(request.args.get('distance_interval', 5))

    api_key = 'AIzaSyCtPeBlGL_cmAUcc8ljVyB-hzwFTB4ofmU'

    route_coordinates = get_route_coordinates(origin, destination, api_key, mode, int(distance_interval))

    wifi_ice_results = get_connection_level(route_coordinates)

    for item in wifi_ice_results['source']:
        if item['quality'] is False:
            item['quality'] = 0
        elif item['quality'] is True:
            item['quality'] = 2

    print(wifi_ice_results)
    print(len(wifi_ice_results))

    conn = psycopg2.connect(
        database='postgres',
        user='postgres',
        password='postgres',
        host='database-2.c18atxd28p1u.eu-central-1.rds.amazonaws.com',
        port=5432
    )
    cursor = conn.cursor()

    coordinates_tuples = [(item['lat'], item['lng']) for item in wifi_ice_results['source']]
    coordinates_string = ','.join(['({}, {})'.format(lat, lng) for lat, lng in coordinates_tuples])
    print(len(coordinates_string))
    sql_query_cell = sql_query_template_cell.format(coordinate_values=coordinates_string)

    print(sql_query_cell)

    cursor.execute(sql_query_cell)
    conn.commit()

    results_cell = cursor.fetchall()
    # print(results_cell)
    print("New")

    for wifi_item in wifi_ice_results['source']:
        wifi_quality = wifi_item['quality']
        db_quality = results_cell[wifi_ice_results['source'].index(wifi_item)][2]

        if wifi_quality == 0 and db_quality:
            wifi_item['quality'] = 1

    for item in wifi_ice_results['source']:
        if pd.isna(item['quality']):
            item['quality'] = 0

    response = render_template('indexDemo.html', geolist=wifi_ice_results['source'])
    # Remove Content-Security-Policy header
    # response.headers.pop('Content-Security-Policy', None)
    # Allow the site to be framed from any origin (not recommended!)
    # response.headers['X-Frame-Options'] = 'ALLOWALL'
    # Disable XSS protection in browsers (not recommended!)
    # response.headers['X-XSS-Protection'] = '0'
    # Disable content type sniffing (not recommended!)
    # response.headers['X-Content-Type-Options'] = 'none'
    return response


@app.route('/events', methods=['GET'])
def get_events():
    url = "https://calendar.google.com/calendar/ical/5b984078298d4206ec1cb83f14314d7ba64fbb486bdde6bb3ef18cd0776e18b7%40group.calendar.google.com/public/basic.ics"
    response = requests.get(url)
    cal = Calendar(response.text)
    events_list = []
    for event in cal.events:
        events_list.append({
            "name": event.name,
            "begin": str(event.begin)
        })
    return jsonify(events_list)


@app.route('/getDemo', methods=['GET'])
def greetTheDemo():
    origin = 'Berlin, Germany'
    destination = 'Dortmund, Germany'
    responseObj = get_route(origin, destination)
    return str(responseObj)


if __name__ == '__main__':
    df = pd.read_csv("wifi_on_ice_griddata_2000kilobit.csv")
    df['geometry'] = df['geometry'].apply(wkt.loads)
    df = geopandas.GeoDataFrame(df, geometry=df.geometry)
    app.run(host='0.0.0.0', port=80)
