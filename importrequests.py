import requests
import json
import bitdotio

import os
from twilio.rest import Client
from datetime import datetime
from datetime import date

import smtplib, ssl
from email.message import EmailMessage

#get the api key
apiKey=os.environ.get('BIT_DOT_IO_API_KEY')

#target site
url=os.environ.get('DLR_URL')
wdwUrl=os.environ.get('WDW_URL')
bitDotIOConn=os.environ.get('BIT_DOT_IO_URL')


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

#Data is separated into a list of calendar availability with 5 elements separated by key level
inspire_avail = parse_json[0]['availabilities']
believe_avail = parse_json[1]['availabilities']
enchant_avail = parse_json[2]['availabilities']
imagine_avail = parse_json[3]['availabilities']
dream_avail = parse_json[4]['availabilities']
incredi_avail=wdwParse_json[0]['availabilities']
sorceror_avail=wdwParse_json[1]['availabilities']
pirate_avail=wdwParse_json[2]['availabilities']
pixie_avail=wdwParse_json[3]['availabilities']

def main():
    dlrResort = "DLR"
    wdwResort = "WDW"
    today=date.today()
    d1 = today.strftime("%Y-%m-%d")
    print('removing past dates')
    remove_past_dates(today)
    #print(today)
    print('getting list of dates')
    query_list=get_list()
    print('making list of queries')
    new_data=make_queries(query_list)
    print(new_data)
    #print(new_data)
    print('updating new data')
    update_data(new_data)
    print('creating list of notifications')
    notify()



def remove_past_dates(today):
#This function updates the remote db to remove any past dates
    a = bitdotio.bitdotio(apiKey)
    check_dates = """
        
        SELECT row_to_json(disreserve) from disreserve where date < '{}'""".format(today)
        
    with a.get_connection(bitDotIOConn) as conn:
                cursor = conn.cursor()
                cursor.execute(check_dates)
                dateList = cursor.fetchall()
    
    for date in range(len(dateList)):
        
        arrDate = dateList[date][0]['date']
        arrPass = dateList[date][0]['pass']
        arrPark = dateList[date][0]['park']
        arrUser = dateList[date][0]['userid']
        
        arrDateObject = datetime.strptime(arrDate, '%Y-%m-%d').date()
        print(arrDateObject, today)
        if arrDateObject < today:
            move_dates = """
            INSERT INTO oldresdates
            SELECT * from disreserve WHERE date = '{}' AND pass = '{}' AND park = '{}' AND userid = '{}'""".format(arrDate, arrPass, arrPark, arrUser)
            remove_dates = """
            DELETE from disreserve WHERE date = '{}' AND pass = '{}'AND park = '{}' AND userid = '{}'
            """.format(arrDate, arrPass, arrPark, arrUser)
            with a.get_connection(bitDotIOConn) as conn:
                cursor = conn.cursor()
                cursor.execute(move_dates)
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
        with c.get_connection(bitDotIOConn) as conn:
                    cursor = conn.cursor()
                    cursor.execute(update_db)
#This function connects to the remote db and returns a list of dates,
#keys, and parks that are flagged for notifications

def get_list():
    #connect to bit.io with api key
    
    b = bitdotio.bitdotio(apiKey)
    
    #check to see which dates are being requested by users
    retrieve_data = """
        SELECT DISTINCT pass, park, date, resort
        FROM disreserve
        """
    #retrieve dates
    with b.get_connection(bitDotIOConn) as conn:
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
    print('getting park availability')
    for row in range(len(query_list)):
        #print(query_list[row])
        check_date = query_list[row][2]
        check_park = query_list[row][1]
        check_pass = query_list[row][0]
        check_resort = query_list[row][3]
        #print(check_pass)
        match check_pass:
            case 'inspire-key-pass':
                check_pass_json = inspire_avail
            case 'believe-key-pass':
                check_pass_json = believe_avail
            case 'enchant-key-pass':
                check_pass_json = enchant_avail
            case 'dream-key-pass':
                check_pass_json = dream_avail
            case 'imagine-key-pass':
                check_pass_json = imagine_avail
            case 'disney-incredi-pass':
                check_pass_json = incredi_avail
            case 'disney-sorceror-pass':
                check_pass_json = sorceror_avail
            case 'disney-pirate-pass':
                check_pass_json = pirate_avail
            case 'disney-pixie-dust-pass':
                check_pass_json = pixie_avail
       
        #print(check_pass_json)    
        if check_resort == 'DLR':
            if check_park == 'ANY':
                dlrResult = get_park_availability(check_date,check_pass_json,'DLR_DP')
                dcaResult = get_park_availability(check_date,check_pass_json,'DLR_CA')
                if dlrResult or dcaResult:
                    dlrResult = True
            else: dlrResult = get_park_availability(check_date,check_pass_json,check_park)
            #print(check_date, check_park, result)    
            dlrResult_tup = (check_date, check_pass, check_park, dlrResult)
            results_list.append(dlrResult_tup)
        if check_resort == 'WDW':
            if check_park == 'ANY':
                mkResult = get_park_availability(check_date,check_pass_json,'WDW_MK')
                epResult = get_park_availability(check_date,check_pass_json,'WDW_EP')
                akResult = get_park_availability(check_date,check_pass_json,'WDW_AK')
                hsResult = get_park_availability(check_date,check_pass_json,'WDW_HS')
                if mkResult or epResult or akResult or hsResult:
                    wdwResult = True
            else: wdwResult = get_park_availability(check_date,check_pass_json,check_park)
            #print(check_date, check_park, result)    
            wdwResult_tup = (check_date, check_pass, check_park, wdwResult)
            results_list.append(wdwResult_tup)
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
        SELECT email, pass, park, date, notifications, method, phone, modified, resort
        FROM disreserve
        WHERE available= true AND notify = true
        """
    update_notes ="""
        UPDATE disreserve 
        SET notifications = notifications + 1, modified = NOW()
        WHERE available = true AND notify = true"""

    # message for users who have received 10 notifications for the same date/pass combination
    ck_nots = "If you wish to no longer receive notifications for this reservation, please open the following link:"
    
    #retrieve test data and store it in a list of tuples
    with d.get_connection(bitDotIOConn) as dconn:
        dcursor = dconn.cursor()
        dcursor.execute(update_notes)
        dcursor.execute(fetch_avail)
        not_records = dcursor.fetchall()
    print('logging info to file...')
    if os.path.exists('/home/jimcreel/Documents/git/disResScraper/notifications.log'):
        with open ('/home/jimcreel/Documents/git/disResScraper/notifications.log', 'a') as logfile:
            records_string = str(not_records).strip('[]')
            if records_string =='':
                now = datetime.now()
                no_not = "No notifications sent at {}\n".format(now)
                logfile.write(no_not)  
    else:
        with open ('notifications.log', 'a') as logfile:
            records_string = str(not_records).strip('[]')
            if records_string =='':
                now = datetime.now()
                no_not = "No notifications sent at {}\n".format(now)
                logfile.write(no_not)
            
# iterate through the list of notifications and generate the message      
    for row in range(len(not_records)):
        email = not_records[row][0]
        magickey = not_records[row][1]
        park = not_records[row][2]
        resort = not_records[row][8]
        if (resort == 'DLR'):
            passOrKey = 'key'
            resUrl='https://tinyurl.com/5n8yetcw'
        else:
            passOrKey = 'pass'
            resUrl='https://tinyurl.com/5dewmzje'
        match park:
            case 'DLR_DP':
                parkfull = 'for Disneyland'
            case 'DLR_CA':
                parkfull = 'for California Adventure'
            case 'ANY':
                parkfull = ''
            case 'WDW_MK':
                parkfull = 'for Magic Kingdom'
            case 'WDW_EP':
                parkfull = 'for Epcot'
            case 'WDW_AK':
                parkfull = 'for Animal Kingdom'
            case 'WDW_HS':
                parkfull = 'for Hollywood Studios'
        date = not_records[row][3]
        #datetime_obj = datetime.strptime(date, '%y-%m-%d')
        #print(datetime_obj)
        now = datetime.now()
        nots = not_records[row][4]
        method = not_records[row][5]
        phone = not_records[row][6]
        msg = ("Reservations {} are available on {} for {} {} holders. Visit {} to make your reservation.").format(parkfull,date,magickey,passOrKey,resUrl)
        #actual path to script log
        if os.path.exists('/home/jimcreel/Documents/git/disResScraper/notifications.log'):
            with open('/home/jimcreel/Documents/git/disResScraper/notifications.log', 'a') as logfile:
                logmessage = 'Notification sent on {} via {} - {} - {} - {} - {}\n'.format(now,method, parkfull,date, nots, phone, email)
                logfile.write(logmessage)
        #test environment path to log
        else:
            with open('notifications.log', 'a') as logfile:
                logmessage = 'Notification sent on {} via {} - {} - {} - {} - {}\n'.format(now,method, parkfull,date, nots, phone, email)
                logfile.write(logmessage)
        #print(msg)
       # print("to:",email,".","Reservations for",park,"are available for",date)
        #print(not_records[row][4])
        #print(method)
        match method:
            case 'phone':
                phone_notifications(msg, phone, date, parkfull, magickey,nots)
            case 'email':
                email_notifications(email,date,parkfull,magickey)
#this function sends an sms notification
def phone_notifications(msg, phone, date, parkfull, magickey,nots):
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
        

 #this function sends an email notification
def email_notifications(email, date, parkfull, magickey):
    print('attempting to send email')
    smtp_server = 'az1-ss106.a2hosting.com'
    port = 465
    send_email = 'notifications@magic-reservations.com'
    receiver_email = email
    password = os.environ.get('MAGIC_RESERVATIONS_EMAIL_PASSWORD')
    context = ssl.create_default_context()
    emailMsg = EmailMessage()
    emailMsg.set_content('''
           
        Get ready to make your reservation! Park reservations are available on {} {}!\n
        Visit https://tinyurl.com/5n8yetcw to make your reservation.\n
        Thank you for using magic-reservations.com!'''.format(date,parkfull))
    emailMsg['Subject'] = 'Reservations are available for {} keys on {}'.format(magickey,date)
    emailMsg['From'] = send_email
    emailMsg['To'] = receiver_email
    
    with smtplib.SMTP_SSL(smtp_server,port,context=context) as server:
        server.login(send_email,password)
        server.send_message(emailMsg, send_email, receiver_email)
     # increment the notification counter
    f = bitdotio.bitdotio(apiKey)
   
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
