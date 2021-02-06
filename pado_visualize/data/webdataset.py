import json
import math
import tarfile
import warnings
from pathlib import Path
from typing import Dict, Optional

import diskcache
import numpy as np
from tqdm import tqdm

__all__ = ["init_wds", "get_wds_map"]

wds_map: Dict[str, Path] = {}


# -- webdataset tars related functions --------------------------------

def init_wds(
    wds_path: Path,
    persist: bool = True,
    ignore_cache: bool = True,
    cache_file: Optional[Path] = None,
) -> None:
    """initialize the webdataset map for the flask instance"""
    global wds_map

    if cache_file is None:
        if persist:
            warnings.warn("persist=True requested but cache_file is None")
        persist = False

    if not wds_path.is_dir():
        raise NotADirectoryError(wds_path)

    def load_wds(path):
        # dont set this outside of init_webdataset
        wm = {}
        for wds_tar in tqdm(path.glob("*.tar"), desc="loading wds"):

            if wds_tar.with_suffix(wds_tar.suffix + ".error").is_file():
                warnings.warn(f"{wds_tar} ignored due to error")
                continue

            with tarfile.open(wds_tar, mode="r") as tar:
                for tarinfo in tar:
                    if not tarinfo.name.endswith(".json"):
                        continue
                    tile_dict = json.load(tar.extractfile(tarinfo))
                    image_id = tile_dict["IMAGE"]
                    break
                else:
                    image_id = None

            if image_id is None:
                warnings.warn(f"no image_id found for {wds_tar}")
                continue
            elif image_id in wm:
                warnings.warn(f"{image_id}:{wds_tar} already in wds_map as {wm[image_id]}")
                continue
            else:
                wm[image_id] = wds_tar
        return wm

    if not persist:
        wds_map.update(load_wds(wds_path))

    else:
        with diskcache.Cache(str(cache_file)) as store:
            key = str(wds_path)
            if key not in store or ignore_cache:
                print("loading web dataset from disk...")
                wds = store[key] = load_wds(wds_path)
            else:
                print("loading webdataset from cache...", end=" ", flush=True)
                wds = store[key]
            wds_map.update(wds)
    print("OK")


def get_wds_map() -> Dict[str, Path]:
    global wds_map
    return wds_map


# -- webdataset image related functions -------------------------------

def wds_grid_thumbnail_array(wds_tar_path: Path) -> np.ndarray:
    """return a thumbnail grid array from a tar file"""
    arr = None

    with tarfile.open(wds_tar_path, mode="r") as tar:
        extractfile = tar.extractfile
        json_load = json.load
        for tarinfo in tar:
            if not tarinfo.name.endswith(".json"):
                continue

            tile_dict = json_load(extractfile(tarinfo))
            tile = tile_dict["tile"]
            filt = tile_dict["filter"]
            x, y = tile["slide_x"], tile["slide_y"]
            tw, th = tuple(tile["size"])
            ix, iy = x // tw, y // th

            try:
                arr[iy, ix] = filt["tissue_perc"]
            except TypeError:
                # this only happens on the first loop
                sw, sh = tw + x + filt["dist_right"], th + y + filt["dist_bottom"]
                aw = int(math.ceil(sw / tw))
                ah = int(math.ceil(sh / th))
                arr = np.zeros((ah, aw), dtype=np.float)
                arr[iy, ix] = filt["tissue_perc"]

    # make green channel
    out = np.zeros((arr.shape[0], arr.shape[1], 4), dtype=np.uint8)
    out[:, :, 1] = 255
    out[:, :, 3] = 255.0 * arr

    return out
