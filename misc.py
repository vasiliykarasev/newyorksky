import cv2
import numpy as np

def get_sky_color(img):
    # Hacks: take top 20% of the image and compute median.
    top = img[0:int(img.shape[0] * 0.25), :, :]
    return [
        int(np.median(top[:, :, 2])),
        int(np.median(top[:, :, 1])),
        int(np.median(top[:, :, 0])),
    ]


def compute_image_stats(img):
    mean_color = cv2.mean(img)
    # bgr->rgb
    img_data = {}
    img_data['mean_color'] = \
        (int(mean_color[2]), int(mean_color[1]), int(mean_color[0]))
    img_data['sky_color'] = get_sky_color(img)
    return img_data



