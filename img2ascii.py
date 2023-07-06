import os
import io
import re
import sys
import requests
import argparse
from PIL import Image




def convert_image_to_ascii(args):
    # Allow images to be filepaths or URLs.
    if re.match(r"(https?\:\/\/)(www\.)?", args.source):
        try:
            with requests.get(args.source, timeout=args.timeout) as res:
                img = Image.open(io.BytesIO(res.content))
        except TimeoutError:
            sys.stderr.write("[img2ascii error]: request has timed out after %s seconds\n" % (args.timeout,))
            return 1
    elif os.path.exists(args.source):
        img = Image.open(args.source)
    else:
        sys.stderr.write("[img2ascii error]: invalid path: %r\n" % (args.source,))
        return 1

    # Strange, I know, but it solves a downsampling quality loss issue.
    if img.mode in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    elif img.mode == "L":
        img = img.convert("L")
    else:
        sys.stderr.write("[img2ascii error]: have not implemented mode %r yet\n" % (img.mode,))
        return 1

    # Basic check for correct size format
    if args.width or args.height:
        img.thumbnail((args.width or img.width, args.height or img.height))
    elif not args.force_size:
        img.thumbnail(args.size)
    else:
        img = img.resize(args.size)

    pixels = img.load()
    data = [["" for _ in range(img.width)] for _ in range(img.height)]

    fgbg = (38 if args.fg else None, 48 if args.bg else None)
    for x in range(img.width):
        for y in range(img.height):
            r, g, b, a = pixels[x,y]

            # Get appropriate "pixel" from charset.
            a = int(a // 2.55 // (len(args.chars) + 1))
            c = args.chars[a]

            data[y][x] = "".join("\x1b[%d;2;%d;%d;%dm" % (z, r, g, b) for z in fgbg if z is not None) + c

    # Add a bold prefix and reset suffix to each line. It's called responsibility.
    res = "\n".join("\x1b[1m" + " ".join(row) + "\x1b[m" for row in data)

    # # Because I can
    # pixels = img.load()
    # data = [[pixels[x,y] for x in range(img.width)] for y in range(img.height)]
    # data = [[f"\x1b[1;38;2;{r};{g};{b}m{charset[int(a//2.55//(len(charset)+1))]}" for r,g,b,a in item] for item in data]
    # data = "\n".join(" ".join(item) for item in data) + "\x1b[m"
    # print(data)

    if isinstance(args.out, str):
        with open(args.out, "w") as f:
            f.write(res)
        if args.quiet is False:
            print("Wrote to file: %r" % (args.out,))
    else:
        if args.quiet is False:
            print(res)

    return 0


def main(argv=None):
    argv = (argv or sys.argv)[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=str,
                        help="either the path to an image on disk or a URL that points to the image")
    parser.add_argument("--timeout", "-T", type=int, default="3", metavar="N",
                        help="Set the max timeout in seconds for requesting a URL. Ignored otherwise. (Default: 3)")
    parser.add_argument("--chars", "-C", type=str, default=" .,:;+*%#@", metavar="ABC",
                        help="The character set to use for the varying levels of pixel brightness.")
    parser.add_argument("--out", "-o", type=str, metavar="FILE",
                        help="Instead of writing to stdout, dump to the provided file (WILL OVERWRITE EXISTING FILE).")

    # Booleans
    parser.add_argument("--fg", action=argparse.BooleanOptionalAction, default=True,
                        help="Whether to use the pixel colors in the foreground of the ASCII. (Default: True)")
    parser.add_argument("--bg", action=argparse.BooleanOptionalAction, default=False,
                        help="Whether to use the pixel colors in the background of the ASCII. (Default: False)")
    parser.add_argument("--force-size", action="store_true",
                        help="This forces the image to be resized without any regard to aspect ratio. (Yes, this will \
                              squash your image. If it were perfectly square, you wouldn't need to to do this.).")
    parser.add_argument("--quiet", "-q", action="store_true",
                        help="Do not print anything to stdout (Default: False).")

    # Dimension group
    dgroup = parser.add_mutually_exclusive_group(required=False)
    dgroup.add_argument("--width", "-x", type=int, metavar="X",
                        help="Force width to X, preserving aspect ratio. This is useful for ensuring that the final \
                              ASCII rendition will fit within a given width.")
    dgroup.add_argument("--height", "-y", type=int, metavar="Y",
                        help="Force height to Y, preserving aspect ratio. This is useful for ensuring that the final \
                              ASCII rendition will fit within a given height.")
    dgroup.add_argument("--size", type=int, nargs=2, default=(100, 100),
                        help="Resize the image to X width by Y height, preserving aspect ratio. If you need to resize \
                              while NOT preserving the aspect ratio, add the boolean option --force-size.")

    args = parser.parse_args(argv)
    return convert_image_to_ascii(args)

if __name__ == "__main__":
    exit(main())