import os
import io
import re
import sys
import requests
import argparse
import itertools
from PIL import Image


def _convert(source, *, size=tuple(), full=False, output=None, color=True, alpha=True, characters=' .,:;+*%#@'):
    if re.match(r"https?\:\/\/", source):
        try:
            with requests.get(source, timeout=3) as response:
                img = Image.open(io.BytesIO(response.content))
        except TimeoutError:
            sys.stderr.write("Request for URL has timed out.\n")
            return 1
        except KeyboardInterrupt as e:
            sys.stderr.write("\nCancelled by user.\n")
            return 1
        except Exception as e:
            sys.stderr.write("I was already doing poor error handling. At least now I'm only handling the errors poorly.\n")
            return 1
    elif os.path.exists(source):
        img = Image.open(source)
    else:
        sys.stderr.write("Could not locate provided filepath.\n")
        return 1


    if color is False:
        img = img.convert("L")
    elif alpha is False:
        img = img.convert("RGB")
    elif alpha is True:
        img = img.convert("RGBA")

    if size:
        img.thumbnail(size)


    data = [[] for _ in range(img.height)]

    step = 101 / len(characters) # account for 0

    for x,y in itertools.product(range(img.width), range(img.height)):
        if color is True and alpha is True:
            r,g,b,a = img.getpixel((x,y))
            if full:
                prefix = "\x1b[48;2;%d;%d;%dm\x1b[38;2;%d;%d;%dm" % (r, g, b, r, g, b)
            else:
                prefix = "\x1b[1m\x1b[38;2;%d;%d;%dm" % (r, g, b)
            suffix = "\x1b[0m"
        elif color is True and alpha is False:
            r,g,b = img.getpixel((x,y))
            if full:
                prefix = "\x1b[48;2;%d;%d;%dm\x1b[38;2;%d;%d;%dm" % (r, g, b, r, g, b)
            else:
                prefix = "\x1b[1m\x1b[38;2;%d;%d;%dm" % (r, g, b)
            suffix = "\x1b[0m"
        elif color is False:
            a = img.getpixel((x,y))
            prefix = ""
            suffix = ""

        ix = int((a // 2.55) // step)
        data[y].append("%s%s" % (prefix, characters[ix]))

    result = '\n'.join(' '.join(c for c in line) + suffix for line in data)

    if output is not None:
        with open(output, "w") as f:
            f.write(result)
    else:
        print(result)

    return 0


def convert(args):
    source = args.source
    size = args.size
    full = args.full
    output = args.output
    return _convert(source, size=size, full=full, output=output)


def main(argv=None):
    argv = (argv or sys.argv)[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument("--size", nargs=2, type=int, default=(100,100),
                        help="desired size of ascii rendition")
    parser.add_argument("--full", action="store_true",
                        help="use both fg and bg")
    parser.add_argument("--output", type=str,
                        help="write to <output> file instead of stdout (useful for when using from python code)")
    parser.set_defaults(func=convert)
    args = parser.parse_args(argv)
    return args.func(args=args)

if __name__ == '__main__':
    sys.exit(main())
