import requests
import polyline
from math import radians, sin, cos, sqrt, atan2
from flask import Flask, request, jsonify

app = Flask(__name__)

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

    return jsonify(route_coordinates)

@app.route('/test', methods=['GET'])
def test():
    return 'Test Successful'


if __name__ == '__main__':
    app.run(debug=True, port=80)
