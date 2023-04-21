#!/bin/sh

import os
import io
import json
import requests
import logging
import re
from google.cloud import vision
from google.cloud.vision_v1 import types
import pandas as pd
from pull_data import initiate_data_pull
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()
cwd = os.getenv("PROJECT_DIR")
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(cwd, "cloud_vision_api.json")

logging.basicConfig(filename='{}/app.log'.format(cwd), format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

today = datetime.today()
    

def process_img(img, pattern):
    try:
        logging.info("Trying to process image and extract text information.")
        client = vision.ImageAnnotatorClient()
        with io.open(img, 'rb') as image_file:
            content = image_file.read()
        image = types.Image(content=content)
        response = client.text_detection(image=image)
        text = response.text_annotations[0].description
        logging.info("Extracted text - {}".format(text))
        location_ids = re.findall(pattern, text)
        location_ids = [id.replace(" ", "_") for id in location_ids]
        logging.info("Found the location ids - {}".format(location_ids))
    except Exception as e:
        logging.error("Unable to process image. Error - {}".format(e))
    return location_ids
    

def main():
    img_name, img_loc = os.getenv("IMAGE_NAME"), os.getenv("IMAGE_LOCATION")
    locations_count, pattern = os.getenv("LOCATIONS_COUNT"), os.getenv("PATTERN")
    
    data_pull_resp = initiate_data_pull()
    print("Image Pull - {}".format(data_pull_resp["Status"]))

    image = "{}{}.png".format(os.path.join(cwd, img_loc, img_name), today.strftime("%Y-%m-%d"))

    if (not os.path.exists(image)) or (data_pull_resp["Status"] != "Success"):
        return {"Status": "Failure"}
    
    location_ids = process_img(image, pattern)

    if len(location_ids) != int(locations_count):
        print("Required locations count is not same as the ones we received.")
    else:
        print("Count: OK")
        print("Location IDs - {}".format(location_ids))

if __name__=="__main__":
    main()

