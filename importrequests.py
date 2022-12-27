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


#target site
url='https://disneyland.disney.go.com/passes/blockout-dates/api/get-availability/?product-types=inspire-key-pass,believe-key-pass,enchant-key-pass,imagine-key-pass,dream-key-pass&destinationId=DLR&numMonths=14'

#open the site
resp=requests.get(url, headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36', "Upgrade-Insecure-Requests": "1","DNT": "1","Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8","Accept-Language": "en-US,en;q=0.5","Accept-Encoding": "gzip, deflate"})
#print(resp)
dates_dict = resp.text
parse_json = json.loads(dates_dict)

#Data is separated into a list of calendar availability with 5 elements separated by key level
inspire_avail = parse_json[0]['availabilities']
believe_avail = parse_json[1]['availabilities']
enchant_avail = parse_json[2]['availabilities']
imagine_avail = parse_json[3]['availabilities']
dream_avail = parse_json[4]['availabilities']

#further parse the json into the list elements

#inspire_avail = inspire['availabilities']
#believe_avail = believe['availabilities']
#enchant_avail = enchant['availabilities']
#imagine_avail = imagine['availabilities']
#dream_avail = dream['availabilities']

def main():
    today=date.today()
    d1 = today.strftime("%Y-%m-%d")
    remove_past_dates(today)
    #print(today)
    query_list=get_list()
    new_data=make_queries(query_list)
    #print(new_data)
    update_data(new_data)
    notify()

def remove_past_dates(today):

#This function updates the remote db with any newly available dates
    a = bitdotio.bitdotio("v2_3wYE3_p3tdjf89BN3c3dbka8tE5nN")

    #update most recent search
    remove_dates = """
        
        INSERT INTO oldresdates (email, pass, park, date, available, notify, notifications, method, phone, modified)
        SELECT email, pass, park, date, available, notify, notifications, method, phone, modified FROM disreserve
        WHERE date < '{}';


        DELETE from disreserve WHERE date < '{}'""".format(today, today)
        
    with a.get_connection("jimcreel/trial") as conn:
                cursor = conn.cursor()
                cursor.execute(remove_dates)

def update_data(new_data):
    for row in range(len(new_data)):
        update_date = new_data[row][0]
        update_park = new_data[row][2]
        update_pass = new_data[row][1]
        update_avail = new_data[row][3]
        
        #connect to bit.io with api key
        c = bitdotio.bitdotio("v2_3wYE3_p3tdjf89BN3c3dbka8tE5nN")

        #update most recent search
        update_db = """
            UPDATE disreserve
            SET available = {}
            WHERE date = '{}' and park = '{}' and pass = '{}'
            """.format(update_avail, update_date, update_park, update_pass)
        with c.get_connection("jimcreel/trial") as conn:
                    cursor = conn.cursor()
                    cursor.execute(update_db)
#This function connects to the remote db and returns a list of dates,
#keys, and parks that are flagged for notifications

def get_list():
    #connect to bit.io with api key
    b = bitdotio.bitdotio("v2_3wYE3_p3tdjf89BN3c3dbka8tE5nN")
    
    #check to see which dates are being requested by users
    retrieve_data = """
        SELECT DISTINCT pass, park, date
        FROM disreserve
        """
    #retrieve dates
    with b.get_connection("jimcreel/trial") as conn:
        cursor = conn.cursor()
        cursor.execute(retrieve_data)
        record=cursor.fetchall()
        return(record)

#This function takes the list of user requested dates, parks, and passes returned by get_list() and passes 
# those arguments into the get_park_availability function
#   
def make_queries(query_list):
    results_list = []
    for row in range(len(query_list)):
        #print(query_list[row])
        check_date = query_list[row][2]
        check_park = query_list[row][1]
        check_pass = query_list[row][0]
        #print(check_pass)
        match check_pass:
            case 'inspire':
                check_pass_json = inspire_avail
            case 'believe':
                check_pass_json = believe_avail
            case 'enchant':
                check_pass_json = enchant_avail
            case 'dream':
                check_pass_json = dream_avail
            case 'imagine':
                check_pass_json = imagine_avail
       
        #print(check_pass_json)    
        if check_park == 'ANY':
            dlrResult = get_park_availability(check_date,check_pass_json,'DLR_DP')
            dcaResult = get_park_availability(check_date,check_pass_json,'DLR_CA')
            if dlrResult or dcaResult:
                result = True
        else: result = get_park_availability(check_date,check_pass_json,check_park)
        #print(check_date, check_park, result)    
        result_tup = (check_date, check_pass, check_park, result)
        results_list.append(result_tup)
    return(results_list)

#This function grabs park availability for each unique date/park/pass combination

def get_park_availability(querydate, avail, querypark):
    #print(avail)
    for index, availabilityDictionary in enumerate(avail):
        #print(dic['date'] + dic['facilityId'])
        if availabilityDictionary['date'] == querydate and availabilityDictionary['facilityId'] == querypark:
            #print(i)
            return availabilityDictionary['slots'][0]['available']
        

#This function makes a new call to the db to generate a list of notifications, generates a message, then sends out notifications via SMS or email  
def notify():
    d = bitdotio.bitdotio("v2_3wYE3_p3tdjf89BN3c3dbka8tE5nN")
    notify_list = []
    fetch_avail = """
        SELECT email, pass, park, date, notifications, method, phone, modified
        FROM disreserve
        WHERE available= true AND notify = true
        """
    
    ck_nots = "If you wish to no longer receive notifications for this reservation, please open the following link:"
    #retrieve test data
    with d.get_connection("jimcreel/trial") as dconn:
        dcursor = dconn.cursor()
        dcursor.execute(fetch_avail)
        not_records = dcursor.fetchall()
        
             
    for row in range(len(not_records)):
        email = not_records[row][0]
        magickey = not_records[row][1]
        park = not_records[row][2]
        if (park == 'DLR_DP'):
            parkfull = 'for Disneyland'
        if (park == 'DLR_CA'):
            parkfull = "for California Adventure"
        else:
            parkfull = ''
        date = not_records[row][3]
        #datetime_obj = datetime.strptime(date, '%y-%m-%d')
        #print(datetime_obj)
        nots = not_records[row][4]
        method = not_records[row][5]
        phone = not_records[row][6]
        msg = ("Reservations {} are available on {} for {} key holders. Visit https://tinyurl.com/5n8yetcw to make your reservation.").format(parkfull,date,magickey)
        #print(msg)
       # print("to:",email,".","Reservations for",park,"are available for",date)
        #print(not_records[row][4])
        #print(method)
        if (method == 'phone'):
            if (nots < 10):
                #send the not via sms        
                print(phone, msg)
                account_sid = "AC0e18af4b5d6a7bd2c440bf47d515c051"
                auth_token = "83bfe69ba814924e99a98459387246b0"
                client = Client(account_sid, auth_token)
                message = client.messages \
                        .create(
                        body = msg,
                        from_ = "+15107267039",
                        to='+1{}'.format(phone)
                        )
                print(message.sid)
                f = bitdotio.bitdotio("v2_3wYE3_p3tdjf89BN3c3dbka8tE5nN")
                increment_note = """
                    UPDATE disreserve 
                    SET notifications = notifications + 1, modified = NOW()
                    WHERE phone = '{}' and date = '{}' and park = '{}' and pass = '{}'
                    """.format(phone, date, park, magickey)
                #print(increment_note)
                with f.get_connection("jimcreel/trial") as fconn:
                    fcursor = fconn.cursor()
                    fcursor.execute(increment_note)
                    
            
main()

### DEPRECATED, index no longer needed in new data structure
#This function uses the date index to navigate to the dictionary
#at date_index, determines which park to evaluate, and returns the park
#status
#def get_park_availability(querydate,magickey,querypark):
#    dateindex = get_date_index(magickey, querydate, querypark)
#    #print(dateindex)
#    return magickey['querydate']['slots']['available']
    
    #if (park == 'DP'):
    #    return dp_avail
    #if (park == 'DCA'):
    #    return dca_avail
    #if (park == 'ANY'):
    #    if dp_avail or dca_avail:
    #        return True
    #    else:
    #        return False

### IN PROGRESS, save values to CSV
 #save notifications to csv
   # with open('/Users/jimcreel/Desktop/resScraper/notificationLog.txt', 'a') as z:
    #    csv_writer = csv.writer(z)
     #   for mytuple in not_records:
      #      csv_writer.writerow(mytuple)
    
    #grab values from row
    #print(not_records)
    #with open('log.csv','w+', newline ='') as logcsv:
    #   writecsv = csv.writer(logcsv)
    #    writecsv.writerow(not_records)