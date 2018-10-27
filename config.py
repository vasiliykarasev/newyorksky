BUCKET_NAME = 'newyorksky.live'
IMAGES_PATH = 'images'
THUMBS_PATH = 'thumbs'
TEMPLATE_PATH = 'templates/'

# Local directory where images/timelapse results are saved.
LOCAL_CACHE_DIR='/tmp/'

# How often are images captured from the camera?
CAPTURE_PERIOD_SEC = 5 * 60.0
# Describes how many images are displayed on the front page.
TIMELINE_DURATION_SEC = 14 * 24 * 3600.0
# Describes long the timelapse video is.
TIMELAPSE_DURATION_SEC = 7 * 24 * 3600.0

# How often the website is refreshed and synced with S3.
HTML_REFRESH_PERIOD_SEC = 5.0 * 60
# How often the timelapse video is regenerated.
TIMELAPSE_REFRESH_PERIOD_SEC = 1 * 24 * 3600.0

