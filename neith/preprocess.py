import numpy as np
import operator

from skimage import measure
from skimage import transform

from collections import namedtuple

Rectangle = namedtuple('Rectangle', 'xmin ymin xmax ymax')

# the percent of overlap required to remove a contour
IOU_THRESHOLD = 0
# used by sci-kit image to extract contours from an image
CONTOUR_LEVEL = 0.8


def remove_overlap_contours(contours):
    to_remove = []
    for i1, contour1 in enumerate(contours):
        min = np.min(contour1, axis=0)
        max = np.max(contour1, axis=0)
        rec1 = Rectangle(min[1], min[0], max[1], max[0])
        area1 = (rec1[2] - rec1[0]) * (rec1[3] - rec1[1])
        for i2, contour2 in enumerate(contours):
            min = np.min(contour2, axis=0)
            max = np.max(contour2, axis=0)
            rec2 = Rectangle(min[1], min[0], max[1], max[0])
            area2 = (rec2[2] - rec2[0]) * (rec2[3] - rec2[1])
            if contour1 is not contour2:
                iou = get_iou(rec1, rec2)
                if iou > IOU_THRESHOLD:
                    if area1 > area2 and i2 not in to_remove:
                        to_remove.append(i2)
                    elif i1 not in to_remove:
                        to_remove.append(i1)
    contours_new = []
    for i, c in enumerate(contours):
        if i not in to_remove:
            contours_new.append(c)
    return contours_new


def equation_char_list(pixels):
    # use sci-kit image to find the contours of the image
    contours = measure.find_contours(pixels, CONTOUR_LEVEL)
    # calls an algorithm on the contours to remove unwanted overlapping contours like the holes in 6's, 8's, and 9's
    contours = remove_overlap_contours(contours)

    # populate a dictionary with key of the left most x coordinate of the contour and value of the resized contour
    resized_char_dict = dict()
    for n, contour in enumerate(contours):
        min = np.min(contour, axis=0)
        max = np.max(contour, axis=0)
        resized_contour = transform.resize(pixels[int(min[0]):int(max[0]), int(min[1]):int(max[1])], (32, 32))
        resized_char_dict[min[1]] = resized_contour

    # sort the map by key (left most x coordinate of the contour)
    sorted_dict = sorted(resized_char_dict.items(), key=operator.itemgetter(0))
    # extract the contours from the sorted dictionary into a list
    char_imgs = np.asarray([i[1] for i in sorted_dict])
    # normalize the contours by subtracting 0.5 to each pixel value
    np.subtract(char_imgs, 0.5, out=char_imgs)
    return char_imgs


def get_iou(rec1, rec2):
    # determine the coordinates of the intersection rectangle
    x_left = max(rec1[0], rec2[0])
    y_top = max(rec1[1], rec2[1])
    x_right = min(rec1[2], rec2[2])
    y_bottom = min(rec1[3], rec2[3])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    # The intersection of two axis-aligned bounding boxes is always an
    # axis-aligned bounding box
    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    # compute the area of both AABBs
    rec1_area = (rec1[2] - rec1[0]) * (rec1[3] - rec1[1])
    rec2_area = (rec2[2] - rec2[0]) * (rec2[3] - rec2[1])

    # compute the intersection over union by taking the intersection
    # area and dividing it by the sum of prediction + ground-truth
    # areas - the interesection area
    iou = intersection_area / float(rec1_area + rec2_area - intersection_area)
    return iou
