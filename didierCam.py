# coding: utf8
import glob
import os
import pygame
import shlex
import subprocess
from time import sleep, time
import RPi.GPIO as GPIO
from picamera import PiCamera

# 2 commands needed to make the ramdisk if planning to run from ramdisk to gain some speed
# sudo mkdir /mnt/ramdisk
# sudo mount -t tmpfs -o size=50m tmpfs /mnt/ramdisk

# folder = "/mnt/ramdisk/"
tmp_folder = u"/tmp/didierCam/"
final_folder = u"/home/pi/didierCam"

fuzzpercent = u"20%"

# A changer selon la taille de ta camera
width = 640
height = 480

# GPIO pin
pin_camera_btn = 21  # pin du bouton de déclenchement
pin_left_btn = 22  # pin du bouton pour changer background à gauche
pin_right_btn = 23  # pin du bouton pur changer background à droite
pin_stop_btn = 24  # pin pour l'arrêt

# Initialisation des ports GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_camera_btn, GPIO.IN, pull_up_down=GPIO.PUD_UP) # assign GPIO pin to take photo

# create Picamera instance
camera = picamera.PiCamera()
camera.rotation = 270  # Change this value to set the correct rotation (depending on how your camera is mounted)
camera.annotate_text_size = 80
camera.resolution = (width, height)  # take photos at this resolution
camera.hflip = True  # When preparing for photos, the preview will be flipped horizontally.

# create a (hopefully) unique part for saved files.
leader = str(time())
print(u"leader is " + leader)

# use glob to catalog all .jpg files in the folder to get the backgrounds
bgimages = glob.glob(tmp_folder + u'tmpBackground/*.jpg')
print (u"len bgimages : " + str(len(bgimages)))
for x in range(0, len(bgimages)):
    os.remove(bgimages[x])
print(u"deleted images")
sleep(0.1)

bgimages = glob.glob(final_folder + u'sourcebg/*.jpg')
print(u"bgimages is " + str(bgimages))
for x in range(0, len(bgimages)):
    sections = bgimages[x].split(u"/")
    bgimage = sections[len(sections) - 1]
    print(u"background is " + bgimage)
    commandis = u"convert " + final_folder + u"sourcebg/" + bgimage + u"  -resize " + str(width) + "x" + str(
        height) + u" " + tmp_folder + u"tmpBackground/" + bgimage

    print(u"\n\r")
    os.system(commandis)

bgimages = glob.glob(tmp_folder + u'tmpBackground/*.jpg')

print(bgimages)
bgnum = len(bgimages)
print(u"bgnum is " + str(bgnum))

# set up pygame 
pygame.init()
screen = pygame.display.set_mode((width, height), )
pygame.display.set_caption(u"didierCam")

# set camera resolution
camera.resolution = (width, height)
camera.vflip = True  # A voir si necessaire

# do first capture to use to get Chroma Key
camera.capture(tmp_folder + u'imagecam.png')

# Get Chroma Key RGB value for top left corner (10 pixels in and 10 pixels down)
command_line = u"/usr/bin/convert -limit thread 4 " + tmp_folder + u"imagecam.png[1x1+10+10] -format '%[fx:int(255*r)],%[fx:int(255*g)],%[fx:int(255*b)]' info:"
args = shlex.split(command_line)
out = subprocess.Popen(args, stdout=subprocess.PIPE)
output, err = out.communicate()
stroutput = str(output)
start = stroutput.split(u"'")
rgb = start[0].split(u",")
red = int(rgb[0])
green = int(rgb[1])
blue = int(rgb[2])
redh = str(hex(red))
greenh = str(hex(green))
blueh = str(hex(blue))
if len(redh) == 3:
    redhash = u"0" + redh[len(redh) - 1]
else:
    redhash = str(redh[2:])
if len(greenh) == 3:
    greenhash = u"0" + greenh[len(greenh) - 1]
else:
    greenhash = str(greenh[2:])
if len(blueh) == 3:
    bluehash = u"0" + blueh[len(blueh) - 1]
else:
    bluehash = str(blueh[2:])
rgbnum = redhash + greenhash + bluehash
print (rgbnum)

savenum = 1
imagenum = 0

imagebg = pygame.image.load(bgimages[imagenum])


# variable use to stay in while unless QUIT is executed
running = True
changebg = u""
doprint = -1  # -1 pas d'impression, 0 on imprime, 1,2,3,4,5 le decompte


# Defining callback
def set_do_print(channel):
    global doprint
    doprint = 5


def set_left(channel):
    global changebg
    changebg = u"left"


def set_right(channel):
    global changebg
    changebg = u"right"


def set_stop(channel):
    global running
    running = False


GPIO.add_event_detect(pin_camera_btn, GPIO.RISING, callback=set_do_print)  # add rising edge detection on a channel
GPIO.add_event_detect(pin_left_btn, GPIO.RISING, callback=set_left)  # add rising edge detection on a channel
GPIO.add_event_detect(pin_right_btn, GPIO.RISING, callback=set_right)  # add rising edge detection on a channel
GPIO.add_event_detect(pin_stop_btn, GPIO.RISING, callback=set_stop)  # add rising edge detection on a channel

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            # change the background
            if event.key == pygame.K_LEFT:
                changebg = u"left"

            # change the background
            if event.key == pygame.K_RIGHT:
                changebg = u"right"

            # Save the current image
            if event.key == pygame.K_RETURN:
                doprint = 5

            if event.key == pygame.K_q:
                running = False
        print(u"checking gamepad")

    # Change the background
    if changebg == u"left":
        imagenum = imagenum - 1
        if imagenum == -1:
            imagenum = bgnum - 1

    if changebg == u"right":
        imagenum = imagenum + 1
        if imagenum == bgnum:
            imagenum = 0

    # reset cghangebg so it doesn't keep changing
    changebg = u""

    # Print
    if doprint == 0:
        savedimage = final_folder + u"saved/didier" + leader + str(savenum) + u".jpg"
        pygame.image.save(screen, savedimage)
        savenum = savenum + 1
        # Print
        os.system(u"lpr "+savedimage)
        print(u"image saved")
        doprint = -1

    # capture image
    camera.capture(tmp_folder + u'imagecam.png')
    # add transparency to image based on sample from above.  
    print(u"get transparent image")
    os.system(u'/usr/bin/convert -limit thread 4 ' + tmp_folder + u'imagecam.png -fuzz ' + fuzzpercent + u' -transparent "#' + rgbnum + u' " ' + tmp_folder + u'imagecamt.png')
    # load image so pygame can display it
    print(u"Add the images together")
    # Background
    screen.fill((255, 255, 255))
    imagebg = pygame.image.load(bgimages[imagenum])
    screen.blit(imagebg, (0, 0))
    # Photo
    imagecam = pygame.image.load(tmp_folder + u'imagecamt.png')
    screen.blit(imagecam, (0, 0))
    # Overlay
    imageover = pygame.image.load(final_folder + u'overlay/overlay.png')
    screen.blit(imageover, (0, 0))
    # Decompte
    if doprint > 0:
        image_decompte = pygame.image.load(final_folder + u'overlay/overlay_' + doprint + u'.png')
        screen.blit(image_decompte, (0, 0))
        doprint -= 1
    # Mise a jour de l'affichage
    pygame.display.update()
    print(u"all added")

print(u"Bye bye shuting down RPI")
os.system(u"shutdown -h now")