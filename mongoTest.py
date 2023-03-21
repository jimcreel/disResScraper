import requests
import json
import pymongo
import os
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

client = pymongo.MongoClient(os.getenv('MONGODBURI'))

db = client['disney-reservations']
col = db['users']
x = col.find({}, {"requests":1})
print('connecting to db')
request_list = []
print('building request list')
for data in x:
    print(data)
    request_list.append(data['requests'])


        

url=os.getenv('DLR_URL')
wdwUrl=os.getenv('WDW_URL')


#open the site
print('opening the reservation site...')
resp=requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
#print(resp)
wdwResp =requests.get(wdwUrl, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
#print(wdwResp)
dates_dict = resp.text
wdwDates=wdwResp.text
parse_json = json.loads(dates_dict)



def find_available_slots(requests, disAvail):
    available_slots = []
    for request in requests:
        for slot in disAvail:
            print(slot)
            if slot['date'] == request['date'] and slot['facilityId'] == f"{request['resort']}_{request['park']}":
                for sub_slot in slot['slots']:
                    if request['pass'] in sub_slot['slotIds']:
                        if sub_slot['available']:
                            available_slots.append({'date': slot['date'], 'facilityId': slot['facilityId'], 'pass': request['pass']})
    return available_slots

print(find_available_slots(request_list, parse_json))