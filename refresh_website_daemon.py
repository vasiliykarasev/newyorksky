from mako.template import Template
import os
import cv2
import config
import utils
import glog as log
import datetime
import argparse
import time

class Cache:
    def __init__(self):
        self.data = {}

    def add(self, key, item):
        self.data[key] = item

    def get(self, key):
        if key in self.data:
            return self.data[key]
        else:
            return None

    def size(self):
        return len(self.data)

cache = Cache()


def compute_image_stats(img):
    mean_color = cv2.mean(img)
    # bgr->rgb
    img_data = {}
    img_data['mean_color'] = \
        (int(mean_color[2]), int(mean_color[1]), int(mean_color[0]))
    print img_data['mean_color']
    return img_data


def get_images():
    filenames = sorted(utils.get_image_filenames())
    # Sort in reverse chrono order.
    filenames.reverse()
    # Take the last few images.
    step = 1
    num_to_take = 6 * 48   # must be a multiple of 8
    print len(filenames)
    filenames = filenames[0:step * num_to_take:step]
    print len(filenames)
    images = []
    num_cache_misses = 0
    print "Number of entries in cache {}".format(cache.size())
    for idx, f in enumerate(filenames):
        print "Processing {}/{}".format(idx, len(filenames))
        img_data = cache.get(f)
        if img_data is None:
            num_cache_misses += 1

            print "Processing {}".format(f)
            img = utils.read_remote_image(f)
            img_data = compute_image_stats(img)
            cache.add(f, img_data)

        images.append({
            'url_thumb':
            f,
            'url':
            f.replace(config.THUMBS_PATH, config.IMAGES_PATH),
            'mean_color':
            img_data['mean_color'],
        })
    cache_miss_frac = num_cache_misses / float(len(filenames))
    print "Fraction of cache misses {}".format(cache_miss_frac)
    return images

def index():
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    images = get_images()
    filename = os.path.join(config.TEMPLATE_PATH, 'index.html')
    return Template(filename=filename).render(images=images, update_date=date)


def about():
    filename = os.path.join(config.TEMPLATE_PATH, 'about.html')
    return Template(filename=filename).render()



def render_templates(output_path, upload_to_s3=True):
    for fn, func in [('index.html', index), ('about.html', about)]:
        local_filename = os.path.join(output_path, fn)
        open(local_filename, 'w').write(func())
        if upload_to_s3:
            bucket = utils.get_s3_bucket()
            bucket.upload_file(
                local_filename,
                fn,
                ExtraArgs={
                    'ContentType': "text/html",
                    'ACL': "public-read"
                })
            log.info("Uploading {} to S3".format(fn))
    if upload_to_s3:
        bucket = utils.get_s3_bucket()
        for fn in os.listdir('static'):
            fn = os.path.join('static', fn)
            bucket.upload_file(fn, fn, ExtraArgs={'ACL': "public-read"})
            log.info("Uploading {} to S3".format(fn))


def spin(args):
    while True:
      render_templates(args.output_path)
      time.sleep(args.interval)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--interval', type=int, default=60, help='How often to sync with s3?')
    parser.add_argument('--output_path', default='/tmp/')
    args = parser.parse_args()
    
    spin(args)
