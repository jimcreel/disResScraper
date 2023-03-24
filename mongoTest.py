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
    request_list.append(data['requests'])

print(request_list)


flat_list = [item for sublist in request_list for item in sublist]


        

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

for x in range(0, len(flat_list), 1):
    for i in range(0, len(parse_json), 1):
        if flat_list[x]['pass'] == parse_json[i]['passType']:
            pass_avail = parse_json[i]['availabilities']
            for date in pass_avail:
                if flat_list[x]['date'] == date['date']:
                    resortString = f'{flat_list[x]["resort"]}' + "_" + f'{flat_list[x]["park"]}'
                    
                    for facilities in date:
                        if date['facilityId'] == resortString:
                            print(date['facilityId'])
                            print(flat_list[x]['park'] + ' request ' + flat_list[x]['date'])
                            print(date['facilityId'] + ' has ' + f'{date["slots"][0]["available"]}') 



