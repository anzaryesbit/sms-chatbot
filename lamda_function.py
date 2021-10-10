from __future__ import print_function
from datetime import datetime
import urllib.request
import os
import sys
import re
import pymysql
import base64
from utility import *
from botocore.exceptions import ClientError

# gets json information from the twilio api, handles authentication (username: Account SID, password: Auth Token)
# url is https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json -> {} is account SID
# inputs: url -> string, username -> string, password -> string
# output: dictionary (json data)
def get_json(url, username=None, password=None):
    ''' Function to get a json dictionary from a website.
        url - a string'''

    # sets up a password manager
    password_mngr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    password_mngr.add_password(None, url, username, password)
    handler = urllib.request.HTTPBasicAuthHandler(password_mngr)
    
    #creates an opener so that all urllib.request calls goes to the opener we created with the authentication
    opener = urllib.request.build_opener(handler)
    opener.open(url)
    urllib.request.install_opener(opener)
    
    #pulls the json data
    with urllib.request.urlopen(url) as response:
        html = response.read()
    htmlstr = html.decode("utf-8")
    return json.loads(htmlstr)

# extracts the json data and returns a list of the most recent interaction
# input: dict (json data from twilio)
# output: list [# message is from (str), message body (str), date message was sent (str)]
def extract_received(JSON):
    received = []
    for i in range(len(JSON['messages'])):
        if JSON['messages'][i]['body'].upper() == 'HELLO':
            message_dict = JSON['messages'][0: i+1]
            return message_dict[::-1]

#puts the responses into a tuple list, first item is a hash of the phone number
# input: list of dictionaries with info about messages
# output: tuple (hash, option, address, feedback)
def get_user_response(dict_list, event):
    bodies = []
    for diction in dict_list:
        if diction['to'] == "+19543887990":
            if diction['body'].upper() == 'HELLO':
                hash = hash_function(diction['from'])
                print(hash)
                bodies.append(hash)
            else:
                bodies.append(diction['body'])
    print(bodies)
    return [str(bodies[0]), int(bodies[2]), str(bodies[1]), str(bodies[3])]

#message response, dictates what message will return to the statement
def message_response(body):
    if body.upper() == "HELLO":
       return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
           "<Response><Message><Body>You’ve reached the feedback number of the KIRA project. Your feedback is valuable to us. If you are comfortable, please tell us your name and location. If not, press the * button. </Body></Message></Response>"
    elif body == "*":
        return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
           "<Response><Message><Body>What can I help you with? Reply 1 for quality of services, 2 for doctors' availability, 3 for feedback related to medications, or 4 for any other types of feedback</Body></Message></Response>"
    else:
       return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
           "<Response><Message><Body>Please tell us your feedback. When finished with your message please put STOP.</Body></Message></Response>"

# writes a hash function from the receiving phone number and date (month, day, year, hour, minute) as a tuple
# allows for a unique item to be placed in the sql table
# input: string (Phone number with the + sign)
# output: string (hash)
def hash_function(phone_number):
    number = int(phone_number[1:])
    now = datetime.now()
    time = int(now.strftime("%d%m%y%H%M%S"))
    two_tuple = (number, time)
    return str(hash(two_tuple))

def persist_to_db(data):
    
    try:
        logger.info("Looking up credentials to DB")
        logger.info("Connecting to DB")
        # configuration if using amazon secrets
        # conn = pymysql.connect(host=secrets["host"], # URL or hostname of the database in Oregon  
        #                        user=secrets["username"],
        #                        password=secrets["password"],
        #                        database=secrets["dbname"],
        #                        connect_timeout=5
        #                        )
        conn = pymysql.connect(host='chatbot-response.cxpevijcux2x.us-east-1.rds.amazonaws.com',
                               user=#input user name,
                               password=# input password,
                               database=#input database name,
                               connect_timeout=5
                               )
        logger.info("Creating cursor to DB")
        cur = conn.cursor()
        # Create a new record
        sql = "INSERT INTO `Messages` (phone,`feedback-type`, address, feedback) VALUES (%s, %s, %s, %s)"
        logger.info("Executing query to DB")
        cur.execute(sql, [data[from], 3, '*', data])
            # connection is not autocommit by default. So you must commit to save
        # your changes
        
        logger.info("Commiting query to DB")
        conn.commit()
        conn.close()
        
        logger.info("Closing connection to DB")
    except Exception as e: 
        logger.info("An error occured {}".format(e))

def lambda_handler(event, context):
    logger = get_logger()
    logger.info("event info: {}".format(event))
    service = 0
    message = ""
    persist_to_db(event['Body'])
    if event['Body'].upper() == "HELLO":
        message = message_response(event['Body'])
    elif event['Body'].isdigit() and event['Body'] in '1 2 3 4':
        if event['Body'] not in '1 2 3 4':
            message = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
           "<Response><Message><Body>Please reply 1 for quality of services, 2 for doctors' availability, 3 for feedback related to medications, or 4 for any other types of feedback</Body></Message></Response>"
        else:    
            service = event['Body']
            print(service)
            message = message_response(event['Body'])
    elif (event['Body'] == "*" or re.match('[^\n\r]', event['Body'])) and "STOP" not in event['Body'] :
        if event != "*":
            print(event['Body'])
            message = message_response("*")
    else:
        logger.info("In else block")
        
        #get the user data from twilio's API
        URL = 'https://api.twilio.com/2010-04-01/Accounts/[Account ID]/Messages.json'
        username = #[Account ID]
        password = #[Password from Twilio]
        json_data = get_json(URL, username, password)
        received_msgs = extract_received(json_data)
        # tuple_row = ('from', 'option', 'address', 'message body')
        tuple_row = get_user_response(received_msgs, event)
        # print(tuple_row)
        message = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"\
           "<Response><Message><Body>Thank you for your feedback</Body></Message></Response>"
    return message
    
   
    
    '''
    current issues:
    You can only send 1 paragraph of feedback at the moment or else it'll send an incorrect reply
    You have to put STOP at the end of your feedback in order to indicate it is a feedbak text
    '''
