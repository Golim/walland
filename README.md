# Walland

Sets as wallpaper the picture of the day of different sources using different backends.

Supported backends are: hyprpaper, swaybg, swww, feh (X11).

The sources are:

- [Bing](https://www.bing.com)
- [Earth Science Picture of the Day](https://epod.usra.edu/)
- [NASA Earth Observatory](https://earthobservatory.nasa.gov/topic/image-of-the-day)
- [NASA](https://www.nasa.gov/multimedia/imagegallery/iotd.html)
- [Unsplash](https://unsplash.com)
- [NASA Astronomy Picture of the Day](https://apod.nasa.gov/apod/astropix.html)

## Install

```bash
sudo cp ./walland.py /usr/bin/walland
```

## Dependencies

Install the Python dependencies with:

```bash
pip install -r requirements.txt
```

[curl_cffi](https://github.com/lexiforest/curl_cffi) because Unsplash is now fingerprinting python requests and returning 403. This library impersonates browser fingerprints to avoid this.

### Backends

One of the following backends:

- [Hyprpaper](https://github.com/hyprwm/hyprpaper)
- [Swaybg](https://github.com/swaywm/swaybg)
- [Swww](https://github.com/LGFae/swww)
- [Feh](https://feh.finalrewind.org/)

### Options

```bash
usage: walland [-h] [-s SOURCE] [-b BACKEND] [-a BACKEND_ARGS] [-S] [-D]

Walland sets as wallpaper the picture of the day of different sources using different backends.

options:
  -h, --help            show this help message and exit
  -s SOURCE, --source SOURCE
                        Source of the picture of the day. Default: random. Available sources: bing, unsplash, national-geographic, nasa, apod, earthobservatory, epod
  -b BACKEND, --backend BACKEND
                        Backend to use to set the wallpaper. Default: hyprpaper. Available backends: hyprpaper, swaybg, feh, swww
  -a BACKEND_ARGS, --backend-args BACKEND_ARGS
                        Additional arguments to pass to the backend.
  -S, --save            Save the picture of the day in the current directory.
  -D, --debug           Print debug information.
```

## Screenshots

![How it works](./screenshots/unsplash.png)

*Image taken from [Unsplash](https://unsplash.com/photos/a-snow-covered-mountain-with-a-sky-background--nXA2hmyWlM)*
