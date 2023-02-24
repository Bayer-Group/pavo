from __future__ import annotations

from pado.dataset import PadoDataset
from pado.images import ImageProvider
from pado.metadata import MetadataProvider
from pado.types import UrlpathLike
from pado_tggates import make_image_provider
from pado_tggates import make_metadata_provider

SELECTED = {"66380.svs", "66372.svs"}


def write_dataset(urlpath: UrlpathLike) -> PadoDataset:
    """store the dataset at a location"""
    ip = make_image_provider()
    mp = make_metadata_provider()
    ds = PadoDataset(urlpath, mode="w")

    iids = list(ip.keys())

    selected = [iid for iid in iids if iid.last in SELECTED]

    filtered_ip = ImageProvider({k: ip[k] for k in selected}, identifier=ip.identifier)

    filtered_mp = MetadataProvider({k: mp[k] for k in selected})

    ds.ingest_obj(filtered_ip)
    ds.ingest_obj(filtered_mp)
    return ds


if __name__ == "__main__":
    import os
    import os.path
    import sys

    path = sys.argv[1]
    if not os.path.isdir(path):
        os.mkdir(path)

    write_dataset(path)
