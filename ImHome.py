# coding:utf-8
#! /usr/bin/env python
from smartcard.System import readers
import time
import boto3

# aws
TARGET_ARN = INPUT_YOUR_ENDPOINT_ARN_TO_NOTIFY

# Change state threashold
MAX_COUNT = 2

# RFID
TARGET_TAG_ID = INPUT_FIRST_PAGE_ID

# handshake cmd needed to initiate data transfer
COMMAND = [0xFF, 0xCA, 0x00, 0x00, 0x00]

# sleep interval
SLEEP_INTERVAL = 3

# message
MESSAGE_IN = INPUT_MESSAGE_FOR_COMING_IN
MESSAGE_OUT = INPUT_MESSAGE_FOR_GOING_OUT

# Parameters
sns = boto3.resource('sns') # sns
platform_endpoint = sns.PlatformEndpoint('arn') # sns endpoint
at_home = False # use is at home or not
count = 0 # count

# get all the available readers
r = readers()
print "Available readers:", r

# Parse RFID data
def stringParser(dataCurr):
    if isinstance(dataCurr, tuple):
        temp = dataCurr[0]
        code = dataCurr[1]
    else:
        temp = dataCurr
        code = 0
    dataCurr = ''
    for val in temp:
        dataCurr += format(val, '#04x')[2:] # += bf
    dataCurr = dataCurr.upper()
    if (code == 144):
        return dataCurr

def sendMessage(message):
    result = platform_endpoint.publish(
            TargetArn=TARGET_ARN,
            Message=message
    )
    print(result)

# Send notification if RFID state is changed
def tagState(isFounded):
    global at_home
    global count

    print 'Cart state: %d ' % (isFounded)
    print 'count: %d ' % (count)

    # count incremented if RFID and at_home state is different
    should_notify = False
    if(isFounded != at_home):
        if(count == MAX_COUNT):
            at_home = not at_home
            should_notify = True
            count = 0
        else:
            count += 1
    else:
        count = 0
    # send message
    if(should_notify):
        message = MESSAGE_OUT if not at_home else MESSAGE_IN
        sendMessage(message)


# Start reading tag
def readTag():
    readingLoop = 1
    while(readingLoop):
        try:
            connection = reader.createConnection()
            status_connection = connection.connect()
            connection.transmit(COMMAND)
            resp = connection.transmit([0xFF, 0xB0, 0x00, 0, 0x04])
            dataCurr = stringParser(resp)

            print dataCurr
            if(dataCurr == TARGET_TAG_ID):
                print "RFID founded"
                tagState(True)
            time.sleep(SLEEP_INTERVAL)
        except Exception,e:
            tagState(False)
            time.sleep(SLEEP_INTERVAL)
            continue

if __name__ == "__main__":
    reader = r[0]
    print "Using:", reader

    readTag()
