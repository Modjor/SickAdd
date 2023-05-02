SickAdd
=======

A Python tool to automatically add your IMDB favorites into SickChill

Roughely, SickAdd is following this logic:
1. Download  IMDB watchlist(s)
2. Only keeps TV Shows
3. Map IMDB IDs to TheTVDB IDs
3. Store result in a sqlite db
4. Download your show list from Sickchill
5. Automatically add to Sickchill using TheTVDB IDs any show from the specified watchlist(s) NOT already in Sickchill and NOT added previoulsy with SickAdd, using your Sickchill default profile.


Usage/Configuration:
You'll need Python3 installed with argparse, sqlite3, requests & BeautifulSoup.
- Set your Sickchill host, port and API key
- Set your IMDB lists URL (multiple supported)
- Schedule a task to run this script every x hours (IE: using cron under linux) : python SickAdd.py

That's it, enjoy your IMDB TV Shows being automatically retrieved and added to SickBeard using your Sickchill default profile

Additional usage:
- You can list all shows from the sqlite db using the command ""SickAdd.py --showdb"
- You can remove previously added item from the sqlite db using the command "SickAdd.py --delete IMDb_ID" (replace IMDB_ID with the IMDB ID of the show you want to remove from the SickChill DB.


Release note:
Add series to SickChill from IMDb watchlists

options:
  -h, --help        show this help message and exit
  --debug           Enable debug mode
  --delete IMDb_ID  Remove a series from the SQLite database using its IMDB ID
  --showdb          Display all series in the database
