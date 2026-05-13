#!/usr/bin/env bash
# Wrapper for chromium-kiosk — sway-config klipper langa exec-rader.
exec /usr/bin/chromium \
    --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --disable-translate \
    --no-first-run \
    --start-fullscreen \
    --check-for-update-interval=31536000 \
    --overscroll-history-navigation=0 \
    --disable-pinch \
    --disable-features=TranslateUI \
    --hide-scrollbars \
    --autoplay-policy=no-user-gesture-required \
    --ozone-platform=wayland \
    --enable-features=UseOzonePlatform \
    --touch-events=enabled \
    --window-size=800,480 \
    http://127.0.0.1:5000/
