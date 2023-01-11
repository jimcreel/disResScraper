import requests
import json
import bitdotio
import psycopg2
import itertools
import os
from twilio.rest import Client
from datetime import datetime
from datetime import date
import csv
import smtplib, ssl
from email.message import EmailMessage

#get the api key
apiKey=os.environ.get('BIT_DOT_IO_API_KEY')
#target site
url='https://disneyland.disney.go.com/passes/blockout-dates/api/get-availability/?product-types=inspire-key-pass,believe-key-pass,enchant-key-pass,imagine-key-pass,dream-key-pass&destinationId=DLR&numMonths=14'
wdwUrl='https://disneyworld.disney.go.com/passes/blockout-dates/api/get-availability/?product-types=disney-incredi-pass,disney-sorcerer-pass,disney-pirate-pass,disney-pixie-dust-pass&destinationId=WDW&numMonths=13'

#open the site
print('opening the reservation site...')
resp=requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
#print(resp)
wdwResp =requests.get(wdwUrl, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
#print(wdwResp)
dates_dict = resp.text
wdwDates=wdwResp.text
parse_json = json.loads(dates_dict)
dates_dict = resp.text
wdwParse_json = json.loads(wdwDates)

#Data is separated into a list of calendar availability with elements separated by pass name
inspire_avail = parse_json[0]['availabilities']
believe_avail = parse_json[1]['availabilities']
enchant_avail = parse_json[2]['availabilities']
imagine_avail = parse_json[3]['availabilities']
dream_avail = parse_json[4]['availabilities']
incredi_avail=wdwParse_json[0]['availabilities']
sorceror_avail=wdwParse_json[1]['availabilities']
pirate_avail=wdwParse_json[2]['availabilities']
pixie_avail=wdwParse_json[3]['availabilities']


for index, availabilityDictionary in enumerate(inspire_avail):
        #print(dic['date'] + dic['facilityId'])
            parkAvailable = availabilityDictionary['slots'][0]['available']
            parkDate = availabilityDictionary['date']
            parkCurrent = availabilityDictionary['facilityId']

            c = bitdotio.bitdotio(apiKey)

        #update most recent search
        update_db = """
            SELECT resort, park, pass, date, available
            FROM disData
            UPDATE disData
            SET available = {}
            WHERE date = '{}' and park = '{}' and pass = '{}'
            """.format(parkAvailable, update_date, update_park, update_pass)
        with c.get_connection("jimcreel/trial") as conn:
                    cursor = conn.cursor()
                    cursor.execute(update_db)
        #parkDate = (inspire_avail[row]['date'])
       # parkLocation = (inspire_avail[row['facilityId']])
       # parkPass = 'inspire'