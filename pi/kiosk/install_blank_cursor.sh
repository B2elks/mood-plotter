#!/usr/bin/env bash
# Skapa ett "blank" XCursor-tema sa cage/wlroots inte ritar en muspekare.
# Tomt 1x1-transparant XCursor-blob — alla cursor-namn pekar pa samma fil.
set -euo pipefail

THEME_DIR=/usr/share/icons/blank/cursors
sudo mkdir -p "$THEME_DIR"

# Generera en 1x1 helt transparent XCursor-fil via Python.
# Filformat: https://man.archlinux.org/man/Xcursor.3
sudo /usr/bin/env python3 - "$THEME_DIR" << 'PY'
import os, struct, sys

out_dir = sys.argv[1]

# 1x1 transparent BGRA: 4 nollor.
pixels = b"\x00\x00\x00\x00"

# Xcursor header
magic = b"Xcur"
header_size = 16
version = 0x10000
ntoc = 1

# TOC entry: type=image, subtype=1 (size in pixels), pos
TYPE_IMAGE = 0xfffd0002
img_offset = header_size + 12  # header + 1 TOC entry (12 bytes each)

header = struct.pack("<4sIII", magic, header_size, version, ntoc)
toc = struct.pack("<III", TYPE_IMAGE, 1, img_offset)

# Image chunk: header_len(36), TYPE_IMAGE, subtype(1), version(1),
#   width(1), height(1), xhot(0), yhot(0), delay(0), then pixels
img_header = struct.pack(
    "<IIIIIIIIII",
    36, TYPE_IMAGE, 1, 1,
    1, 1, 0, 0, 0,
    0,  # placeholder; actually image header has different layout, see below
)
# Re-do properly:
# header: { len=36, type=0xfffd0002, subtype=1, version=1, width, height, xhot, yhot, delay }
img_hdr = struct.pack(
    "<IIIIIIIIII",
    36,            # length of image-header
    TYPE_IMAGE,    # type
    1,             # subtype (nominal size)
    1,             # image version
    1,             # width
    1,             # height
    0,             # xhot
    0,             # yhot
    0,             # delay (ms)
    0,             # PAD — Xcursor header is 9 uint32 + pixels; padding for alignment
)
# Actual format has 9 uint32 in image header (no extra padding), so trim:
img_hdr = struct.pack(
    "<IIIIIIIII",
    36, TYPE_IMAGE, 1, 1, 1, 1, 0, 0, 0,
)

data = header + toc + img_hdr + pixels

cursor_path = os.path.join(out_dir, "left_ptr")
with open(cursor_path, "wb") as f:
    f.write(data)

# Symlink alla vanliga namn till samma blob
aliases = [
    "default", "pointer", "arrow", "text", "hand", "hand1", "hand2",
    "crosshair", "wait", "watch", "progress",
    "ibeam", "grab", "grabbing", "move",
    "n-resize", "s-resize", "e-resize", "w-resize",
    "ne-resize", "nw-resize", "se-resize", "sw-resize",
]
for a in aliases:
    p = os.path.join(out_dir, a)
    if os.path.lexists(p):
        os.unlink(p)
    os.symlink("left_ptr", p)
print(f"OK: {cursor_path} + {len(aliases)} aliases")
PY

# Theme metadata
sudo tee /usr/share/icons/blank/index.theme > /dev/null << 'INI'
[Icon Theme]
Name=blank
Inherits=core
INI

echo "Blank-cursor-tema installerat. Anvand med XCURSOR_THEME=blank"
