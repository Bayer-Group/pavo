import numpy as np

from typing import List
from typing import Mapping
from typing import Sequence

from pado_visualize.data import DatasetProxy
from pado_visualize.data import dataset


def get_valid_metadata_attributes(ds: DatasetProxy = dataset) -> List[str]:
    """return all the attributes present in the metadata provider"""
    return list(ds.metadata.df.columns)

def get_valid_metadata_attribute_options(metadata_attribute: str, ds: DatasetProxy = dataset) -> List[str]:
    """return all the options given for a single attribute present in the metadata provider"""

    def _make_jsonisable(option_list):
        """some types cannot be serialised to json"""
        # TODO: please please plase find a non brute force method to force the df to return safe types (no numpy.int64)
        for idx, option in enumerate(option_list):
            if isinstance(option, np.int64):
                option_list[idx] = int(option)
            if isinstance(option, np.bool_):
                option_list[idx] = bool(option)
        return option_list

    try:
        return _make_jsonisable(list(dataset.metadata.df[metadata_attribute].unique()))
    except KeyError as e:
        raise KeyError(f'Invalid metadata attribute {e} caused a key error.')

def get_all_metadata_attribute_options() -> Mapping[str, Sequence]:
    """build a mapping from a metadata attribute to a list of all of its valid options in the ds."""
    metadata_attributes = get_valid_metadata_attributes()
    valid_metadata_attribute_options = {}
    for attr in metadata_attributes:
        valid_metadata_attribute_options[attr] = get_valid_metadata_attribute_options(attr)
    
    return valid_metadata_attribute_options
