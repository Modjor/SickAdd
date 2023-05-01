#!/usr/bin/env python
#
##################################################################################
### SickAdd V3  - THIS IS AN ALPHA RELEASE
#
# This script downloads your IMDB favorites and add them to your SickBeard shows
#
# NOTE: This script requires Python to be installed on your system
#
#
# Changelog
# Version 3.1
# Supports imdb list with over 100 items
#
# Version 3.0
# Full rewrite, now supports multiple imdb watchlist to be monitored, various command line argument including browsing &
# deleting items from the sqlite db
#
# Version 2.1
# Minor Bug correction around TVDB url / IMDB mapping)
#
# Version 2
# - Add IMDB Watch list support (using IMDB Mapping from TVDB)
# - Add a Debug mode so it's a bit less verbose in standard mode
#
##################################################################################


# Settings
settings = {
    "watchlist_urls": [
        "https://www.imdb.com/list/lsxxxxxxxx", "https://www.imdb.com/list/lsxxxxxxxxxx"
    ],
    "sickchill_url": "http://sickchill_ip:8081",
    "sickchill_api_key": "your_sickchill_api_key",
    "debug": 1,
}

#########    NO MODIFICATION UNDER THAT LINE
##########################################################

import sys
import argparse
import sqlite3
import requests
from bs4 import BeautifulSoup
import json
# import re
# import os
from datetime import datetime



# Debug function
def debug_log(message):
    if settings["debug"]:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        with open("debug.log", "a") as log_file:
            log_file.write(f"[{timestamp}] {message}\n")

# Check if IMDB Watchlists are reachable
def check_watchlists():
    # Create a list to store unreachable watchlists
    unreachable_watchlists = []

    # Create a list to store reachable watchlists
    reachable_watchlists = []

    for url in settings["watchlist_urls"]:
        response = requests.get(url)
        if response.status_code == 200:
            reachable_watchlists.append(url)
        else:
            unreachable_watchlists.append(url)

    # Log unreachable watchlists in debug mode
    if unreachable_watchlists:
        debug_log(f"Unreachable IMDb watchlists: {', '.join(unreachable_watchlists)}")

    # Log reachable watchlists in debug mode
    if reachable_watchlists:
        debug_log(f"Reachable IMDb watchlists: {', '.join(reachable_watchlists)}")

    # Check if the count of reachable watchlists is 0. If so, stop the script.
    if len(reachable_watchlists) == 0:
        print("Error: None of the IMDb watchlists are reachable.")
        sys.exit(1)

    debug_log("IMDb watchlists check completed.")

# Check if SickChill is reachable
def check_sickchill():
    url = f"{settings['sickchill_url']}/api/{settings['sickchill_api_key']}/?cmd=shows"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error: SickChill is not reachable.")
        sys.exit(1)
    debug_log("SickChill is reachable.")


# Check if TheTVDB is reachable
def check_thetvdb():
    url = "https://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=tt0257315"
    debug_log("Testing TheTVDB availability at URL: " + url)
    response = requests.get(url)
    if response.status_code != 200:
        debug_log("Error during TheTVDB availability test at URL: " + url)
        debug_log("Response: " + str(response.status_code) + " - " + response.text)
        print("Error: TheTVDB is not reachable.")
        sys.exit(1)
    else:
        debug_log("TheTVDB is reachable.")
  


# Create or connect to SQLite database
def setup_database():
    conn = sqlite3.connect("sickadd.db")
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS shows (
            imdb_id TEXT PRIMARY KEY,
            title TEXT,
            watchlist_url TEXT,
            imdb_import_date TEXT,
            added_to_sickchill INTEGER,
            thetvdb_id INTEGER,
            sc_added_date TEXT
        )
        """
    )
    conn.commit()
    return conn, cur

# Get IMDb watchlists and extract series
def get_imdb_watchlist_series():
    series_list = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Accept-Language": "en-US"
    }
    for url in settings["watchlist_urls"]:
        debug_log(f"Fetching IMDb watchlist: {url}")
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        series_items = soup.find_all("div", class_="lister-item mode-detail")
        debug_log(f"Number of series found in the watchlist: {len(series_items)}")
        for item in series_items:
            imdb_id = item.find("div", class_="ribbonize")["data-tconst"]
            title = item.find("h3", class_="lister-item-header").find("a").text
            imdb_url = f"https://www.imdb.com/title/{imdb_id}/"
            imdb_response = requests.get(imdb_url, headers=headers)
            imdb_soup = BeautifulSoup(imdb_response.text, "html.parser")
            title_tag = imdb_soup.find("title")

            if title_tag and "TV Series" in title_tag.text:
                series_list.append({
                    "imdb_id": imdb_id,
                    "title": title,
                    "watchlist_url": url,
                })
                debug_log(f"TV Series detected: {title} ({imdb_id})")
            else:
                debug_log(f"Ignored item (not a TV series): {title}")
    debug_log(f"Total series fetched: {len(series_list)}")
    return series_list


# Insert series into SQLite database
def insert_series_to_db(conn, cur, series_list):
    for series in series_list:
        cur.execute("SELECT * FROM shows WHERE imdb_id=?", (series["imdb_id"],))
        if not cur.fetchone():
            cur.execute(
                "INSERT INTO shows (imdb_id, title, watchlist_url, imdb_import_date, added_to_sickchill) VALUES (?, ?, ?, ?, ?)",
                (series["imdb_id"], series["title"], series["watchlist_url"], datetime.now().strftime("%Y-%m-%d"), 0),
            )
            conn.commit()
            debug_log(f'Series added to the database: {series["title"]} (IMDb ID: {series["imdb_id"]})')

# Get TheTVDB ID for series in the database
def get_thetvdb_ids(conn, cur):
    cur.execute("SELECT imdb_id, title FROM shows WHERE thetvdb_id IS NULL")
    series_without_thetvdb_id = cur.fetchall()
    for imdb_id, title in series_without_thetvdb_id:
        try:
            url = f"https://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid={imdb_id}"
            debug_log(f"URL used to fetch TheTVDB ID for {title} (IMDb ID: {imdb_id}): {url}")
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers)
            debug_log(f"TheTVDB response for {title} (IMDb ID: {imdb_id}): {response.status_code}")
            if response.status_code != 200 or response.content.strip() == b'':
                debug_log(f"Error fetching TheTVDB ID for {title} (IMDb ID: {imdb_id}): {response.status_code}")
                continue
            soup = BeautifulSoup(response.content, "lxml-xml")
            series = soup.find("Series")
            if series is None:
                debug_log(f"No series found for IMDb ID {imdb_id}")
                continue
            tvdb_id = series.find("id").text
            cur.execute("UPDATE shows SET thetvdb_id=? WHERE imdb_id=?", (tvdb_id, imdb_id))
            conn.commit()
            debug_log(f"TheTVDB ID added for {title} (IMDb ID: {imdb_id}, TheTVDB ID: {tvdb_id})")
        except requests.exceptions.RequestException as e:
            debug_log(f"Error fetching TheTVDB ID for {title} (IMDb ID: {imdb_id}): {e}")

# Get the list of TheTVDB IDs of shows already in SickChill
def get_sickchill_shows():
    url = f"{settings['sickchill_url']}/api/{settings['sickchill_api_key']}/?cmd=shows"
    response = requests.get(url)
    shows = response.json()["data"]
    tvdb_ids = [int(show["tvdbid"]) for show in shows.values()]
    return tvdb_ids

# Update added_to_sickchill value in the database
def update_added_to_sickchill(conn, cur, sickchill_tvdb_ids):
    cur.execute("SELECT thetvdb_id FROM shows WHERE added_to_sickchill=0")
    shows_to_check = cur.fetchall()
    for show in shows_to_check:
        if show[0] in sickchill_tvdb_ids:
            cur.execute("UPDATE shows SET added_to_sickchill=1 WHERE thetvdb_id=?", (show[0],))
            conn.commit()
            debug_log(f"Updated added_to_sickchill value for the series (TheTVDB ID: {show[0]})")

# Add series to SickChill
def add_series_to_sickchill(conn, cur):
    cur.execute("SELECT thetvdb_id, title FROM shows WHERE added_to_sickchill=0")
    shows_to_add = cur.fetchall()
    debug_log(f"{len(shows_to_add)} series to add to SickChill")
    for show in shows_to_add:
        thetvdb_id, title = show
        debug_log(f"Attempting to add series to SickChill (TheTVDB ID: {thetvdb_id}, Title: {title})")
        url = f"{settings['sickchill_url']}/api/{settings['sickchill_api_key']}/?cmd=show.addnew&indexerid={thetvdb_id}"
        debug_log(f"URL called to add the series to SickChill: {url}")
        response = requests.get(url)
        if response.status_code == 200 and response.json()["result"] == "success":
            cur.execute("UPDATE shows SET added_to_sickchill=1, sc_added_date=? WHERE thetvdb_id=?", (datetime.now().strftime("%Y-%m-%d"), thetvdb_id))
            conn.commit()
            debug_log(f"Series added to SickChill (TheTVDB ID: {thetvdb_id}, Title: {title})")
        else:
            debug_log(f"Unable to add series to SickChill (TheTVDB ID: {thetvdb_id}, Title: {title}) - Response code: {response.status_code}")




# Show the SQLite database content
def show_db_content(cursor):
    cursor.execute("PRAGMA table_info(shows)")
    columns = [column[1] for column in cursor.fetchall()]
    cursor.execute("SELECT * FROM shows")
    rows = cursor.fetchall()

    # Print column names
    column_names = "|".join(columns)
    print(f"+{'-' * len(column_names.replace('|', ''))}+")
    print(f"| {column_names} |")

    # Print separator
    print(f"+{'-' * len(column_names.replace('|', ''))}+")

    # Print rows with field values
    for row in rows:
        row_values = "|".join([str(value) for value in row])
        print(f"| {row_values} |")

    # Print bottom separator
    print(f"+{'-' * len(column_names.replace('|', ''))}+")

# Delete series from SQLite database
def delete_series_from_db(conn, cur, imdb_id):
    cur.execute("SELECT imdb_id FROM shows WHERE imdb_id=?", (imdb_id,))
    result = cur.fetchone()
    if result is None:
        debug_log(f"The series does not exist in the database (IMDb ID: {imdb_id})")
    else:
        cur.execute("DELETE FROM shows WHERE imdb_id=?", (imdb_id,))
        conn.commit()
        debug_log(f"Series removed from the database (IMDb ID: {imdb_id})")


# Main function
def main():
    check_watchlists()
    check_sickchill()
    check_thetvdb()
    conn, cur = setup_database()
    series_list = get_imdb_watchlist_series()
    insert_series_to_db(conn, cur, series_list)
    get_thetvdb_ids(conn, cur)
    sickchill_tvdb_ids = get_sickchill_shows()
    update_added_to_sickchill(conn, cur, sickchill_tvdb_ids)
    add_series_to_sickchill(conn, cur)
    conn.close()
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add series to SickChill from IMDb watchlists")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--delete", metavar="IMDb_ID", help="Remove a series from the SQLite database using its IMDB ID")
    parser.add_argument("--showdb", action="store_true", help="Display all series in the database")
    args = parser.parse_args()

    if args.debug:
        settings["debug"] = 1
        debug_log("Debug mode enabled")

    if args.delete:
        conn, cur = setup_database()
        delete_series_from_db(conn, cur, args.delete)
        conn.close()
    elif args.showdb:
        conn, cur = setup_database()
        show_db_content(cur)
        conn.close()
    else:
        main()
