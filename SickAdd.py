#!/usr/bin/env python
#
##################################################################################
### SickAdd V. 1.0  - THIS IS AN ALPHA RELEASE
#
# This script downloads your TVDB favorites and add them to your SickBeard shows
#
# NOTE: This script requires Python to be installed on your system
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
tvdb_enabled = 1



##########################################################


### BEGIN OF SCRIPT
import sys
import urllib2
import sqlite3
import os.path
import json
from lxml import etree
from StringIO import StringIO

tvdb_api_url = "http://thetvdb.com/api"
sickadd_db = install_path + "/" + db_name
sickadd_version = 1
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



## DB Check - checks if db exists
def db_check():
	print "Initializing database " + sickadd_db
	if not os.path.isfile(sickadd_db):
		print ("database does NOT exist")
		db_creation()
		
	else:
		print db_name + " found. Continuing..."




## Is TVDB processing is enabled?
def tvdb_check():
	if tvdb_enabled == 1:
		tvdb_processing()
	else: 
		print ("TVDB processing is disabled")
		print ("Please configure and enable TVDB in your settings")
		sys.exit()

	

	
## TVDB processing
def tvdb_processing():
#	Get the favorites from TVDB.com
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
		print "Adding show TVDB ID: " + Favorites.text
		FavoritesInt = int(Favorites.text)
		c.execute ("INSERT OR IGNORE INTO tvdb_fav VALUES (?,?,?)", (FavoritesInt, "", 0))
		conn.commit()
	print "XML Import Done"
	conn.close()



## Checking if sickbeard is running
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
		print "Checking show: " + tvdbid + ": " + show_name
		c.execute ('UPDATE tvdb_fav SET state = 2 WHERE state != 2 AND tvdb_id  = ?', [tvdbid])
		c.execute ('UPDATE tvdb_fav SET tvdb_name = ? WHERE tvdb_name != ? AND tvdb_id  = ?', (show_name, show_name, tvdbid))	
	conn.commit()
	conn.close()
	print "Local database updated with current list of Sickbeard shows"


		

def AddToSickbeard():
	print "Adding to SickBeard favorites which are not already there"
	sb_add_show_url =  sickbeard_api_url + "/?cmd=show.addnew&tvdbid="
	conn = sqlite3.connect(sickadd_db)
	c = conn.cursor()
	c.execute ("SELECT tvdb_id FROM tvdb_fav WHERE state < 2")
	result_set = c.fetchall()
	for tvdbid_list in result_set:
		tvdb_id =  str(tvdbid_list[0])
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



	
	

def startup():
	db_check()
	if tvdb_enabled == 1:
		print "TVDB Favorites are enabled"
		tvdb_check()
	else:
		print "TVDB Favorites are disabled. Skipping TVDB"
	sickbeard_check()
	AddToSickbeard()	

startup()

