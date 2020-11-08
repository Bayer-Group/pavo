import shelve
from pathlib import Path
from typing import Optional, Dict, Literal, overload

from flask import abort
from pado.dataset import PadoDataset

__all__ = ["init_dataset", "get_dataset", "get_image_map"]

# default config
DEFAULT_SHELVE = Path(".pado_visualize.shelve")

# data storage
dataset: Optional[PadoDataset] = None
image_map: Optional[Dict[str, Optional[Path]]] = None


def init_dataset(
    dataset_path: Path,
    persist: bool = True,
    ignore_cache: bool = True,
    cache_file: Path = DEFAULT_SHELVE,
) -> bool:
    """initialize the pado dataset for the flask instance"""
    # NOTE: this should be done using a better cache system
    #   keep this logic here for now to continue developing the POC,
    #   and be able to refactor easily later
    global dataset, image_map

    # normalize path
    dataset_path = Path(dataset_path).expanduser().absolute().resolve()

    def load_dataset(path):
        # there's no need to set this outside of init_dataset
        try:
            ds = PadoDataset(path, mode="r")
        except FileNotFoundError:
            return None, None
        # build image_id:idx map
        im = {img.id_str: img.local_path for img in ds.images}
        return ds, im

    if not persist:
        dataset, image_map = load_dataset(dataset_path)

    else:
        with shelve.open(cache_file) as store:
            key = str(dataset_path)
            if key not in store or ignore_cache:
                print("loading dataset from disk...", end=" ", flush=True)
                dataset, image_map = store[key] = load_dataset(dataset_path)
            else:
                print("loading dataset from cache...", end=" ", flush=True)
                dataset, image_map = store[key]

    print("OK")
    return dataset is not None


@overload
def get_dataset(abort_if_none: Literal[True]) -> PadoDataset:
    ...


def get_dataset(abort_if_none: bool = True) -> Optional[PadoDataset]:
    global dataset
    if abort_if_none and dataset is None:
        return abort(500, "missing dataset")
    return dataset


@overload
def get_image_map(abort_if_none: Literal[True]) -> Dict[str, Optional[Path]]:
    ...


def get_image_map(abort_if_none: bool = True) -> Optional[Dict[str, Optional[Path]]]:
    global image_map
    if abort_if_none and image_map is None:
        return abort(500, "missing image map")
    return image_map


'''
im = {img.id_str: img.lo for idx, img in enumerate(ds.images)}
img_map = get_image_id_map()
if not ds:
    raise RuntimeError("dataset not loaded")

# retrieve the image resource
try:
    img_resource = ds.images[img_map[image_id]]
except KeyError:
    raise FileNotFoundError(f"image_id '{image_id}' not found")

# check if remote resource
p = img_resource.local_path
if p is None:
    raise FileNotFoundError("image is remote")

# verify the resource is local
if not p.is_file():
    raise FileNotFoundError("image is not accessible locally")

return p
'''
