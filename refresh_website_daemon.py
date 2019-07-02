import datetime
import os
import time
import shutil
import subprocess
import argparse
from mako.template import Template
from mako.lookup import TemplateLookup
import numpy as np
import cv2
import glog as log
from botocore.exceptions import EndpointConnectionError
from cache import Cache
from misc import compute_image_stats
import config
import utils
import datetime
import pytz

def overlay_timestamp_on_image(img, timestamp):
    d = datetime.datetime.fromtimestamp(timestamp, pytz.timezone('US/Eastern'))
    text = d.strftime('%4Y %02m %02d %02H:%02M')
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    cv2.putText(img, text, (10,20), font, 0.6, (255, 255, 255), 4, cv2.LINE_AA)
    cv2.putText(img, text, (10,20), font, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
    return img

def subsample_filenames(filenames):
    def is_bad_date(date):
        return d.year == 2018 and d.month < 10
    
    output = []
    MAX_GAP_SEC = 15*60
    has_file_for_day = False
    target_hour = 18
    for f in filenames:
        ts = float(os.path.splitext(os.path.basename(f))[0])
        d = datetime.datetime.fromtimestamp(ts, pytz.timezone('US/Eastern'))
        if is_bad_date(d):
            continue
        if has_file_for_day:
            if d.day == d_target.day:
                continue
            else:
                has_file_for_day = False
        
        d_target = datetime.datetime(d.year, d.month, d.day, target_hour, 0, 0, 0, pytz.timezone('US/Eastern'))
        if (d - d_target).total_seconds() < MAX_GAP_SEC:
            has_file_for_day = True
            output.append(f)
    return output

    
def make_long_timelapse_video(output_filename,
                              fps,
                              num_images_to_take,
                              image_process_lambda=None):
    filenames = sorted(utils.get_image_filenames())
    filenames.reverse()
    filenames = subsample_filenames(filenames)
    filenames = filenames[0:num_images_to_take]
    # Get filenames back into chronological orger.
    filenames.reverse()


    img = utils.read_remote_image(filenames[0])
    if image_process_lambda is not None:
        img = image_process_lambda(img)
    fourcc_func = None
    try:
        fourcc_func = cv2.VideoWriter_fourcc
    except AttributeError:
        fourcc_func = cv2.cv.FOURCC
    fourcc = fourcc_func('M', 'J', 'P', 'G')
    original_img_shape = img.shape
    video = cv2.VideoWriter(output_filename, fourcc, fps,
                            (img.shape[1], img.shape[0]))

    for idx, f in enumerate(filenames):
        print "Processing {}/{}".format(idx, len(filenames))
        local_filename = os.path.join(config.LOCAL_IMAGE_CACHE_DIR,
                                      os.path.basename(f))
        print local_filename, os.path.exists(local_filename)

        if os.path.exists(local_filename):
            print "Getting {} from cache".format(local_filename)
            img = cv2.imread(local_filename)
        else:
            try:
                print "Getting {} from s3".format(f)
                img = utils.read_remote_image(f)
            except Exception as e:
                print "Caught {}".format(e)
                continue
            cv2.imwrite(
                os.path.join(config.LOCAL_IMAGE_CACHE_DIR, os.path.basename(f)), img)
        # Process image.
        if image_process_lambda is not None:
            img = image_process_lambda(img)
        timestamp = float(os.path.splitext(os.path.basename(local_filename))[0])
        img = overlay_timestamp_on_image(img, timestamp)
        # Verify that current image dimensions match the dimensions that we
        # created the video with -- otherwise the video will not be playable.
        if img.shape[0] != original_img_shape[0] or img.shape[
                1] != original_img_shape[1]:
            print "Image shape ({}) does not match original shape {}".format(
                img.shape, original_img_shape)
            img = cv2.resize(img, (original_img_shape[1], original_img_shape[0]))
            print "Resized to {}".format(img.shape)
        video.write(img)



def make_timelapse_video(output_filename,
                         fps,
                         num_images_to_take,
                         image_process_lambda=None):
    filenames = sorted(utils.get_image_filenames())
    filenames.reverse()
    filenames = filenames[0:num_images_to_take]
    # Get filenames back into chronological orger.
    filenames.reverse()

    img = utils.read_remote_image(filenames[0])
    if image_process_lambda is not None:
        img = image_process_lambda(img)
    fourcc_func = None
    try:
        fourcc_func = cv2.VideoWriter_fourcc
    except AttributeError:
        fourcc_func = cv2.cv.FOURCC
    fourcc = fourcc_func('M', 'J', 'P', 'G')
    original_img_shape = img.shape
    video = cv2.VideoWriter(output_filename, fourcc, fps,
                            (img.shape[1], img.shape[0]))

    for idx, f in enumerate(filenames):
        print "Processing {}/{}".format(idx, len(filenames))
        local_filename = os.path.join(config.LOCAL_IMAGE_CACHE_DIR,
                                      os.path.basename(f))
        print local_filename, os.path.exists(local_filename)

        if os.path.exists(local_filename):
            print "Getting {} from cache".format(local_filename)
            img = cv2.imread(local_filename)
        else:
            try:
                print "Getting {} from s3".format(f)
                img = utils.read_remote_image(f)
            except Exception as e:
                print "Caught {}".format(e)
                continue
            cv2.imwrite(
                os.path.join(config.LOCAL_IMAGE_CACHE_DIR, os.path.basename(f)), img)
        # Process image.
        if image_process_lambda is not None:
            img = image_process_lambda(img)
        timestamp = float(os.path.splitext(os.path.basename(local_filename))[0])
        img = overlay_timestamp_on_image(img, timestamp)
        # Verify that current image dimensions match the dimensions that we
        # created the video with -- otherwise the video will not be playable.
        if img.shape[0] != original_img_shape[0] or img.shape[
                1] != original_img_shape[1]:
            print "Image shape ({}) does not match original shape {}".format(
                img.shape, original_img_shape)
            img = cv2.resize(img, (original_img_shape[1], original_img_shape[0]))
            print "Resized to {}".format(img.shape)
        video.write(img)


def make_timelapse_video_for_web(output_filename,
                                 fps,
                                 num_images_to_take,
                                 image_process_lambda=None):
    temp_filename = os.path.splitext(output_filename)[0] + '.mp4'
    make_timelapse_video(temp_filename, fps, num_images_to_take,
                         image_process_lambda)
    # Re-encode_video, sigh.
    subprocess.check_call([
        'ffmpeg', '-y', '-i', temp_filename, '-vcodec', 'libvpx', '-qmin', '0',
        '-qmax', '1', '-crf', '1', '-q:v', '1', output_filename
    ])
    os.remove(temp_filename)


class Renderer:
    def __init__(self, output_path, upload_to_s3):
        self.lookup = TemplateLookup(directories=[os.getcwd()])
        self.output_path = output_path
        self.upload_to_s3 = upload_to_s3
        self.thumb_cache = Cache()
        self.thumb_cache_filename = os.path.join(output_path, 'cache.pkl')
        log.info("Initializing thumbnail cache in {}".format(
            self.thumb_cache_filename))
        # Take a few days' worth of images.
        self.num_images_on_index = int(config.TIMELINE_DURATION_SEC /
                                       config.CAPTURE_PERIOD_SEC)
        self.num_timelapse_images = int(config.TIMELAPSE_DURATION_SEC /
                                        config.CAPTURE_PERIOD_SEC)
        self.image_step = 1
        self.last_timelapse_rendered_timestamp = 0
        self.already_uploaded_static_files = False

    def render_templates(self):
        # Render and upload templates.
        for fn, func in [
            ('index.html', self.index),
            ('about.html', self.about),
            ('timelapse.html', self.timelapse),
        ]:
            local_filename = os.path.join(self.output_path, fn)
            open(local_filename, 'w').write(func())
            log.info("Rendered {}".format(local_filename))
            if self.upload_to_s3:
                bucket = utils.get_s3_bucket()
                bucket.upload_file(
                    local_filename,
                    fn,
                    ExtraArgs={
                        'ContentType': "text/html",
                        'ACL': "public-read"
                    })
                log.info("Uploading {} to S3".format(fn))
        # Upload static files.
        if not self.already_uploaded_static_files:
            self.already_uploaded_static_files = True
            if os.path.exists(os.path.join(self.output_path, 'static')):
                shutil.rmtree(os.path.join(self.output_path, 'static'))
            shutil.copytree('static', os.path.join(self.output_path, 'static'))
            if self.upload_to_s3:
                bucket = utils.get_s3_bucket()
                for fn in os.listdir('static'):
                    fn = os.path.join('static', fn)
                    bucket.upload_file(fn, fn, ExtraArgs={'ACL': "public-read"})
                    log.info("Uploading {} to S3".format(fn))


    def should_render_timelapse(self):
        dt = time.time() - self.last_timelapse_rendered_timestamp
        return dt > config.TIMELAPSE_REFRESH_PERIOD_SEC

    def did_render_timelapse(self):
        self.last_timelapse_rendered_timestamp = time.time()

    def render_timelapse_video(self):
        # Make and upload a timelapse video.
        print "Making a timelapse"
        video_filename = os.path.join(self.output_path, 'timelapse.webm')
        make_timelapse_video_for_web(
            video_filename,
            fps=15,
            num_images_to_take=self.num_timelapse_images)
        if self.upload_to_s3:
            bucket = utils.get_s3_bucket()
            bucket.upload_file(
                video_filename,
                os.path.join('video', os.path.basename(video_filename)),
                ExtraArgs={'ACL': "public-read",
                           'ContentType': "video/webm"})

    def get_images(self, step=1, num_to_take=1000):
        if os.path.exists(self.thumb_cache_filename):
            print "Loading from {}".format(self.thumb_cache_filename)
            self.thumb_cache = Cache.load(self.thumb_cache_filename)

        filenames = sorted(utils.get_thumbs_filenames())
        if len(filenames) == 0:
            return []
        # Sort in reverse chrono order.
        filenames.reverse()
        # Take the last few images.
        filenames = filenames[0:step * num_to_take:step]
        images = []
        num_cache_misses = 0
        print "Number of entries in cache {}".format(self.thumb_cache.size())
        for idx, f in enumerate(filenames):
            print "Processing {}/{}".format(idx, len(filenames))
            img_data = self.thumb_cache.get(f)
            if img_data is None:
                num_cache_misses += 1
                print "Processing {}".format(f)
                try:
                    img = utils.read_remote_image(f)
                except Exception as e:
                    print "Could not read {}; exception {}".format(f, e)
                    continue
                img_data = compute_image_stats(img)
                self.thumb_cache.add(f, img_data)

            images.append({
                'url_thumb_dirname': os.path.dirname(f),
                'url_image_dirname': os.path.dirname(f).replace(config.THUMBS_PATH, config.IMAGES_PATH),
                'url_basename': os.path.basename(f), 
                'sky_color': img_data['sky_color'],
            })
        cache_miss_frac = num_cache_misses / float(len(filenames))
        print "Fraction of cache misses {}".format(cache_miss_frac)
        print "Dumping cache to disk: {}".format(self.thumb_cache_filename)
        Cache.save(self.thumb_cache, self.thumb_cache_filename)
        return images

    def index(self):
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        images = self.get_images(self.image_step, self.num_images_on_index)
        filename = os.path.join(config.TEMPLATE_PATH, 'index.html')
        return Template(
            filename=filename, lookup=self.lookup).render(
                images=images, update_date=date)

    def about(self):
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        filename = os.path.join(config.TEMPLATE_PATH, 'about.html')
        return Template(
            filename=filename, lookup=self.lookup).render(update_date=date)

    def timelapse(self):
        date = datetime.datetime.fromtimestamp(
            self.last_timelapse_rendered_timestamp).strftime("%Y-%m-%d %H:%M")
        filename = os.path.join(config.TEMPLATE_PATH, 'timelapse.html')
        return Template(
            filename=filename, lookup=self.lookup).render(update_date=date)


def spin(args):
    counter = 0
    renderer = Renderer(args.output_path, args.upload)
    while True:
        try:
            renderer.render_templates()
            if args.timelapse and renderer.should_render_timelapse():
                try:
                    renderer.render_timelapse_video()
                    renderer.did_render_timelapse()
                except Exception as e:
                    print "Couldn't generate timelapse {}".format(e)
            print "Sleeping."
            counter += 1
            time.sleep(args.interval)
        except (IOError, EndpointConnectionError) as err:
            log.warning('Encountered {}'.format(err))
            time.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--interval',
        type=int,
        default=config.HTML_REFRESH_PERIOD_SEC,
        help='How often to sync with s3?')
    parser.add_argument('--output_path', default=config.LOCAL_CACHE_DIR)
    parser.add_argument('--upload', dest='upload', action='store_true')
    parser.add_argument('--no-upload', dest='upload', action='store_false')
    parser.set_defaults(upload=True)
    parser.add_argument('--timelapse', dest='timelapse', action='store_true')
    parser.add_argument(
        '--no-timelapse', dest='timelapse', action='store_false')
    parser.set_defaults(timelapse=True)
    args = parser.parse_args()

    spin(args)
