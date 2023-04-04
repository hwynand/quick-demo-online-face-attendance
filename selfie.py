import cv2

video_capture = cv2.VideoCapture(1)

while True:
    result, image = video_capture.read()

    cv2.imshow("Live cam", image)

    # If press `q` on keyboard, take a photo and break the loop
    if cv2.waitKey(1) & 0xFF == ord("q"):
        cv2.imwrite("selfie.png", image)
        break

# release
video_capture.release()
cv2.destroyAllWindows()
