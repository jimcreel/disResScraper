import json
from prodict import Prodict
import requests


#target site
url='https://disneyland.disney.go.com/passes/blockout-dates/api/get-availability/?product-types=inspire-key-pass,believe-key-pass,enchant-key-pass,imagine-key-pass,dream-key-pass&destinationId=DLR&numMonths=14'

#open the site
resp=requests.get(url, headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
#print(resp)
dates_dict = resp.text
parse_json = json.loads(dates_dict)

#parse the json into separate keys
inspire = parse_json[0]
believe = parse_json[1]
enchant = parse_json[2]
imagine = parse_json[3]
dream = parse_json[4]

#further parse the json into the list elements

inspire_avail = inspire['availabilities']
believe_avail = believe['availabilities']
enchant_avail = enchant['availabilities']
imagine_avail = imagine['availabilities']
dream_avail = dream['availabilities']

inspire_json = json.dumps(inspire_avail, indent = 4)

print(inspire_json)
with open('inspiredates.json','w') as outfile:
   outfile.write(inspire_json)

#with open ('inspiredates.json', 'rb') as f:
#    inspire_dates=Prodict.from_dict(json.load(f))

def get_park_availability(querydate,magickey,park):
    #dateindex = get_date_index(magickey, querydate)
    dp_avail = magickey[dateindex]['facilities'][1]['available']
    dca_avail = magickey[dateindex]['facilities'][0]['available']
    if (park == 'DP'):
        return dp_avail
    if (park == 'DCA'):
        return dca_avail
    if (park == 'ANY'):
        if dp_avail or dca_avail:
            return True
        else:
            return False

#    for dates in testdate:
#            for days in inspire_dates.date:
#                print (days)
#                if testdate == days:
#                    print(inspire_dates.date)
        #if inspire_dates[date] == testdate:
    

#with open('dates.json', 'rb') as f:
#    props = Prodict.from_dict(json.load(f))
#   print(props.calendar_availabilities)



""" class clsprops:
	def __init__(self, data):
		self.__dict__ = data

def main():
  with open('resources.json','rb') as f:
    props = Prodict.from_dict(json.load(f))
    print(props.sitemap.url)

if (__name__=="__main__"):
  main() """