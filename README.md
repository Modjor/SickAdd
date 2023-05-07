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

You'll need Python3 installed with argparse, sqlite3, requests & BeautifulSoup

Usage:
sickadd.py [-h] [--debug] [--delete IMDb_ID] [--showdb] [--watchlist_urls URL [URL ...]] [--sickchill_url SICKCHILL_URL] [--sickchill_api_key SICKCHILL_API_KEY]

options:
  -h, --help            show this help message and exit
  --debug               Enable debug mode
  --delete IMDb_ID      Remove a series from the SQLite database using its IMDb ID
                        Example: --delete "tt1234567"
  --showdb              Display all series in the database
  --watchlist_urls URL [URL ...]
                        List of IMDb watchlist URLs separated by commas
                        Example: --watchlist_urls "https://www.imdb.com/list/ls00000000,https://www.imdb.com/list/ls123456789"
  --sickchill_url SICKCHILL_URL
                        SickChill URL (example: http://sickchill_ip:port)
                        Example: --sickchill_url "http://192.168.1.2:8081"
  --sickchill_api_key SICKCHILL_API_KEY
                        SickChill API key
                        Example: --sickchill_api_key "1a2b3c4d5e6f7g8h"
                        
Example:
python sickadd.py --debug   --watchlist_urls "https://www.imdb.com/list/ls987654321,https://www.imdb.com/list/ls123456789"  --sickchill_url "http://192.168.1.2:8081" --sickchill_api_key "1a2b3c4d5e6f7g8h"
