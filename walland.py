#!/usr/bin/env python3

__author__ = "Matteo Golinelli"
__copyright__ = "Copyright (C) 2023 Matteo Golinelli"
__license__ = "MIT"

from curl_cffi import requests
from bs4 import BeautifulSoup

import subprocess
import argparse
import logging
import random
import shlex
import time
import sys
import os
import re

USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64)' + \
    'AppleWebKit/537.36 (KHTML, like Gecko) ' + \
    'Chrome/90.0.4430.212 Safari/537.36'

DEFAULT = 'random'

SOURCES = ['bing', 'unsplash', 'national-geographic', 'nasa', 'apod', 'earthobservatory', 'epod']

BACKENDS = ['hyprpaper', 'swaybg', 'feh', 'swww']

SUPPORTED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'webp']

SOURCES_INFO = {
    'bing': {
        'url': 'https://www.bing.com/HPImageArchive.aspx?idx=0&n=1', # https://github.com/TimothyYe/bing-wallpaper
        'download': 'https://www.bing.com{}',
        'element': {
            'tag': 'urlBase',
            'attrs': {}
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
    # 'national-geographic': { # Providing the same image since October 31, 2022, RIP :(
    #     'url': 'https://www.nationalgeographic.com/photography/photo-of-the-day/',
    #     'download': '',
    #     'element': {
    #         'tag': 'meta',
    #         'attrs': {'property': 'og:image'}
    #     },
    # },
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


def set_wallpaper(image_path, backend='hyprpaper', backend_args=''):
    '''
    Set as wallpaper the image in image_path
    using the preferred backend.

    backend_args is a string that can be used to pass
    additional arguments to the backend of choice.
    '''

    # Check if the backend is installed
    try:
        if subprocess.check_output(shlex.split(f'which {backend}'), stderr=subprocess.PIPE) == b'':
            logger.error(f'Error: {backend} is not installed. Use one of the available backends: {", ".join(BACKENDS)}')
            sys.exit(1)
    except subprocess.CalledProcessError:
        logger.error(f'Error: {backend} is not installed. Use one of the available backends: {", ".join(BACKENDS)}')
        sys.exit(1)

    if backend == 'hyprpaper':
        # Check if hyprpaper is running
        try:
            if subprocess.check_output(shlex.split('pgrep hyprpaper'), stderr=subprocess.PIPE) == b'':
                # Start hyprpaper in the background
                subprocess.Popen('hyprpaper &', shell=True).wait()
                # Wait for hyprpaper to start
                time.sleep(1)
        except subprocess.CalledProcessError:
            # Start hyprpaper in the background
            subprocess.Popen('hyprpaper &', shell=True).wait()
            # Wait for hyprpaper to start
            time.sleep(1)

        # Preload the image
        subprocess.Popen(shlex.split(f'hyprctl hyprpaper preload "{image_path}"'), stdout=subprocess.PIPE).wait()

        # Get the monitor names with hyprctl monitors
        monitors = subprocess.Popen(shlex.split('hyprctl monitors'), stdout=subprocess.PIPE).communicate()[0].decode().split('\n')
        monitors = [monitor.split('Monitor ')[1].split(' ') for monitor in monitors if 'Monitor ' in monitor]

        for monitor in monitors:
            subprocess.Popen(shlex.split(f'hyprctl hyprpaper wallpaper "{monitor[0]},{image_path}" {backend_args}'), stdout=subprocess.PIPE).wait()
    elif backend == 'swaybg':
        # Kill swaybg
        subprocess.Popen(shlex.split('killall swaybg')).wait()

        subprocess.Popen(shlex.split(f'swaybg --mode fill -i {image_path} {backend_args}'), stdout=subprocess.PIPE)
    elif backend == 'swww':
        # Check that swww-daemon is running
        try:
            if subprocess.check_output(shlex.split('pgrep swww-daemon'), stderr=subprocess.PIPE) == b'':
                # Start swww-daemon in the background
                subprocess.Popen('swww-daemon &', shell=True, stdout=subprocess.PIPE).wait()
                # Wait for swww-daemon to start
                time.sleep(1)
        except subprocess.CalledProcessError:
            # Start swww-daemon in the background
            subprocess.Popen('swww-daemon &', shell=True, stdout=subprocess.PIPE).wait()
            # Wait for swww-daemon to start
            time.sleep(1)

        subprocess.Popen(shlex.split(f'swww img {image_path} {backend_args}'), stdout=subprocess.PIPE)
    elif backend == 'feh':
        subprocess.Popen(shlex.split(f'feh --bg-fill {image_path} {backend_args}'), stdout=subprocess.PIPE)
    else:
        logger.error(f'Error: backend {backend} not found. Use one of the available backends: {", ".join(BACKENDS)}')
        sys.exit(1)


def download_image(url, source, save=False):
    '''
    Download the image from the URL and
    save it in the temporary directory or,
    if save is True, in the current directory.
    '''

    logger.debug(f'Image URL: {url}')

    response = requests.get(url, headers={'User-Agent': USER_AGENT}, impersonate='chrome')

    if response.status_code != 200:
        # For Unsplash: sometimes the download link does not include the name of the photo
        if source == 'unsplash':
            try:
                # Visit the URL without the /download?force=true part
                response = requests.get(url.split('/download')[0], headers={'User-Agent': USER_AGENT}, impersonate='chrome')

                # Get the download link
                source_info = SOURCES_INFO[source]
                source_info['element']['attrs'] = {'href': re.compile(r'/photos/')}

                soup = BeautifulSoup(response.text, 'html.parser')
                element = soup.find(source_info['element']['tag'], source_info['element']['attrs'])
                path = element['href']

                return download_image(path, source, save)
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
        current_dir = os.getcwd()
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

    return filename


def convert_image(image_path):
    '''
    Convert the image in image_path to
    PNG format and save it in the same directory.
    '''
    # Check if ImageMagick is installed
    logger.debug('Converting the image to PNG format')
    try:
        if subprocess.check_output(shlex.split('which magick'), stderr=subprocess.PIPE) == b'':
            logger.error('Error: ImageMagick is not installed. Please install it to convert the image.')
            sys.exit(1)
    except subprocess.CalledProcessError:
        logger.error('Error: ImageMagick is not installed. Please install it to convert the image.')
        sys.exit(1)

    filename = os.path.basename(image_path)
    filename = '.'.join(filename.split('.')[:-1])  # Remove the extension

    subprocess.Popen(shlex.split(f'magick {image_path} {filename}.png')).wait()

    logger.debug(f'Image converted to {filename}.png')
    return f'{filename}.png'


def main():
    parser = argparse.ArgumentParser(description='Walland sets as wallpaper the picture of the day of different sources using different backends.')

    parser.add_argument('-s', '--source', type=str, default=DEFAULT, help=f'Source of the picture of the day. Default: random. Available sources: {", ".join(SOURCES)}')

    parser.add_argument('-b', '--backend', type=str, default='hyprpaper', help=f'Backend to use to set the wallpaper. Default: hyprpaper. Available backends: {", ".join(BACKENDS)}')

    parser.add_argument('-a', '--backend-args', type=str, default='', help='Additional arguments to pass to the backend.')

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

    if args.backend not in BACKENDS:
        logger.error(f'Error: backend {args.backend} not found. Use one of the available backends: {", ".join(BACKENDS)}')
        sys.exit(1)

    source_info = SOURCES_INFO[args.source]

    try:
        response = requests.get(
            SOURCES_INFO[args.source]['url'],
            headers={'User-Agent': USER_AGENT},
            impersonate='chrome'
        )
    except Exception as e:
        logger.error(f'Error: {e}')
        sys.exit(1)

    if args.source in ['nasa', 'earthobservatory', 'bing']:
        soup = BeautifulSoup(response.text, features="xml")
    else:
        soup = BeautifulSoup(response.text, 'html.parser')

    element = soup.find(source_info['element']['tag'], source_info['element']['attrs'])
    path = ''
    if args.source == 'bing':
        path = element.text

        if path.startswith('/'):
            path = source_info['download'].format(path) + '_UHD.jpg'

    elif args.source == 'unsplash':
        path = element['href']

    elif args.source == 'national-geographic':
        path = element['content']

    elif args.source == 'nasa':
        path = element['url']

    elif args.source == 'apod':
        path = source_info['download'].format(element['href'])

    elif args.source == 'earthobservatory':
        print(element, flush=True)
        path = element['url']

    elif args.source == 'epod':
        path = element['src']

    image_path = download_image(path, args.source, args.save)

    # swaybg does not support webp images
    extension = image_path.split('.')[-1]
    if (
        (args.backend == 'swaybg' and extension == 'webp') or
        extension not in SUPPORTED_EXTENSIONS
        ):
        image_path = convert_image(image_path)

    set_wallpaper(image_path, backend=args.backend, backend_args=args.backend_args)


if __name__ == '__main__':
    main()
