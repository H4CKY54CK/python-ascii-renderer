import os
import sys
import cv2
import time
import numpy
from PIL import Image
import sys



def _round(value):
    ivalue = int(value)
    rem = value - ivalue
    if rem > .5:
        return ivalue + 1
    return ivalue

def convert_frame_to_ascii(frame, size, *, bg=False, fg=True, chars=" .,:;+*%#@", force_size=False, timeout=3):
    # Frame will be a numpy array
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    # New plan. Convert to RGBA regardless, as that "specific downsampling quality loss issue" was actually just a gap
    # in knowledge on my part. This hopefully now accomodates all images and image types that PIL supports.
    img = img.convert("RGBA")

    # Basic check for correct size format
    width, height = size or (None, None)
    if (width and not height) or (height and not width):
        img.thumbnail((width or img.width, height or img.height))
    elif not force_size:
        img.thumbnail(size)
    else:
        img = img.resize(size)

    pixels = img.load()
    data = [["" for _ in range(img.width)] for _ in range(img.height)]

    fgbg = (38 if fg else None, 48 if bg else None)
    for x in range(img.width):
        for y in range(img.height):
            r, g, b, a = pixels[x,y]

            # Get appropriate "pixel" from charset.
            a = _round(a / 255 * (len(chars) - 1))
            c = chars[a]

            data[y][x] = "".join("\x1b[%d;2;%d;%d;%dm" % (z, r, g, b) for z in fgbg if z is not None) + c

    # Add a bold prefix and reset suffix to each line. It's called responsibility.
    return "\n".join("\x1b[1m" + " ".join(row) + "\x1b[m" for row in data)



def convert_video_to_ascii(source):
    vid = cv2.VideoCapture(source)
    nframes = vid.get(cv2.CAP_PROP_FRAME_COUNT)
    fps = vid.get(cv2.CAP_PROP_FPS)
    delay = 1 / fps
    last = time.time()
    print(f"\x1b[2J\x1b[H\x1b[s")
    while True:
        success, frame = vid.read()
        if not success:
            break
        ascii_frame = convert_frame_to_ascii(frame, size=(100,100))
        while time.time() - delay < last:
            time.sleep(.001)
            pass
        last = last + delay
        print(f"\x1b[u{ascii_frame}")




def main():
    convert_video_to_ascii(sys.argv[1])


if __name__ == '__main__':
    main()
