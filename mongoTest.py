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




flat_list = [item for sublist in request_list for item in sublist]
update_list = []
        

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
wdwParse = json.loads(wdwDates)
json_list = [parse_json, wdwParse]

for list in json_list:
    for x in range(0, len(flat_list), 1):
        for i in range(0, len(list), 1):
            if flat_list[x]['pass'] == list[i]['passType']:
                pass_avail = list[i]['availabilities']
                for date in pass_avail:
                    if flat_list[x]['date'] == date['date']:
                        resortString = f'{flat_list[x]["resort"]}' + "_" + f'{flat_list[x]["park"]}'
                        for facilities in date:
                            if flat_list[x]['park'] == 'ANY':
                                if date['slots'][0]['available'] != flat_list[x]['available'] and flat_list[x]['available'] == False:
                                    flat_list[x]['available'] = date['slots'][0]['available']
                                    print(flat_list[x]['date'], '-' , date)
                                    print('changed')
                                    update_list.append(flat_list[x])
                            if date['facilityId'] == resortString:
                                if date['slots'][0]['available'] != flat_list[x]['available']:
                                    flat_list[x]['available'] = date['slots'][0]['available']
                                    update_list.append(flat_list[x])
                                    #print(flat_list[x], '-' , date)
                                    #print('changed')

for list in update_list:
    print(list)

db = client['disney-reservations']
col = db['users']
for list in update_list:
    request_id = list['_id']
    col.update_one({'requests._id': request_id}, {'$set': {'requests.$.available': list['available']}})
    list_match = col.find({}, {request_id { $in: requests._id}})
    print(list_match)
    #test

