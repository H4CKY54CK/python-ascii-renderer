import os
import io
import sys
import requests
import argparse
import itertools
from PIL import Image


def _convert(source, *, full=False, color=True, alpha=True, size=tuple(), characters=' .,:;+*%#@'):
    if os.path.exists(source):
        img = Image.open(source)
    else:
        try:
            with requests.get(source) as response:
                img = Image.open(io.BytesIO(response.content))
        except:
            raise ValueError("invalid url")


    if color is True and alpha is True:
        img = img.convert('RGBA')
    elif color is True and alpha is False:
        img = img.convert('RGB')
    elif color is False:
        img = img.convert('L')

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

    return result


def convert(args):
    source = args.source
    size = args.size
    full = args.full
    print(_convert(source, size=size, full=full))


def main(argv=None):
    argv = (argv or sys.argv)[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument("--size", nargs=2, type=int, default=(100,100), help="desired size of ascii rendition")
    parser.add_argument("--full", action="store_true", help="use both fg and bg")
    parser.set_defaults(func=convert)
    args = parser.parse_args(argv)
    return args.func(args=args)

if __name__ == '__main__':
    sys.exit(main())
