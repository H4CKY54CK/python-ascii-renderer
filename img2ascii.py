#!/usr/bin/env python3

import os
import io
import re
import sys
import time
import math
import shutil
import requests
import argparse
import itertools
from PIL import Image, ImageOps



def _round(value):
    ivalue = int(value)
    rem = value - ivalue
    if rem > .5:
        return ivalue + 1
    return ivalue


def get_frames(source, save=False, dest=None):
    result = []
    with Image.open(source) as img:
        for i in range(img.n_frames):
            img.seek(i)
            frame = img.copy()
            fdata = {"frame": frame, "duration": img.info["duration"],}
            result.append(fdata)
    return result


def error_msg(msg):
    nbytes = sys.stderr.write("%s" % msg)
    sys.stderr.flush()
    return nbytes


def convert_image_to_ascii(source, size, *, bg=False, fg=True, chars=" .,:;+*%#@", force_size=False, timeout=3, autofit=False):
    # if isinstance(source, np.ndarray):
    #     img = Image.fromarray(source)
    if isinstance(source, Image.Image):
        img = source.copy()
        # source.close()
    elif re.match(r"(https?\:\/\/)(www\.)?", source):
        try:
            with requests.get(source, timeout=timeout) as res:
                img = Image.open(io.BytesIO(res.content))
        except TimeoutError:
            error_msg("[img2ascii error]: request has timed out after %s seconds\n" % (timeout,))
            return 1
    elif os.path.exists(source):
        img = Image.open(source)
    else:
        error_msg("[img2ascii error]: invalid path: %r\n" % (source,))
        return 1

    # Normalize the mode
    img = img.convert("RGBA")

    # Basic check for correct size format
    if autofit:
        width, height = os.get_terminal_size()
        img = ImageOps.contain(img, (width, height))
    else:
        width, height = size or (None, None)
        if (width and not height) or (height and not width):
            img.thumbnail((width or img.width, height or img.height))
        elif not force_size:
            img.thumbnail(size)
        else:
            img = img.resize(size)

    # This works and is faster than list(img.getdata())
    #pixels = list(itertools.batched(img.tobytes(), len(img.getbands())))
    # But this is easier and probably more reliable lol
    pixels = list(img.getdata())
    data = []

    fgbg = (38 if fg else None, 48 if bg else None)
    for pixel in pixels:
        r, g, b, a = pixel

        # Get appropriate "pixel" from charset.
        a = _round(a / 255 * (len(chars) - 1))
        c = chars[a]

        data.append("".join("\x1b[%d;2;%d;%d;%dm" % (z, r, g, b) for z in fgbg if z is not None) + c)

    img.close()

    # Add a "bold" prefix and "reset" suffix to each line. It's called responsibility.
    return "\n".join("\x1b[1m" + " ".join(row) + "\x1b[m" for row in itertools.batched(data, img.width))


def main(args):
    if args.width or args.height:
        args.size = (args.width, args.height)
    kwargs = {key: val for key, val in args._get_kwargs() if key not in ("width", "height", "out", "quiet") and val is not None}

    if not args.source.casefold().endswith(".gif"):
        result = convert_image_to_ascii(**kwargs)
        if args.out:
            with open(args.out, "w") as f:
                f.write(result + "\n")
            if args.quiet is False:
                print("Wrote to file: %r" % (args.out,))
        else:
            if args.quiet is False:
                print(result)
    else:
        sys.stdout.write("\x1b[H\x1b[s")
        sys.stdout.flush()
        frames = get_frames(args.source)
        last = time.time()
        total = sum(i["duration"] for i in frames) / 1000
        # Play for at least 5 seconds
        loops = 5 / total
        if loops < 1:
            loops = 1
        loops = math.ceil(loops)
        last = 0
        timestamps = []
        for _ in range(loops):
            for entry in frames:
                frame = entry["frame"]
                duration = entry["duration"]
                kw = kwargs | {"source": frame}
                converted = convert_image_to_ascii(**kw)
                sys.stdout.write("\x1b[2J\x1b[u%s" % (converted,))
                sys.stdout.flush()
                delay = duration / 1000
                # While it hasn't been 'delay' since 'last'
                while True:
                    now = time.time()
                    if now > last + delay:
                        break
                    # Sleep for 100 µs
                    time.sleep(.0001)
                timestamps.append(now)
                # Set last
                last = now

    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)


    # Positional
    pgroup = parser.add_argument_group("Positional Arguments")
    pgroup.add_argument("source", type=str,
                        help="Either the path to an image on disk or a URL that points to the image.")

    # Options
    ogroup = parser.add_argument_group("Options")
    ogroup.add_argument("--timeout", "-T", type=int, metavar="N",
                        help="Set the max timeout in seconds for requesting a URL. Ignored otherwise. (Default: 3)")
    ogroup.add_argument("--chars", "-C", type=str, metavar="ABC",
                        help="The character set to use for the varying levels of pixel brightness.")
    ogroup.add_argument("--out", "-o", type=str, metavar="FILE",
                        help="Instead of writing to stdout, dump to the provided file (WILL OVERWRITE EXISTING FILE).")

    # Dimension group
    dgroup = parser.add_argument_group("Size Options")
    dgroup = dgroup.add_mutually_exclusive_group(required=False)
    dgroup.add_argument("--width", "-x", type=int, metavar="X",
                        help="Force width to X, preserving aspect ratio. This is useful for ensuring that the final \
                              ASCII rendition will fit within a given width.")
    dgroup.add_argument("--height", "-y", type=int, metavar="Y",
                        help="Force height to Y, preserving aspect ratio. This is useful for ensuring that the final \
                              ASCII rendition will fit within a given height.")
    dgroup.add_argument("--size", type=int, nargs=2, default=(100, 100), metavar=("X", "Y"),
                        help="Resize the image to X width by Y height, preserving aspect ratio. If you need to resize \
                              while NOT preserving the aspect ratio, add the boolean option --force-size.")

    # Booleans
    bgroup = parser.add_argument_group("True/False Flags")
    bgroup.add_argument("--autofit", "-F", action="store_true",
                        help="Fit the final render to the terminal size (preserves aspect ratio).")
    bgroup.add_argument("--fg", action=argparse.BooleanOptionalAction, default=True,
                        help="Whether to use the pixel colors in the foreground of the ASCII. (Default: True)")
    bgroup.add_argument("--bg", action=argparse.BooleanOptionalAction, default=False,
                        help="Whether to use the pixel colors in the background of the ASCII. (Default: False)")
    bgroup.add_argument("--force-size", action="store_true",
                        help="This forces the image to be resized without any regard to aspect ratio. (Yes, this will \
                              squash your image. If it were perfectly square, you wouldn't need to to do this.).")
    bgroup.add_argument("--quiet", "-q", action="store_true",
                        help="Do not print anything to stdout (Default: False).")
    bgroup.add_argument("--help", "-h", action="help",
                        help="Show this help message and exit.")

    args = parser.parse_args()

    ret = 0
    try:
        # sys.stdout.write("\x1b[?1049h")
        sys.stdout.write("\x1b[?47h")
        sys.stdout.flush()
        main(args)
    except KeyboardInterrupt as e:
        sys.stdout.write("\n")
        sys.stdout.flush()
        ret = 1
    finally:
        sys.stdout.write("\x1b[2J\x1b[?47l")
        # sys.stdout.write("\x1b[?1049l")
        sys.stdout.flush()

    sys.exit(ret)
