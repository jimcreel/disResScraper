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

#get the api key
apiKey=os.environ.get('BIT_DOT_IO_API_KEY')
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

#This function updates the remote db to remove any past dates
    a = bitdotio.bitdotio(apiKey)
    remove_dates = """
        
        INSERT INTO oldresdates 
        SELECT * FROM disreserve
        WHERE date < '{}';


        DELETE from disreserve WHERE date < '{}'""".format(today, today)
        
    with a.get_connection("jimcreel/trial") as conn:
                cursor = conn.cursor()
                cursor.execute(remove_dates)

#This function injects new data into the remote db
def update_data(new_data):
    for row in range(len(new_data)):
        update_date = new_data[row][0]
        update_park = new_data[row][2]
        update_pass = new_data[row][1]
        update_avail = new_data[row][3]
        
        #connect to bit.io with api key
        c = bitdotio.bitdotio(apiKey)

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
    b = bitdotio.bitdotio(apiKey)
    
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

#This function takes the list of user requested dates, parks, and passes returned by get_list(), reads
# individual variables from the list and passes 
# those arguments into the get_park_availability function along with the 
# appropriate key level data
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

#This function searches the appropriate key data for the specified park/pass combination

def get_park_availability(querydate, avail, querypark):
    #print(avail)
    for index, availabilityDictionary in enumerate(avail):
        #print(dic['date'] + dic['facilityId'])
        if availabilityDictionary['date'] == querydate and availabilityDictionary['facilityId'] == querypark:
            #print(i)
            return availabilityDictionary['slots'][0]['available']
        

#This function makes a new call to the db to generate a list of notifications, generates a message, then sends out notifications via SMS or email  
def notify():
    d = bitdotio.bitdotio(apiKey)
    notify_list = []
    # selects only rows at which the specified park is available and which notifications are turned on
    fetch_avail = """
        SELECT email, pass, park, date, notifications, method, phone, modified
        FROM disreserve
        WHERE available= true AND notify = true
        """
    # message for users who have received 10 notifications for the same date/pass combination
    ck_nots = "If you wish to no longer receive notifications for this reservation, please open the following link:"
    
    #retrieve test data and store it in a list of tuples
    with d.get_connection("jimcreel/trial") as dconn:
        dcursor = dconn.cursor()
        dcursor.execute(fetch_avail)
        not_records = dcursor.fetchall()
    with open ('notifications.log', 'a') as logfile:
        if not not_records:
            now = datetime.now()
            no_not = "No notifications sent at {}".format(now)
            logfile.write(no_not)
        else:
            for notification in not_records:
                logfile.write("$s\n" % notification)

    # iterate through the list of notifications and generate the message      
    for row in range(len(not_records)):
        email = not_records[row][0]
        magickey = not_records[row][1]
        park = not_records[row][2]
        match park:
            case 'DLR_DP':
                parkfull = 'for Disneyland'
            case 'DLR_CA':
                parkfull = 'for California Adventure'
            case 'ANY':
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
                account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
                auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
                client = Client(account_sid, auth_token)
                message = client.messages \
                        .create(
                        body = msg,
                        from_ = "+15107267039",
                        to='+1{}'.format(phone)
                        )
                print(message.sid)
                # increment the notification counter
                f = bitdotio.bitdotio(apiKey)
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
