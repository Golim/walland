#!/usr/bin/env python3

__author__ = "Matteo Golinelli"
__copyright__ = "Copyright (C) 2023 Matteo Golinelli"
__license__ = "MIT"

from bs4 import BeautifulSoup

import argparse
import requests
import logging
import random
import time
import sys
import os
import re

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64)' + \
    'AppleWebKit/537.36 (KHTML, like Gecko) ' + \
    'Chrome/90.0.4430.212 Safari/537.36'

DEFAULT = 'random'

SOURCES = ['bing', 'unsplash', 'national-geographic', 'nasa', 'apod', 'earthobservatory', 'epod']

SOURCES_INFO = {
    'bing': {
        'url': 'https://www.bing.com',
        'download': 'https://www.bing.com{}',
        'element': {
            'tag': 'div',
            'attrs': {'class': 'hp_top_cover'}
        },
    },
    'unsplash': {
        'url': 'https://unsplash.com/collections/1459961/photo-of-the-day-(archive)',
        'download': '',
        'element': {
            'tag': 'a',
            'attrs': {'href': re.compile(r'^https://unsplash.com/photos/'), 'title': 'Download this image'}
        },
    },
    'national-geographic': {
        'url': 'https://www.nationalgeographic.com/photography/photo-of-the-day/',
        'download': '',
        'element': {
            'tag': 'meta',
            'attrs': {'property': 'og:image'}
        },
    },
    'nasa': {
        'url': 'https://www.nasa.gov/rss/dyn/lg_image_of_the_day.rss',
        'download': '',
        'element': {
            'tag': 'enclosure',
            'attrs': {'type': 'image/jpeg'}
        },
    },
    'apod': {
        'url': 'https://apod.nasa.gov/apod/astropix.html',
        'download': 'https://apod.nasa.gov/apod/{}',
        'element': {
            'tag': 'a',
            'attrs': {'href': re.compile(r'^image/')}
        },
    },
    'earthobservatory': {
        'url': 'https://earthobservatory.nasa.gov/feeds/earth-observatory.rss',
        'download': '',
        'element': {
            'tag': 'media:thumbnail',
            'attrs': {}
        },
    },
    'epod': {
        'url': 'https://epod.usra.edu/',
        'download': '',
        'element': {
            'tag': 'img',
            'attrs': {'class': 'asset-image'}
        },
    },
}

logger = logging.getLogger('walland')

def download_image(url, source, save=False):
    logger.debug(f'Image URL: {url}')

    response = requests.get(url, headers={'User-Agent': USER_AGENT})

    if response.status_code != 200:
        # For Unsplash: sometimes the download link does not include the name of the photo
        if source == 'unsplash':
            try:
                # Visit the URL without the /download?force=true part
                response = requests.get(url.split('/download')[0], headers={'User-Agent': USER_AGENT})

                # Get the download link
                source_info = SOURCES_INFO[source]
                source_info['element']['attrs'] = {'href': re.compile(r'/photos/')}

                soup = BeautifulSoup(response.text, 'html.parser')
                element = soup.find(source_info['element']['tag'], source_info['element']['attrs'])
                path = element['href']

                download_image(path, source, save)
                return
            except Exception as e:
                logger.error(f'Error: {e}')
                sys.exit(1)

    # Filename is the source + the current date
    filename = f'{source}_{time.strftime("%Y-%m-%d")}'

    # Add the extension
    url = url.split('?')[0]
    url = url.split('#')[0]
    if '.' in url.split('/')[-1]:
        # If it's in the URL, use that
        filename += f'.{url.split(".")[-1]}'
    else:
        # Use the content-type
        filename += f'.{response.headers["content-type"].split("/")[-1]}'

    if save:
        current_dir = os.path.dirname(os.path.realpath(__file__))
        filename = f'{current_dir}/{filename}'
    else:
        # Save the image in a temporary directory
        tmp_dir = f'/tmp/walland'
        if not os.path.exists(tmp_dir):
            os.makedirs(tmp_dir)
        filename = f'{tmp_dir}/{filename}'

    logger.debug(f'Saving image as {filename}')

    with open(filename, 'wb') as f:
        f.write(response.content)

    # If the image is not of the supported formats (png, jpg, jpeg), convert it to png
    if filename.split('.')[-1] not in ['png', 'jpg', 'jpeg']:
        os.system(f'convert {filename} {filename.split(".")[0]}.png')
        # Remove the old file
        os.remove(filename)
        filename = f'{filename.split(".")[0]}.png'

        logger.debug(f'Converted to {filename}')

    # Set as wallpaper using hyprpaper

    # Preload the image
    os.system(f'hyprctl hyprpaper preload "{filename}"')
    logger.debug(f'hyprctl hyprpaper preload "{filename}"')

    # Get the monitor names with hyprctl monitors
    monitors = os.popen('hyprctl monitors').read().split('\n')
    monitors = [monitor.split('Monitor ')[1].split(' ') for monitor in monitors if 'Monitor ' in monitor]
    logger.debug(f'Detected monitors: {monitors}')

    for monitor in monitors:
        os.system(f'hyprctl hyprpaper wallpaper "{monitor[0]},{filename}"')
        logger.debug(f'hyprctl hyprpaper wallpaper "{monitor[0]},{filename}"')

def main():
    parser = argparse.ArgumentParser(description='Walland sets as wallpaper the picture of the day of different sources using hyprpaper.')

    parser.add_argument('-s', '--source', type=str, default=DEFAULT, help=f'Source of the picture of the day. Default: random. Available sources: {", ".join(SOURCES)}')

    parser.add_argument('-S', '--save', action='store_true', help='Save the picture of the day in the current directory.')

    parser.add_argument('-D', '--debug', action='store_true', help='Print debug information.')

    # If argcomplete is installed, autocomplete is enabled
    try:
        import argcomplete
        argcomplete.autocomplete(parser)
    except ImportError:
        pass

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # Set urllib3 logger to ERROR
    logging.getLogger('urllib3').setLevel(logging.ERROR)

    if args.source == DEFAULT:
        args.source = random.choice(SOURCES)

    elif args.source not in SOURCES:
        logger.error(f'Error: source {args.source} not found.')
        sys.exit(1)

    source_info = SOURCES_INFO[args.source]

    try:
        response = requests.get(
            SOURCES_INFO[args.source]['url'],
            headers={'User-Agent': USER_AGENT}
        )
    except Exception as e:
        logger.error(f'Error: {e}')
        sys.exit(1)

    if args.source in ['nasa', 'earthobservatory']:
        soup = BeautifulSoup(response.text, features="xml")
    else:
        soup = BeautifulSoup(response.text, 'html.parser')

    element = soup.find(source_info['element']['tag'], source_info['element']['attrs'])
    path = ''
    if args.source == 'bing':
        path = element['style'].split('url(')[1].split(')')[0].replace('"', '')

        if path.startswith('/'):
            path = source_info['download'].format(path)

    elif args.source == 'unsplash':
        path = element['href']

    elif args.source == 'national-geographic':
        path = element['content']

    elif args.source == 'nasa':
        path = element['url']

    elif args.source == 'apod':
        path = source_info['download'].format(element['href'])

    elif args.source == 'earthobservatory':
        path = element['url']

    elif args.source == 'epod':
        path = element['src']

    download_image(path, args.source, args.save)

if __name__ == '__main__':
    main()
