import os
import gpxpy
import folium
import json
from geopy.distance import geodesic
from aiocron import crontab
from git import Repo
import numpy as np

import globals as g

logger = g.Logger(__name__)


async def download_gpx():
    logger.info(f"Trying to download files from github repo {g.REPO_URL}.")

    try:
        Repo.clone_from(g.REPO_URL, g.GH_DIR)
        logger.info("GH directory cloned.")
    except Exception:
        repo = Repo(g.GH_DIR)
        repo.remotes.origin.pull()
        logger.info("GH directory wasn't empty, pulled changes.")

    gpx_files = [file for file in os.listdir(g.GH_DIR) if file.endswith(".gpx")]
    logger.info(f"GH directory contains following GPX files: {gpx_files}")
    return gpx_files


async def prepare_json_tracks():
    gpx_files = await download_gpx()
    race_codes = [file.split(".")[0] for file in gpx_files]

    logger.info(
        f"Found GPX files with following race codes: {race_codes}, starting conversion to JSON."
    )

    for race_code in race_codes:
        await gpx_to_json(race_code)

    logger.info("All GPX files converted to JSON.")

    return race_codes


async def gpx_to_json(race_code) -> str | None:
    gpx_file_name = f"{race_code}.gpx"
    json_file_name = f"{race_code}.json"
    gpx_file_path = os.path.join(g.GH_DIR, gpx_file_name)
    json_file_path = os.path.join(g.TRACKS_DIR, json_file_name)

    if not os.path.exists(gpx_file_path):
        logger.error(f"GPX file {gpx_file_path} does not exist.")
        return

    with open(gpx_file_path) as gpx_file:
        gpx = gpxpy.parse(gpx_file)

    logger.info(f"GPX file {gpx_file_name} parsed.")

    track_points = []
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                track_points.append([point.latitude, point.longitude])

    logger.info(f"Track points extracted from {gpx_file_name}.")

    with open(json_file_path, "w") as json_file:
        json.dump(track_points, json_file, indent=2)

    logger.info(f"Track points saved to {json_file_name}.")

    return json_file_path


def track_distance(track, coordinates):
    track = np.array(track)
    closest_point = min(track, key=lambda point: geodesic(coordinates, point).meters)

    closest_point_index = np.where((track == closest_point).all(axis=1))[0][0]

    logger.debug(f"Closest point on track for {coordinates} is {closest_point}.")

    distance = 0.0
    for i in range(closest_point_index):
        point1 = track[i]
        point2 = track[i + 1]
        distance = geodesic(point1, point2).kilometers
        distance += distance

    logger.debug(f"Distance along track for {coordinates} is {distance} km.")

    return round(distance, 2)


@crontab(g.MAP_TICKRATE)
async def race_map_create():
    logger.debug("Crontab rule for race map creation triggered.")

    if not (g.AppState.Race.info and g.AppState.Race.ongoing):
        logger.debug("There's no active race at the moment.")
        return

    if not g.AppState.Race.location_data:
        logger.debug("Race is active, but no location data received yet.")
        return

    location = g.AppState.Race.info.location
    race_code = g.AppState.Race.info.code

    logger.info(f"Active race with code: {race_code}")

    track_json_path = os.path.join(g.TRACKS_DIR, f"{race_code}.json")
    if not os.path.exists(track_json_path):
        logger.error(f"Can't find JSON file with track data in path: {track_json_path}")
        return

    with open(track_json_path, "r") as json_file:
        track = json.load(json_file)

    logger.debug(f"Loaded track with {len(track)} points from JSON file.")

    m = folium.Map(location=location, zoom_start=10)

    folium.PolyLine(track).add_to(m)

    g.AppState.Race.leaderboard = []

    for telegram_id, user_data in g.AppState.Race.location_data.items():
        description = (
            f"<b>Имя:</b> {user_data['full_name']}<br>"
            f"<b>Категория:</b> {user_data['category']}<br>"
            f"<b>Номер:</b> {user_data['race_number']}\n"
        )

        folium.Marker(
            location=user_data["coordinates"],
            popup=folium.Popup(html=description, max_width=300),
            icon=folium.Icon(icon="glyphicon glyphicon-record", color="red"),
        ).add_to(m)

        logger.debug(f"Added marker for {user_data['full_name']}.")

        coordinates = user_data["coordinates"]
        distance = track_distance(track, coordinates)
        leaderboard_entry = user_data.copy()
        leaderboard_entry["distance"] = distance

        g.AppState.Race.leaderboard.append(leaderboard_entry)

        logger.debug(
            f"Added {user_data['full_name']} to leaderboard with distance {distance}."
        )

    map_save_path = os.path.join(g.STATIC_DIR, f"{race_code}_map.html")

    m.save(map_save_path)

    logger.debug(
        f"Map created, added {len(g.AppState.Race.location_data)} markers. Saved to {map_save_path}."
    )

    await build_leaderboard()


async def build_leaderboard():
    if not (g.AppState.Race.leaderboard and g.AppState.Race.info):
        return

    leaderboard_data = sorted(g.AppState.Race.leaderboard, key=lambda x: x["distance"])

    logger.debug(f"Sorted leaderboard data with {len(leaderboard_data)} entries.")

    leaderboard = []
    for idx, entry in enumerate(leaderboard_data):
        leaderboard.append(
            {
                "row_number": idx + 1,
                "distance": f'{entry["distance"]} км',
                "category": entry["category"],
                "race_number": entry["race_number"],
                "full_name": entry["full_name"],
            }
        )

    logger.debug(f"Built leaderboard with {len(leaderboard)} entries.")

    race_code = g.AppState.Race.info.code
    json_path = os.path.join(g.JSON_DIR, f"{race_code}_leaderboard_all.json")

    with open(json_path, "w") as json_file:
        json.dump(leaderboard, json_file, indent=2)

    logger.info(f"Leaderboard saved to {json_path}.")
