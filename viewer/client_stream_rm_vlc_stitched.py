from pynput import keyboard
import cv2
import hl2ss
import hl2ss_lnm
import numpy as np

# Settings --------------------------------------------------------------------

# HoloLens address
host = "192.168.2.38"

# Ports and labels for the cameras we are using
camera_info = [
    (hl2ss.StreamPort.RM_VLC_LEFTFRONT, "Left Front"),
    (hl2ss.StreamPort.RM_VLC_RIGHTFRONT, "Right Front")
]

# Operating mode
mode = hl2ss.StreamMode.MODE_0

# Framerate denominator
divisor = 1

# Video encoding profile
profile = hl2ss.VideoProfile.H265_MAIN

# Initialize clients for each camera
clients = []
for port, _ in camera_info:
    client = hl2ss_lnm.rx_rm_vlc(host, port, mode=mode, divisor=divisor, profile=profile)
    client.open()
    clients.append(client)

def on_press(key):
    global enable
    enable = key != keyboard.Key.esc
    return enable

# Initialize keyboard listener
enable = True
listener = keyboard.Listener(on_press=on_press)
listener.start()

def rotate_image(image, angle):
    (h, w) = image.shape[:2]
    center = (w // 2, h // 2)
    matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, matrix, (w, h))
    return rotated

def stitch_images(image1, image2):
    # Detect ORB keypoints and descriptors
    orb = cv2.ORB_create(nfeatures=3000)
    keypoints1, descriptors1 = orb.detectAndCompute(image1, None)
    keypoints2, descriptors2 = orb.detectAndCompute(image2, None)

    # Match descriptors using BFMatcher
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(descriptors1, descriptors2)
    matches = sorted(matches, key=lambda x: x.distance)

    # Extract location of good matches
    points1 = np.zeros((len(matches), 2), dtype=np.float32)
    points2 = np.zeros((len(matches), 2), dtype=np.float32)

    for i, match in enumerate(matches):
        points1[i, :] = keypoints1[match.queryIdx].pt
        points2[i, :] = keypoints2[match.trainIdx].pt

    # Find homography matrix
    H, mask = cv2.findHomography(points2, points1, cv2.RANSAC)

    # Warp the second image to align with the first image
    height, width = image1.shape
    warped_image2 = cv2.warpPerspective(image2, H, (width + width // 2, height))

    # Create Gaussian pyramids
    G1 = image1.copy()
    G2 = warped_image2[:, :width].copy()
    gp1 = [G1]
    gp2 = [G2]
    for i in range(6):
        G1 = cv2.pyrDown(G1)
        G2 = cv2.pyrDown(G2)
        gp1.append(G1)
        gp2.append(G2)

    # Create Laplacian pyramids
    lp1 = [gp1[5]]
    lp2 = [gp2[5]]
    for i in range(5, 0, -1):
        L1 = cv2.subtract(gp1[i - 1], cv2.pyrUp(gp1[i]))
        L2 = cv2.subtract(gp2[i - 1], cv2.pyrUp(gp2[i]))
        lp1.append(L1)
        lp2.append(L2)

    # Add left and right halves of images in each level
    LS = []
    for l1, l2 in zip(lp1, lp2):
        rows, cols = l1.shape
        ls = np.hstack((l1[:, :cols // 2], l2[:, cols // 2:]))
        LS.append(ls)

    # Reconstruct image
    ls_ = LS[0]
    for i in range(1, 6):
        ls_ = cv2.pyrUp(ls_)
        ls_ = cv2.add(ls_, LS[i])

    return ls_

while enable:
    frames = []
    for client in clients:
        data = client.get_next_packet()
        frames.append(data.payload)

    # Rotate Left Front and Right Front images
    frame_leftfront = rotate_image(frames[0], -90)  # Rotate 90 degrees counter-clockwise
    frame_rightfront = rotate_image(frames[1], 90)  # Rotate 90 degrees clockwise

    # Stitch Left Front and Right Front images
    stitched_frame = stitch_images(frame_leftfront, frame_rightfront)

    cv2.imshow("Stitched Left Front and Right Front", stitched_frame)

    cv2.waitKey(1)

# Close clients
for client in clients:
    client.close()

listener.join()
cv2.destroyAllWindows()
