SickAdd
=======

A Python tool to automatically add your IMDB and/or TVDB favorites into Sickbeard


I've always been  a big fan of being able to add movie to CouchPotato sraight from my IMDB watchlist, and always dreamed to do the same with Sickbeard... Well, this is exactely what SickAdd has been designed for :)

So far, SickAdd only support auto add of your favorites from your TVDB account, but plan is to also support ImDB and TVRage.

Roughely, SickAdd is following this logic:
1. Download TVDB Favorites
2. Store result in the TVDB_table
3. Download your show list from Sickbeard
4. Automatically add to Sickbeard any show from your favorties and NOT in Sickbeard using your Sickbeard default profile

Usage/Configuration:
- Set your install path (where the DB file will be stored - need write permission)
- Set your Sickbeard host, port and API key
- Set your TVDB Account ID
- Schedule a task to run this script every x hours (IE: using cron under linux)

That's it, enjoy your TDDB Favorites being automatically added to SickBeard using your SB default profile


Release note:
I've been tested this successfully with SickRage, and works smoothly.
However be carfeull if your using TVRage as indexer, since SickAdd only supports TVDB Id currently, if a show indexed with TVRage in Sickbeard was added to your TVDB ID favorites it would most likely add it a second time to Sickbeard (not tested but kind of expected behavior).

I haven't test this script under Windows, but it should work correctly.


RoadMap:
- Support for IMDB
- Support for TVRage
- Support for custom profile while adding show
