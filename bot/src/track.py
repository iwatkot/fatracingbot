import os
import gpxpy
import dropbox
import folium
import json
from geopy.distance import geodesic
from aiocron import crontab

# from git import Repo
import numpy as np

import globals as g

logger = g.Logger(__name__)


async def download_gpx():
    logger.info("Trying to download GPX files from Dropbox dir '/tracks'.")
    files = g.DBX.files_list_folder("/tracks").entries

    logger.info(f"Found {len(files)} files in '/tracks'")

    for entry in files:
        if isinstance(entry, dropbox.files.FileMetadata):
            g.DBX.files_download_to_file(
                os.path.join(g.TRACKS_DIR, entry.name), f"/tracks/{entry.name}"
            )

    gpx_files = [file for file in os.listdir(g.TRACKS_DIR) if file.endswith(".gpx")]

    logger.info(f"Succesfully downloaded {len(gpx_files)} GPX files: {gpx_files}")

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
    gpx_file_path = os.path.join(g.TRACKS_DIR, gpx_file_name)
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

    try:
        os.remove(gpx_file_path)
    except Exception:
        pass

    return json_file_path


def track_distance(track, coordinates):
    track = np.array(track)
    closest_point = min(track, key=lambda point: geodesic(coordinates, point).meters)

    closest_point_index = np.where((track == closest_point).all(axis=1))[0][0]

    logger.debug(f"Closest point on track for {coordinates} is {closest_point}.")

    track_distance = 0.0
    for i in range(closest_point_index):
        point1 = track[i]
        point2 = track[i + 1]
        distance = geodesic(point1, point2).kilometers
        track_distance += distance

    logger.debug(f"Distance along track for {coordinates} is {track_distance} km.")

    return round(track_distance, 2)


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

    m = folium.Map(location=location, zoom_start=13)

    folium.PolyLine(track).add_to(m)

    raw_leaderboard = []

    for telegram_id, user_info in g.AppState.Race.location_data.items():
        description = (
            f"<b>Имя:</b> {user_info['full_name']}<br>"
            f"<b>Категория:</b> {user_info['category']}<br>"
            f"<b>Номер:</b> {user_info['race_number']}\n"
        )

        coordinates = user_info["coordinates"]

        folium.Marker(
            location=coordinates,
            popup=folium.Popup(html=description, max_width=300),
            icon=folium.Icon(icon="glyphicon glyphicon-record", color="red"),
        ).add_to(m)

        logger.debug(f"Added marker for {user_info['full_name']}.")

        distance = track_distance(track, coordinates)
        leaderboard_entry = user_info.copy()
        leaderboard_entry["distance"] = distance

        raw_leaderboard.append(leaderboard_entry)

        logger.debug(
            f"Added {user_info['full_name']} to leaderboard with distance {distance}."
        )

    map_save_path = os.path.join(g.STATIC_DIR, f"{race_code}_map.html")

    m.save(map_save_path)

    logger.debug(
        f"Map created, added {len(g.AppState.Race.location_data)} markers. Saved to {map_save_path}."
    )

    await build_leaderboard(raw_leaderboard)


async def build_leaderboard(raw_leaderboard):
    if not g.AppState.Race.info:
        return

    raw_leaderboard = sorted(raw_leaderboard, key=lambda x: x["distance"], reverse=True)

    logger.debug(f"Sorted leaderboard data with {len(raw_leaderboard)} entries.")

    leaderboard = []
    for idx, entry in enumerate(raw_leaderboard):
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
