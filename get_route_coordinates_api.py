import requests
import polyline
from math import radians, sin, cos, sqrt, atan2
from flask import Flask, request, jsonify
import psycopg2
from shapely.geometry import box


app = Flask(__name__)

db_connection = psycopg2.connect(
    database='your_database_name',
    user='your_username',
    password='your_password',
    host='your_host',
    port='your_port'
)


def haversine(lat1, lon1, lat2, lon2):
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Radius of the Earth in kilometers
    radius = 6371.0

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = radius * c

    return distance
def get_route_coordinates(origin, destination, api_key, mode = 'transit', distance_interval = 10):
    url = f'https://maps.googleapis.com/maps/api/directions/json'
    params = {
        'origin': origin,
        'destination': destination,
        'key': api_key,
        'mode': mode
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


@app.route('/get_route', methods=['GET'])
def get_route():
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    mode = request.args.get('mode', 'transit')
    distance_interval = float(request.args.get('distance_interval', 5))

    api_key = 'AIzaSyCtPeBlGL_cmAUcc8ljVyB-hzwFTB4ofmU'

    route_coordinates = get_route_coordinates(origin, destination, api_key, mode, distance_interval)
    envelopes = []

    cursor = db_connection.cursor()

    for i in range(len(route_coordinates) - 1):
        current_latitude, current_longitude = route_coordinates[i]
        next_latitude, next_longitude = route_coordinates[i + 1]

        envelope = box(min(current_longitude, next_longitude), min(current_latitude, next_latitude),
                       max(current_longitude, next_longitude), max(current_latitude, next_latitude))

        envelopes.append(envelope)

        query = f'SELECT * FROM your_table WHERE ST_Within(your_geometry_column, {envelope});'

        results = cursor.execute(query)

    db_connection.commit()

    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True, port='80', host='0.0.0.0')
