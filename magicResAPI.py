import requests
import json
import os


def main(resort):
    # determine the resort 

    if(resort == "DLR"):
        url = os.environ.get('DLR_URL')
    elif(resort == 'WDW'):
        url = os.environ.get('WDW_URL')
    else: return False
    
    #get the api key

    #open the site
    print('opening the reservation site...')
    resp=requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
    #print(resp)
    dates_dict = resp.text
    parse_json = json.loads(dates_dict)
    print(parse_json)
    return parse_json

main('WDW')