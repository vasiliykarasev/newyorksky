import os
import time
import argparse
import boto3
import cv2
import glog as log
import config

class ImageWriter:
    def __init__(self,
                 interval=1,
                 output_path='/tmp/',
                 device_id=0,
                 upload_to_s3=False):
        self._output_path = output_path
        self._interval = interval
        self._cap = cv2.VideoCapture(device_id)
        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self._thumb_scale = 0.125
        self._image_scale = 1.0

        log.check(self._cap.isOpened())

        if upload_to_s3:
            s3 = boto3.resource('s3')
            self._bucket = s3.Bucket(config.BUCKET_NAME)
        else:
            self._bucket = None
        if not os.path.exists(os.path.join(self._output_path, 'images')):
            os.mkdir(os.path.join(self._output_path, 'images'))
        if not os.path.exists(os.path.join(self._output_path, 'thumbs')):
            os.mkdir(os.path.join(self._output_path, 'thumbs'))
        self.warmup()

    def spin(self):
        while True:
            if not self.process():
                break

            time.sleep(self._interval)

    def warmup(self):
        for i in range(10):
            success, image = self._cap.read()
            if not success:
                log.info("Could not grab image from camera.")
            time.sleep(1)

    def process(self):
        success, image = self._cap.read()
        if not success:
            log.info("Could not grab image from camera.")
            return False

        # Do extra processing, if any.
        if self._image_scale != 1.0:
            image_size = (int(image.shape[1] * self._image_scale),
                          int(image.shape[0] * self._image_scale))
            image = cv2.resize(image, image_size)

        self.write(image)
        return True

    def write(self, image):
        timestamp = long(time.time())

        basename = '{}.jpg'.format(timestamp)

        self._write_image(image, basename, 'images')

        thumb_size = (int(image.shape[1] * self._thumb_scale),
                      int(image.shape[0] * self._thumb_scale))
        thumb = cv2.resize(image, thumb_size)
        self._write_image(thumb, basename, 'thumbs')

    def _write_image(self, image, basename, subdir):
        output_filename = os.path.join(self._output_path, subdir, basename)
        cv2.imwrite(output_filename, image)
        log.info("Writing {}".format(output_filename))
        if self._bucket is not None:
            try:
                remote_filename_key = os.path.join(subdir, basename)
                log.info("Uploading to s3 ({})".format(remote_filename_key))
                self._bucket.upload_file(output_filename, 
                                         remote_filename_key,
                                         ExtraArgs={
                                             'ACL': "public-read",
                                             'ContentType': "image/jpeg",
                                             })
                # Don't remove -- we may need these images elsewhere, and
                # it's expensive to download them back from S3.
                #os.remove(output_filename)
            except Exception as error:
                log.error(error)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--interval',
        default=config.CAPTURE_PERIOD_SEC,
        type=int,
        help='Capture interval')
    parser.add_argument(
        '--device_id', default=0, type=int, help='Camera device id')
    parser.add_argument(
        '--output_path', default=config.LOCAL_CACHE_DIR, help='Output path')
    parser.add_argument(
        '--no-upload',
        default=False,
        action='store_true',
        help='Upload to S3?')

    args = parser.parse_args()

    upload = True if not args.no_upload else False

    image_writer = ImageWriter(
        interval=args.interval,
        output_path=args.output_path,
        device_id=args.device_id,
        upload_to_s3=upload)
    image_writer.spin()


if __name__ == "__main__":
    main()
