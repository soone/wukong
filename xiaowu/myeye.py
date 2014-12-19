#!/bin/env python

import cv, Image, time

capture = cv.CaptureFromCAM(0)
cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 600)
cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 400)
for i in range(10):
    img = cv.QueryFrame(capture)
    pi = Image.fromstring("RGB", cv.GetSize(img), img.tostring())
    pi.save("./pic/" + str(i) + ".jpg", format = "JPEG")
    time.sleep(3)
