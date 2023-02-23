from __future__ import annotations

from typing import List
from typing import Mapping
from typing import Sequence

from pavo.data import DatasetProxy
from pavo.data import dataset


def get_valid_metadata_attributes(ds: DatasetProxy = dataset) -> List[str]:
    """return all the attributes present in the metadata provider"""
    return list(ds.metadata.df.columns)


def get_valid_metadata_attribute_options(
    metadata_attribute: str, ds: DatasetProxy = dataset
) -> List[str]:
    """return all the options given for a single attribute present in the metadata provider"""

    try:
        return list(dataset.metadata.df[metadata_attribute].unique())
    except KeyError as e:
        raise KeyError(f"Invalid metadata attribute {e} caused a key error.")


def get_all_metadata_attribute_options() -> Mapping[str, Sequence]:
    """build a mapping from a metadata attribute to a list of all of its valid options in the ds."""
    metadata_attributes = get_valid_metadata_attributes()
    valid_metadata_attribute_options = {}
    for attr in metadata_attributes:
        valid_metadata_attribute_options[attr] = get_valid_metadata_attribute_options(
            attr
        )

    return valid_metadata_attribute_options
