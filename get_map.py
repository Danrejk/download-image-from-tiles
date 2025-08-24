import os
import requests
from PIL import Image

# CHANGE THESE VALUES TO FIT YOUR NEEDS
# -------------------------------------
base_url = "https://srv2.zoomable.ca/viewer_dest.php?i=img5eb718ef7f019ca5_Europe_WM_8000px&file={zoom}/{x}/{y}.jpg"

max_zoom = 6  # Set this to the max zoom level
tile_size = 256  # Usually tiles on zoomable for example are 256x256px
# -------------------------------------

output_dir = "tiles"
output_image = "stiched_map{0}.jpg".format(max_zoom)

os.makedirs(output_dir, exist_ok=True)

def download_tile(zoom, x, y):
    url = base_url.format(zoom=zoom, x=x, y=y)
    local_path = os.path.join(output_dir, f"{zoom}_{x}_{y}.jpg")
    if os.path.exists(local_path):
        print(f"Tile {zoom}_{x}_{y} already downloaded.")
        return True
    response = requests.get(url)
    if response.status_code == 200:
        with open(local_path, "wb") as f:
            f.write(response.content)
        print(f"Downloaded tile: x={x} y={y} (zoom {zoom})")
        return True
    else:
        print(f"Tile missing or error: x={x} y={y} (zoom {zoom}) status={response.status_code}")
        return False

def download_all_tiles(zoom):
    tile_count = 2 ** zoom  # Number of tiles in each dimension at this zoom level
    print(f"Downloading all tiles for zoom level {zoom} ({tile_count}x{tile_count} tiles)")
    for x in range(tile_count):
        for y in range(tile_count):
            download_tile(zoom, x, y)

def stitch_tiles(zoom):
    tile_count = 2 ** zoom
    final_width = tile_count * tile_size
    final_height = tile_count * tile_size
    print(f"Stitching tiles into final image of size {final_width}x{final_height}")
    final_image = Image.new("RGB", (final_width, final_height))

    for x in range(tile_count):
        for y in range(tile_count):
            tile_path = os.path.join(output_dir, f"{zoom}_{x}_{y}.jpg")
            if os.path.exists(tile_path):
                tile_img = Image.open(tile_path)
                final_image.paste(tile_img, (x * tile_size, y * tile_size))
            else:
                print(f"Missing tile for stitching: x={x} y={y}")

    final_image.save(output_image)
    print(f"Saved stitched image to {output_image}")

if __name__ == "__main__":
    download_all_tiles(max_zoom)
    stitch_tiles(max_zoom)
