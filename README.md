# python-ascii-renderer
This Python script just takes an image, resizes it, and converts it to colored ASCII. Beware, it relies on truecolor support.

## Usage
First off, it requires `pillow`. And that's the only 3rd party package needed.

Use this script as follows:

`python img2ascii.py <source>` where `source` can be either a path to a local file or a URL pointing to an image.

Optional arguments include:

- `--full` to color the background as well as the foreground (does not look great)
- `--size X Y` to resize the image in case your terminal is not the smallest font and fullscreened (which is how I usually demo it). **Note that this ends up being the width and height of characters in your terminal.**
- `--help`/`-h` because `argparse` is helpful.

## A few notes
There might be some unused variables even though I gave it a once-over before pushing this to the repo. When (not if) you find something incorrect, feel free to mention it. I just may not prioritize a fix, since nobody is really relying on this for anything.