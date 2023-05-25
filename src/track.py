import os
import gpxpy
import json
from geopy.distance import geodesic
import numpy as np

from globals import GPX_DIR

print(GPX_DIR)
TDS_GPX = os.path.join(GPX_DIR, "TDS.gpx")
TDS_JSON = os.path.join(GPX_DIR, "TDS.json")


def read_gpx_file(file_path):
    with open(file_path, "r") as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    return gpx


def extract_track_points(gpx):
    track_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                track_points.append([point.latitude, point.longitude])
    return track_points


def save_track_to_json(track_points, file_path):
    with open(file_path, "w") as json_file:
        json.dump(track_points, json_file, indent=2)


# gpx = read_gpx_file(TDS_GPX)
# track_points = extract_track_points(gpx)
# save_track_to_json(track_points, TDS_JSON)


def find_distance_along_track(gpx_track, rider_coords):
    closest_point = min(
        gpx_track, key=lambda point: geodesic(rider_coords, point).meters
    )
    closest_point_index = np.where((gpx_track == closest_point).all(axis=1))[0][0]

    track_distance = 0.0
    for i in range(closest_point_index):
        point1 = gpx_track[i]
        point2 = gpx_track[i + 1]
        distance = geodesic(point1, point2).kilometers
        track_distance += distance

    return track_distance


TEST_COORDS1 = [58.66558065110315, 31.49214988582637]
TEST_COORDS2 = [58.65483713902874, 31.74333683284003]
TEST_COORDS3 = [58.50183495038282, 31.6049256226557]
TEST_COORDS4 = [58.57649711857753, 31.44184256669087]
TEST_COORDS5 = [58.64171097461575, 31.44218705453459]

TEST_COORDS = [TEST_COORDS1, TEST_COORDS2, TEST_COORDS3, TEST_COORDS4, TEST_COORDS5]


gpx_json = json.load(open(TDS_JSON))
gpx_track = np.array(gpx_json)

for test_coords in TEST_COORDS:
    distance = find_distance_along_track(gpx_track, test_coords)
    print(distance)
