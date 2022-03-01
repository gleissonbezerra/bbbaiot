# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import asyncio
import sys
import signal
import threading
import os
import time

import json

import uuid

import smbus2

from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

# Event indicating client stop
stop_event = threading.Event()

def create_client():

    PEOPLE_ALERT_INTERVAL = float(os.getenv('PEOPLE_ALERT_INTERVAL', "10.00"))

    client = IoTHubModuleClient.create_from_edge_environment()

    # Define function for handling received messages
    async def receive_message_handler(message):
        global i2c
        global I2C_SLAVE_ADDRESS
        global alertStarted
        global alertTimer

        # NOTE: This function only handles messages sent to "input1".
        # Messages sent to other inputs, or to the default, will be discarded
        if message.input_name == "detectionsInput":

            # print("the data in the message received on detectionsInput was ")
            # print(message.data)
            # print("custom properties are")
            # print(message.custom_properties)

            #parse data to json
            jsonData = json.loads(message.data)

            #check if people is present for a while
            if jsonData != None and "detections" in jsonData:

                peopleDetected = 0

                for object in jsonData["detections"]:

                    if object["label"] == "person":
                        peopleDetected += 1

                if peopleDetected > 0:
                    if alertStarted:
                        if time.time() - alertTimer >= PEOPLE_ALERT_INTERVAL:
                            print ("Alert confirmed. Sendindg notification...")

                            strMessage = '{"type":"peopleAlert", "count":'+str(peopleDetected)+'}'

                            msg = Message(strMessage)
                            msg.message_id = uuid.uuid4()
                            msg.content_encoding = "utf-8"
                            msg.content_type = "application/json"

                            await client.send_message_to_output(msg, "alertsOutput")

                            print ("Notification sent!")

                            #send close command over i2c
                            command = "close"
                            print("Sending "+command+" to I2C slave!")
                            i2c.write_i2c_block_data(I2C_SLAVE_ADDRESS, 0, command.encode('utf-8'))			

                            alertStarted = False

                        else:
                            print ("Trying to confirm people alert...")
                    else:
                        print ("Starting people alert timer..")
                        alertStarted = True
                        alertTimer = time.time()
                else:
                    alertStarted = False
                    print ("Finished or No Alert!")




    try:
        # Set handler on the client
        client.on_message_received = receive_message_handler
    except:
        # Cleanup if failure occurs
        client.shutdown()
        raise

    return client


async def run_sample(client):
    # Customize this coroutine to do whatever tasks the module initiates
    # e.g. sending messages

    global i2c
    global I2C_BUS_NUMBER
    global I2C_SLAVE_ADDRESS

    I2C_INTERVAL = float(os.getenv('I2C_INTERVAL', "5.0"))

    while True:
        #collect temperature data 

        try:

            data = bytes(i2c.read_i2c_block_data(I2C_SLAVE_ADDRESS, 0, 32)).decode('cp855').rstrip()

            if len(data) > 0:

                # print("Received data from I2C slave")
                # print(data)

                jsonData = json.loads(data)


                if jsonData != None and "t" in jsonData and "h" in jsonData:

                    temperature = jsonData["t"]
                    humidity = jsonData["h"]

                    strMessage = '{"type":"telemetryData", "temperature":'+str(temperature)+', "humidity":'+str(humidity)+'}'

                    msg = Message(strMessage)
                    msg.message_id = uuid.uuid4()
                    msg.content_encoding = "utf-8"
                    msg.content_type = "application/json"

                    await client.send_message_to_output(msg, "telemetryOutput")

                else:

                    print("Error in get sensor data over i2C ")

        except Exception as e:

            print("I2C Manager communication error on receiving %s " % e)

            time.sleep(2)

            i2c = smbus2.SMBus(I2C_BUS_NUMBER)

            time.sleep(2)

            print("Serial BUS restarted {} at {}".format(I2C_BUS_NUMBER, I2C_SLAVE_ADDRESS))
    

        await asyncio.sleep(I2C_INTERVAL)


def main():

    global i2c
    global I2C_BUS_NUMBER
    global I2C_SLAVE_ADDRESS
    global alertStarted
    global alertTimer
    
    alertStarted = False
    alertTimer = time.time()

    I2C_BUS_NUMBER = int(os.getenv('I2C_BUS_NUMBER', "0"))
    I2C_SLAVE_ADDRESS = int(os.getenv('I2C_SLAVE_ADDRESS', 0x08))

    if not sys.version >= "3.5.3":
        raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
    print ( "Command Module for Python" )

    # NOTE: Client is implicitly connected due to the handler being set on it
    client = create_client()

    i2c = smbus2.SMBus(I2C_BUS_NUMBER)

    time.sleep(2)

    print("Serial BUS started {} at {}".format(I2C_BUS_NUMBER, I2C_SLAVE_ADDRESS))

    # Define a handler to cleanup when module is is terminated by Edge
    def module_termination_handler(signal, frame):
        print ("Command Module stopped by Edge")
        stop_event.set()

    # Set the Edge termination handler
    signal.signal(signal.SIGTERM, module_termination_handler)

    # Run the sample
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(run_sample(client))
    except Exception as e:
        print("Unexpected error %s " % e)
        raise
    finally:
        print("Shutting down IoT Hub Client...")
        loop.run_until_complete(client.shutdown())
        loop.close()

if __name__ == "__main__":
    main()
