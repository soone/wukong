#!/bin/env python

import cv, Image

capture = cv.CaptureFromCAM(0)
cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_WIDTH, 1024)
cv.SetCaptureProperty(capture, cv.CV_CAP_PROP_FRAME_HEIGHT, 768)
img = cv.QueryFrame(capture)
pi = Image.fromstring("RGB", cv.GetSize(img), img.tostring())
pi.save("./a.jpg", format = "JPEG")
