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

    # It may seem strange to convert it to itself, but it solves a specific downsampling quality loss issue.
    # Also, convert to RGBA if the image is RGB. That way, we have a default alpha value without any fuss.
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

    if isinstance(args.out, str):
        with open(args.out, "w") as f:
            f.write(res + "\n")
        if args.quiet is False:
            print("Wrote to file: %r" % (args.out,))
    else:
        if args.quiet is False:
            print(res)

    return 0


def main(argv=None):
    argv = (argv or sys.argv)[1:]
    # parser = argparse.ArgumentParser(conflict_handler="resolve")
    parser = argparse.ArgumentParser(add_help=False)


    # Positional
    pgroup = parser.add_argument_group("Positional Arguments")
    pgroup.add_argument("source", type=str,
                        help="Either the path to an image on disk or a URL that points to the image.")

    # Options
    ogroup = parser.add_argument_group("Options")
    ogroup.add_argument("--timeout", "-T", type=int, default="3", metavar="N",
                        help="Set the max timeout in seconds for requesting a URL. Ignored otherwise. (Default: 3)")
    ogroup.add_argument("--chars", "-C", type=str, default=" .,:;+*%#@", metavar="ABC",
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

    args = parser.parse_args(argv)
    return convert_image_to_ascii(args)


if __name__ == "__main__":
    exit(main())