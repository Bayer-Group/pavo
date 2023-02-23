from __future__ import annotations

from typing import List
from typing import Set

from pado.annotations import Annotation
from pado.images import ImageId

from pavo.data import DatasetProxy
from pavo.data import dataset
from pavo.metadata.utils import get_valid_metadata_attribute_options
from pavo.metadata.utils import get_valid_metadata_attributes


# --- filtering ---------------------------------------------------------------
class InvalidFilterParameters(Exception):
    pass


def get_filtered_image_ids(filter: dict, ds: DatasetProxy = dataset) -> List[ImageId]:
    """returns tuple of all ImageIds which match the given filter"""

    filtered_ids = set(ds.index)

    filename: str = filter.get("filename", None)
    metadata_key: str = filter.get("metadata_key", None)
    metadata_values: List[str] = filter.get("metadata_values", None)
    if metadata_values and not isinstance(metadata_values, list):
        metadata_values = [metadata_values]

    # TODO: for efficiency, combine filters without needing set<->list conversions
    try:
        if filename:
            filtered_ids = filtered_ids & filter_by_filename(filename, ds)
        if metadata_key or metadata_values:
            if metadata_key and metadata_values:
                filtered_ids = filtered_ids & filter_by_metadata(
                    metadata_key, metadata_values
                )
            else:
                raise InvalidFilterParameters(
                    "Must specify a metadata_key and metadata_value."
                )
    except Exception as e:
        raise InvalidFilterParameters(f"{e}")

    return list(filtered_ids)


# --- filter by helpers -------------------------------------------------------
def filter_by_filename(filename: str, ds: DatasetProxy = dataset) -> Set[ImageId]:
    return {id for id in ds.index if id.last == filename}


def filter_by_metadata(
    metadata_key: str, metadata_values: List[str], ds: DatasetProxy = dataset
) -> Set[ImageId]:
    try:
        assert (
            metadata_key in get_valid_metadata_attributes()
        ), "Invalid metadata attribute."
        valid_options = get_valid_metadata_attribute_options(metadata_key)
        for idx, metadata_value in enumerate(metadata_values):
            assert metadata_values[idx] in valid_options, (
                f"{metadata_values[idx]} of type {type(metadata_value[idx])} "
                "is an invalid metadata attribute value."
            )
    except AssertionError as e:
        raise AssertionError(e)

    image_id_strings = ds.metadata.df[
        ds.metadata.df[metadata_key].isin(metadata_values)
    ].index.unique()
    return {ImageId.from_str(id) for id in image_id_strings}


# ---- prediction api helper functions ----------------------------------------
def insert_annotation_prediction(prediction_record: dict, image_id: ImageId):
    """inserts an annotation style prediction into an image's list of annotations"""

    if prediction_record["annotator"]["type"] != "model":
        return 'Annotator type for predictions must be "model"', 400

    try:
        dataset.annotations[image_id].insert(
            index=0, value=Annotation.from_obj(prediction_record)
        )
    except Exception as e:
        return f"Could not insert prediction for {image_id} due to {e}", 500

    return "", 200


def insert_image_prediction():
    # TODO: upload a large image style prediction here
    return "not implemented", 200
