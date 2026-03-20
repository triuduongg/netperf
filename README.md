# python, mediamtx, ffmpeg, requirements
## python: https://www.python.org/
## mediamtx: https://github.com/bluenviron/mediamtx/releases ./netperf/
## ffmpeg: https://github.com/BtbN/FFmpeg-Builds/releases {bin}
## `python -m pip install -r requirements.txt`
# Chrome
## Google Play: https://play.google.com/store/apps/details?id=com.android.chrome, App Store: https://apps.apple.com/app/google-chrome/id535886823
## chrome://flags/#unsafely-treat-insecure-origin-as-secure = `http://<laptopIP>:8889, http://<laptopIP>:8000`
# Image Mode
## `./mediamtx`
## `http://<laptopIP>:8889/<hostname>/publish` on Chrome
## `python station.py`
## `1`
## Source = `image = jpg, png, ...`, `video = mp4, avi, ...`, `link = http, rtsp, ...`, `rtsp://127.0.0.1:8554/<hostname>`
# Semantic Mode
## script.js: `SERVER_IP = "<laptopIP>"`
## `python -m http.server 8000`
## `http://<laptopIP>:8000` on Chrome
## `python station.py`
## `2`
## Source = `phoneIP`
