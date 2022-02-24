# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import cv2 as cv

import requests

import asyncio
import sys
import signal
import threading
from azure.iot.device.aio import IoTHubModuleClient


# Event indicating client stop
stop_event = threading.Event()


def create_client():
    client = IoTHubModuleClient.create_from_edge_environment()

    # Define function for handling received messages
    async def receive_message_handler(message):
        # NOTE: This function only handles messages sent to "input1".
        # Messages sent to other inputs, or to the default, will be discarded
        if message.input_name == "input1":
            print("the data in the message received on input1 was ")
            print(message.data)
            print("custom properties are")
            print(message.custom_properties)
            print("forwarding mesage to output1")
            await client.send_message_to_output(message, "output1")

    try:
        # Set handler on the client
        client.on_message_received = receive_message_handler
    except:
        # Cleanup if failure occurs
        client.shutdown()
        raise

    return client


async def processFrame(frameBytes):

    multipart_form_data = {'frame': ("frame.jpg", frameBytes)}

    response = requests.post('http://10.10.2.101:8080/analyze',files=multipart_form_data)

    return response.json()

async def run_sample(client):
    # Customize this coroutine to do whatever tasks the module initiates
    # e.g. sending messages
    global cap


    while True:

        ret, frame = cap.read()

        if ret:

            frameBytes = cv.imencode( '.jpg', frame)[1].tobytes()
            r = processFrame(frameBytes)

            print (r)

        await asyncio.sleep(500)


def main():
    global cap

    if not sys.version >= "3.5.3":
        raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
    print ( "Camera Module for Python" )

    cap = cv.VideoCapture(0)

    if not cap.isOpened():
        print("Error opening camera!!!")
        exit()

    # NOTE: Client is implicitly connected due to the handler being set on it
    client = create_client()

    # Define a handler to cleanup when module is is terminated by Edge
    def module_termination_handler(signal, frame):
        print ("Camera Module stopped by Edge")
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
        cap.release()
        loop.run_until_complete(client.shutdown())
        loop.close()


if __name__ == "__main__":
    main()
