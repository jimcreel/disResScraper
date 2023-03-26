import requests
import json
import pymongo
import os
from dotenv import load_dotenv
from pandas import DataFrame
import smtplib
import ssl
from email.message import EmailMessage  

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




flat_resort_list = [item for sublist in request_list for item in sublist]
update_list = []
        

url=os.getenv('DLR_URL')
wdwUrl=os.getenv('WDW_URL')


#open the site
print('opening the reservation site...')
dlr_resp=requests.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
#print(resp)
wdw_resp =requests.get(wdwUrl, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
#print(wdwResp)
dlr_dates = dlr_resp.text
wdw_dates=wdw_resp.text
dlr_parse = json.loads(dlr_dates)
wdw_parse = json.loads(wdw_dates)
resort_list = [dlr_parse, wdw_parse]


def get_full_text(code):
    print(f'received {code}')
    match code: 
        case 'DLR':
            return 'Disneyland Resort'
        case 'WDW': 
            return 'Walt Disney World'
        case 'DP':
            return 'Disneyland Park'
        case 'CA':
            return 'California Adventure'
        case 'MK':
            return 'Magic Kingdom'
        case 'EP':
            return 'EPCOT'
        case 'AK':
            return 'Animal Kingdom'
        case 'HS':
            return 'Hollywood Studios'
        case 'inspire-key-pass':
            return 'Inspire Magic Key'
        case 'enchant-key-pass':
            return 'Enchant Magic Key'
        case 'believe-key-pass':
            return 'Believe Magic Key'
        case 'imagine-key-pass':
            return 'Imagine Magic Key'
        case 'disney-incredi-pass':
            return 'Incredi-pass'
        case 'disney-sorcerer-pass':
            return 'Sorcerer Annual Pass'
        case 'disney-pirate-pass':
            return 'Pirate Annual Pass'
        case 'disney-pixie-dust-pass':
            return 'Pixie Dust Annual Pass'
        case 'ANY':
            return 'Any Park'
        
def update_availability(resort_list):
    for list in resort_list:
        for x in range(0, len(flat_resort_list), 1):
            for i in range(0, len(list), 1):
                if flat_resort_list[x]['pass'] == list[i]['passType']:
                    pass_avail = list[i]['availabilities']
                    for date in pass_avail:
                        if flat_resort_list[x]['date'] == date['date']:
                            resortString = f'{flat_resort_list[x]["resort"]}' + "_" + f'{flat_resort_list[x]["park"]}'
                            for facilities in date:
                                if flat_resort_list[x]['park'] == 'ANY':
                                    if date['slots'][0]['available'] != flat_resort_list[x]['available'] and flat_resort_list[x]['available'] == False:
                                        flat_resort_list[x]['available'] = date['slots'][0]['available']
                                        update_list.append(flat_resort_list[x])

                                elif date['facilityId'] == resortString:
                                    if date['slots'][0]['available'] != flat_resort_list[x]['available']:
                                        flat_resort_list[x]['available'] = date['slots'][0]['available']
                                        if flat_resort_list[x]['available'] == True:
                                            update_list.append(flat_resort_list[x])
                                            #print(flat_resort_list[x], '-' , date)
                                            #print('changed')
                                
                  


def notify(update_list):
    print(update_list)
    db = client['disney-reservations']
    col = db['users']
    
    for list in update_list:
        request_id = list['_id']
        park = get_full_text(list['park'])
        date = list['date']
        annual_pass = get_full_text(list['pass'])
        resort = get_full_text(list['resort'])
        col.update_one({'requests._id': request_id}, {'$set': {'requests.$.available': list['available']}})
        list_match = col.find( { 'requests._id': request_id } )
        
        for match in list_match:
            
          
            print('attempting to send email')
            smtp_server = 'az1-ss106.a2hosting.com'
            port = 465
            send_email = 'notifications@magic-reservations.com'
            receiver_email = match['email']
            password = os.getenv('MAGIC_RESERVATIONS_EMAIL_PASSWORD')
            context = ssl.create_default_context()
            emailMsg = EmailMessage()
            emailMsg.set_content(f'''
                
                Get ready to make your reservation! You requested an update when reservations were
                available on {date} at {park} !\n
                Visit https://tinyurl.com/5n8yetcw to make your reservation.\n
                Thank you for using magic-reservations.com!''')
            emailMsg['Subject'] = f'Reservations are available for {annual_pass} at {resort} on {date}'
            emailMsg['From'] = send_email
            emailMsg['To'] = receiver_email
            
            with smtplib.SMTP_SSL(smtp_server,port,context=context) as server:
                server.login(send_email,password)
                server.send_message(emailMsg, send_email, receiver_email)

update_availability(resort_list)

notify(update_list)