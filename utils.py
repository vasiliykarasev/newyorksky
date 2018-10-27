import boto3
import os
import glog as log
import config
import cv2
import urllib
import numpy as np

s3 = boto3.resource('s3')
s3_bucket = s3.Bucket(config.BUCKET_NAME)

def get_s3_bucket():
    return s3_bucket

def get_image_filenames():
    filenames = []
    for obj in s3_bucket.objects.filter(Prefix=config.IMAGES_PATH):
        filenames.append(os.path.join('http://s3.amazonaws.com', config.BUCKET_NAME, obj.key))
    return filenames

def get_thumbs_filenames():
    filenames = []
    for obj in s3_bucket.objects.filter(Prefix=config.THUMBS_PATH):
        filenames.append(os.path.join('http://s3.amazonaws.com', config.BUCKET_NAME, obj.key))
    return filenames


def read_remote_image(url):
    data = urllib.urlopen(url).read()
    if len(data) == 0:
        raise Exception('No data!')
    image = np.asarray(bytearray(data), dtype="uint8")
    return cv2.imdecode(image, cv2.IMREAD_COLOR)
