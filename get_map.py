import os
import math
import requests
from PIL import Image
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO

# CHANGE THESE VALUES TO FIT YOUR NEEDS
# -------------------------------------
base_url = "https://srv2.zoomable.ca/viewer_dest.php?i=img5eb718ef7f019ca5_Europe_WM_8000px&file=_files/{zoom}/{x}_{y}.jpg"

max_zoom = 13  # max zoom level of the image
tile_size = 256   # tile dimensions in px
overlap = 1       # from XML

effective_tile_size = tile_size - overlap

max_workers = 50  # concurrency of downloads

image_width = 8000
image_height = 5714
# -------------------------------------

output_dir = "tiles"
output_image = f"stitched_map_zoom{max_zoom}.jpg"

os.makedirs(output_dir, exist_ok=True)

tiles_x = math.ceil(image_width / tile_size)
tiles_y = math.ceil(image_height / tile_size)

def download_tile(zoom, x, y, retries=3):
    url = base_url.format(zoom=zoom, x=x, y=y)
    local_path = os.path.join(output_dir, f"{zoom}_{x}_{y}.jpg")
    if os.path.exists(local_path):
        return f"Tile {zoom}_{x}_{y} already downloaded."
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                img_bytes = BytesIO(response.content)
                try:
                    img = Image.open(img_bytes)
                    img.verify()
                except Exception:
                    print(f"Invalid image data for tile x={x} y={y} (zoom {zoom}), retrying...")
                    continue
                with open(local_path, "wb") as f:
                    f.write(response.content)
                return f"Downloaded tile: x={x} y={y} (zoom {zoom})"
            else:
                print(f"Tile missing or error: x={x} y={y} (zoom {zoom}) status={response.status_code}")
                break
        except Exception as e:
            print(f"Error downloading tile: x={x} y={y} (zoom {zoom}) attempt {attempt+1} error={e}")
    return f"Failed to download valid tile: x={x} y={y} (zoom {zoom})"

def download_all_tiles(zoom):
    print(f"Downloading tiles for zoom level {zoom} ({tiles_x}x{tiles_y} tiles)")
    tasks = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        for x in range(tiles_x):
            for y in range(tiles_y):
                tasks.append(executor.submit(download_tile, zoom, x, y))
        for future in as_completed(tasks):
            print(future.result())


def stitch_tiles(zoom):
    final_width = tiles_x * effective_tile_size + overlap
    final_height = tiles_y * effective_tile_size + overlap
    print(f"Stitching tiles into final image of size {final_width}x{final_height}")
    final_image = Image.new("RGB", (final_width, final_height), (255, 255, 255))

    for x in range(tiles_x):
        for y in range(tiles_y):
            tile_path = os.path.join(output_dir, f"{zoom}_{x}_{y}.jpg")
            if os.path.exists(tile_path):
                tile_img = Image.open(tile_path)

                # For edge tiles, crop to actual size if needed
                if x == tiles_x - 1:
                    width = final_width - x * effective_tile_size
                else:
                    width = tile_size
                if y == tiles_y - 1:
                    height = final_height - y * effective_tile_size
                else:
                    height = tile_size

                tile_img_cropped = tile_img.crop((0, 0, width, height))
                final_image.paste(tile_img_cropped, (x * effective_tile_size, y * effective_tile_size))
            else:
                print(f"Missing tile for stitching: x={x} y={y}")

    final_image.save(output_image)
    print(f"Saved stitched image to {output_image}")

if __name__ == "__main__":
    download_all_tiles(max_zoom)
    stitch_tiles(max_zoom)
