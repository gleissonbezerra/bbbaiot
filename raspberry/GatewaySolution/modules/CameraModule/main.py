# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.

import cv2 as cv
import requests
import os
import uuid
import json

import asyncio
import sys
import signal
import threading
from azure.iot.device.aio import IoTHubModuleClient
from azure.iot.device import Message

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
    return client


def processFrame(frameBytes):
    global INFERENCE_URL

    multipart_form_data = {'frame': ("frame.jpg", frameBytes)}

    response = requests.post(INFERENCE_URL,files=multipart_form_data, timeout=2)

    return response.json()

async def run_sample(client):
    # Customize this coroutine to do whatever tasks the module initiates
    # e.g. sending messages
    global cap

    INFERENCE_INTERVAL = float(os.getenv('INFERENCE_INTERVAL', "1.0"))


    while True:

        frame = cap.getLastFrame()

        frame = resize(frame, 0.5)

        frameBytes = cv.imencode( '.jpg', frame)[1].tobytes()
        r = processFrame(frameBytes)

        #print (r)

        if r != None and "detections" in r:

            del r['fps']
            
            strMessage = json.dumps(r)

            msg = Message(strMessage)
            msg.message_id = uuid.uuid4()

            await client.send_message_to_output(msg, "detectionsOutput")


        await asyncio.sleep(INFERENCE_INTERVAL)


def main():
    global vf
    global cap
    global INFERENCE_URL

    if not sys.version >= "3.5.3":
        raise Exception( "The sample requires python 3.5.3+. Current version of Python: %s" % sys.version )
    print ( "Camera Module for Python" )

    print("Python3 cv2 version: %s" % cv.__version__)

    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', "0"))
    CAMERA_INTERVAL = float(os.getenv('CAMERA_INTERVAL', "1.0"))
    INFERENCE_URL = os.getenv('INFERENCE_URL', "")

    vf = cv.VideoCapture(CAMERA_INDEX)

    if not vf.isOpened():
        print("Error opening camera!!!")
        exit()

    cap = CaptureManager(vf, CAMERA_INTERVAL).start()

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
