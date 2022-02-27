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

from CaptureManager import CaptureManager

# Event indicating client stop
stop_event = threading.Event()

def resize(img, scale_percent):

    width = int(img.shape[1] * scale_percent)
    height = int(img.shape[0] * scale_percent)

    dim = (width, height)

    return cv.resize(img, dim, interpolation = cv.INTER_AREA)

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


def processFrame(frameBytes):

    multipart_form_data = {'frame': ("frame.jpg", frameBytes)}

    response = requests.post('http://MobileDetectionModule:8080/analyze',files=multipart_form_data)

    return response.json()

async def run_sample(client):
    # Customize this coroutine to do whatever tasks the module initiates
    # e.g. sending messages
    global cap

    while True:

        frame = cap.getLastFrame()

        frame = resize(frame, 0.5)

        frameBytes = cv.imencode( '.jpg', frame)[1].tobytes()
        r = processFrame(frameBytes)

        print (r)


        await asyncio.sleep(1)


def main():
    global vf
    global cap

    if not sys.version >= "3.5.3":
        raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
    print ( "Camera Module for Python" )

    print("Python3 cv2 version: %s" % cv.__version__)

    vf = cv.VideoCapture(0)

    if not vf.isOpened():
        print("Error opening camera!!!")
        exit()

    cap = CaptureManager(vf).start()

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
        vf.release()
        loop.run_until_complete(client.shutdown())
        loop.close()


if __name__ == "__main__":
    main()
