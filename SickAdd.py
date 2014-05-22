#!/usr/bin/env python
#
##################################################################################
### SickAdd V. 2  - THIS IS AN ALPHA RELEASE
#
# This script downloads your TVDB favorites and add them to your SickBeard shows
#
# NOTE: This script requires Python to be installed on your system
#
#
# Changelog
# Version 2
# - Add IMDB Watch list support (using IMDB Mapping from TVDB)
# - Add a Debug mode so it's a bit less verbose in standard mode
#
##################################################################################



### OPTIONS

## General

# SickAdd settings
db_name = "sickadd.db"
install_path = "/volume1/Scripts/SickAdd" #directory where sickadd.db will be created


# Sickbeard configuration
sickbeard_host = "127.0.0.1"
sickbeard_port = "8083"
sickbeard_api = "your_api_key"
webroot = ""


#TVDB Configuration
tvdb_accountid= "your_tvdb_account_id"
tvdb_enabled = 0

# IMDB Configuration
imdb_watchlist_rss_url = "path_to_imdb_watchlist_rss"
imdb_enabled = 0



# Advanced Settings
debug = 0



#########    NO MODIFICATION UNDER THAT LINE
##########################################################


### BEGIN OF SCRIPT
import sys
import urllib2
import sqlite3
import os.path
import json
from lxml import etree
from StringIO import StringIO
import shutil


db_version_must_be = 2
sickadd_db = install_path + "/" + db_name
sickbeard_api_url = "http://" + sickbeard_host + ":" + sickbeard_port + "/api/" + sickbeard_api

	
## Database creation
def db_creation():
	print "Creating database file: " + sickadd_db 
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()
	c.execute ('''CREATE TABLE tvdb_fav (tvdb_id INTEGER PRIMARY KEY, tvdb_name text, state INTEGER DEFAULT '0')''')
	c.execute ('''CREATE TABLE info (db_version num)''')
	c.execute ("INSERT INTO info VALUES (1)")
	conn.commit()
	conn.close()
	print "Database has been created"
	db_check()



##############################   DATABASE OPERATIONS  ############################

## DB Check - checks if db exists or if needs to be upgraded
def db_check():
	print "Initializing database " + sickadd_db
	if not os.path.isfile(sickadd_db):
		print ("database does NOT exist")
		db_creation()
		
	else:
		if debug == 1:
			print db_name + " found. Checking Database version"
		conn = sqlite3.connect(sickadd_db)
		c = conn.cursor()
		c.execute ("SELECT db_version FROM info WHERE db_version NOT NULL")
		result_set = c.fetchall()
		value =  result_set[0]
		current_db_version = str(value[0])
		
		if debug == 1:
			print "Current Database version is: " + current_db_version
			print "Database version must be: " + str(db_version_must_be)
			
		if int(current_db_version) > db_version_must_be:
			print "Your database file version greater than what this version of SickAdd can support"
			print "Please upgrade SickAdd or delete your DB file"
			print "Exiting..."
			conn.close()
			sys.exit()
			
		if int(current_db_version) == db_version_must_be:
			if debug == 1:
				print "Your database is using current schema. No need for update"
			conn.close()
		else:
			print "Your database scheme has to be upgraded"
			conn.close()
			db_upgrade(current_db_version)
	
	



## DB Upgrade. Used if current DB file has to be upgraded to match current SickAdd version	
def db_upgrade(current_db_version):	
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()	
	if 	int(current_db_version) == 1:
#	UPGRADE TO VERSION 2 ANY DB IN VERSION 1
		db_bck = (sickadd_db + "_v1")		
		if debug == 1:
			print "Backing up database file as: "  + db_bck
			print "Upgrading database to version 2..."
		shutil.copyfile(sickadd_db, db_bck)
		c.execute ("CREATE TABLE imdb_fav (imdb_id text PRIMARY KEY, imdb_name text, tvdb_id INTEGER)")
		c.execute ("UPDATE info SET db_version = 2 WHERE db_version = 1")
		conn.commit()
		c.execute ("SELECT db_version FROM info WHERE db_version NOT NULL")
		result_set = c.fetchall()
		value =  result_set[0]
		current_db_version = value[0]
		conn.close()
		if debug == 1:
			print "DB should be now in version "+ str(current_db_version)
		if current_db_version == 2:
			if debug == 1:
				print "Your database has been upgraded to version 2"
			db_check()
		else:
			print "Database is NOT in version 2"
			print "Error during database upgrade. Exiting..."
			sys.exit()
			
			
		



		
##############################  TVDB FAVORITES PROCESSING  ############################		

## TVDB processing -  download TVDB favorites and add them to SickAdd db
def tvdb_processing():
#	Get the favorites from TVDB.com
	if debug == 1:
		print ("Retrieving TVDB Favorites for Account ID: " + tvdb_accountid)
	tvdb_fav_url =  tvdb_api_url + "/User_Favorites.php?accountid=" + tvdb_accountid
	response = urllib2.urlopen(tvdb_fav_url)
	tvdb_xml = response.read()
	response.close()
	if '</Favorites>' not in tvdb_xml:
		print ("There was wan error grabbing TVDB favorites")
		print (tvdb_fav_url)
		sys.exit()
#	Parse the XML result and add the favorites to the sickadd database
	print ("Favorites downloaded. Parsing into database...")
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()
	tree = etree.parse(StringIO(tvdb_xml))
	for Favorites in tree.xpath("/Favorites/Series"):
		if debug == 1:
			print "Adding show TVDB ID: " + Favorites.text
		FavoritesInt = int(Favorites.text)
		c.execute ("INSERT OR IGNORE INTO tvdb_fav VALUES (?,?,?)", (FavoritesInt, "", 0))
		conn.commit()
	print "XML Import Done"
	conn.close()

	


	
##############################  IMDB FAVORITES PROCESSING  ############################	
	
## IMDB Processing: Download IMDB RSS whatchlist and store the IMDB_ID and IMDB_Title in the imdb_fav table
# Download IMDB watchlist and add it to local SickAdd DB 
def imdb_processing(imdb_watchlist_rss_url):
#	Get the watchlist from imdb.com
	imdb_http_status = urllib2.urlopen("http://www.imdb.com").getcode()
	if imdb_http_status != 200:
		print "IMDB cannot be contacted. Cancelling IMDB processing"
		return
	if debug == 1:
		print ("Retrieving IMDB watchlist from:")
		print imdb_watchlist_rss_url
	response = urllib2.urlopen(imdb_watchlist_rss_url)
	imdb_rss = response.read()
	response.close()
#	Parse the IMDB RSS result from the web response and only add the IMDB TV series to the sickadd database
	if debug == 1:
		print "Adding new IMDB IDs to SickAdd database"
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()
	tree = etree.parse(StringIO(imdb_rss))
	for item in tree.iter('item'):
		imdb_title = item[1].text
		imdb_link = item[2].text
		imdb_guid = item[3].text
		imdb_id = (imdb_guid[-10:])[:9]
		if debug == 1:
			print "Title: " + imdb_title
			print "Link: " + imdb_link
			print "GUID: " + imdb_guid
			print "IMDB ID from GUID: " + imdb_id
		if ("TV Series" in imdb_title) or ("Mini-Series" in imdb_title):
			if debug == 1:
				print imdb_title, "seems to be a TV show"
				print "Adding (if does not already exist)", imdb_title, "to IMDB Favorites"
			c.execute ("INSERT OR IGNORE INTO imdb_fav VALUES (?,?,?)", (imdb_id, imdb_title, None))
			conn.commit()
	if debug == 1:
		print "End of IMDB watch list Import"
	conn.close()
	imdbid_to_tvdbid()


## Looks at all IMDB_fav records without a valid TVDB ID and tries to find a match on TVDB:
def imdbid_to_tvdbid():
	tvdb_http_status = urllib2.urlopen("http://thetvdb.com").getcode()
	if tvdb_http_status != 200:
		print "TheTVDB cannot be contacted. Cancelling process 'IMDB ID TO TVDB ID'"
		return
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()
# Select all records from imdb_fav table where tvdb_id is NULL	
	c.execute ("SELECT imdb_id, imdb_name FROM imdb_fav WHERE tvdb_id is NULL")
	result_set = c.fetchall()
	for imdb_id_list in result_set:
		imdb_id =  str(imdb_id_list[0])
		imdb_name = imdb_id_list[1]
		print "TV show", imdb_name, "does not have a valid TVDB ID. Trying to find one"
		print "Attempting to match IMDB ID", imdb_id, "with TheTVDB"
 # 		Request TVDP API using IMDB ID of the show		
		tvdb_imdbid_request_url = (tvdb_api_url + "/GetSeriesByRemoteID.php?imdbid=" + imdb_id)
		if debug == 1:
			print ("Retrieving IMDB Info from TVDB using:")
			print tvdb_imdbid_request_url
		response = urllib2.urlopen(tvdb_imdbid_request_url)
		tvdb_show = etree.parse(StringIO(response.read()))
# 		Checks if the answer from TVDB contains TVDB data or not		
		tvdb_id_txt = tvdb_show.find('Series/seriesid')
		if tvdb_id_txt is None: 
			print "No record found on TVDB for", imdb_id, "-", imdb_name
		else:
# 		If data found, add the TVDB id to the IMDB table for the current IMDB record
			tvdb_id = int((tvdb_id_txt).text)
			print "TVDB ID value found for IMDB", imdb_id, ":", str(tvdb_id)
			c.execute ('UPDATE imdb_fav SET tvdb_id = ? WHERE imdb_id = ? AND tvdb_id is NULL', (tvdb_id, imdb_id))
			conn.commit()

	conn.close()
	imdb_table_to_tvdb_table()

	
	
def imdb_table_to_tvdb_table():
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()	
	c.execute ("SELECT tvdb_id, imdb_name FROM imdb_fav WHERE tvdb_id is NOT NULL")
	result_set = c.fetchall()
	for imdb_fav_list in result_set:
		tvdb_id =  int(imdb_fav_list[0])
		imdb_name = ("IMDB - " + (imdb_fav_list[1]))
		c.execute ("INSERT OR IGNORE INTO tvdb_fav VALUES (?,?,?)", (tvdb_id, imdb_name, 0))
		conn.commit()









##############################  SICKBEARD INTERACTIONS  ############################	

## Is Sickbeard reachable?
def sickbeard_check():
	sb_http_status = urllib2.urlopen(sickbeard_api_url).getcode()
	if sb_http_status != 200:
		print "Sickbeard cannot be contacted. Make sure it's running and host and port are corrects"
		sys.exit()
	else:
		print "Sickbeard is running. Continuing..."
		sb_showlist_download()

		


## Retrieve the list of all shows from Sickbeard
def sb_showlist_download():
	#	Get the list from Sickbeard
	print ("Retrieving Sickbeard show list")
	sb_show_list_url =  sickbeard_api_url + "/?cmd=shows"
	if debug == 1:
		print "Getting show list from: " + sb_show_list_url
	response = urllib2.urlopen(sb_show_list_url)
	sb_show_list_response = json.load(response)
	response.close()
#	Checking if the list downloaded correctly
	if not sb_show_list_response['result'] == "success":
		print "There was an error with the downloaded list"
		sys.exit()
	else:
		print "Show list successfully retrieved from SickBeard"
		print "Sending a list of Sickbeard shows for status update in local DB"
		tvdb_show_status_update(sb_show_list_response['data'])


		
## Changing TVDB records status to "in_SB" for 	any records found in SB
def tvdb_show_status_update(sb_show_list):
#	print "Parsing SickBeard show list into a list of TVDB ID"
	print "connecting database file: " + sickadd_db
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()
	for item in sb_show_list:
		sb_show_id = sb_show_list[item]
		show_name = sb_show_id['show_name']
		tvdbid = str(sb_show_id['tvdbid'])
		if debug == 1:
			print "Checking show: " + tvdbid + ": " + show_name
		c.execute ('UPDATE tvdb_fav SET state = 2 WHERE state != 2 AND tvdb_id  = ?', [tvdbid])
		c.execute ('UPDATE tvdb_fav SET tvdb_name = ? WHERE tvdb_name != ? AND tvdb_id  = ?', (show_name, show_name, tvdbid))	
	conn.commit()
	conn.close()
	print "Local database updated with current list of Sickbeard shows"

	

		
## Add to SickBeard shows with TVDB IDs which are not already there
def AddToSickbeard():
	if debug == 1:
		print "Adding to SickBeard shows with TVDB IDs which are not already there"
	sb_add_show_url =  sickbeard_api_url + "/?cmd=show.addnew&tvdbid="
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()
	c.execute ("SELECT tvdb_id FROM tvdb_fav WHERE state < 2")
	result_set = c.fetchall()
	for tvdbid_list in result_set:
		tvdb_id =  str(tvdbid_list[0])
		if debug == 1:
			print "Adding show with TVDB ID: " + tvdb_id
			print sb_add_show_url + tvdb_id
		response = urllib2.urlopen(sb_add_show_url + tvdb_id)
		sb_add_show_response = json.load(response)
		if not sb_add_show_response['result'] == "success":
			print "There was an error wile adding the show"
		else:
			print "yipee! Show was successfully added to Sickbeard!"
		
	conn.commit()
	conn.close()



################################### SCRIPT STARTUP ###########################################	

def startup():
	db_check()
# Is TVDB Enabled?
	if tvdb_enabled == 1:
		print "TVDB Favorites are enabled. Processing TVDB"
		tvdb_processing()
	else:
		print "TVDB Favorites are disabled. Skipping TVDB Favorites download"

# Is IMDB enabled?	
	if imdb_enabled == 1:
		print "IMDB watchlist is enabled. Downloading now IMDB watchlist"
		imdb_processing(imdb_watchlist_rss_url)
	else:
		print "IMDB watchlist disabled. Skipping IMDB processing"
	
	sickbeard_check()
	AddToSickbeard()	

startup()
