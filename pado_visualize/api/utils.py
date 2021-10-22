from typing import List
from typing import Set

from pado.images import ImageId
from pado.annotations import Annotation

from pado_visualize.data import DatasetProxy
from pado_visualize.data import dataset
from pado_visualize.metadata.utils import get_valid_metadata_attributes
from pado_visualize.metadata.utils import get_valid_metadata_attribute_options


# --- filtering ---------------------------------------------------------------
class InvalidFilterParameters(Exception):
    pass

def get_filtered_images(filter: dict, ds: DatasetProxy = dataset) -> List[ImageId]:
    """returns tupe of ImageIds which match the given filter"""
    
    filtered_ids = set(ds.index)
    
    filename: str = filter.get('filename', None)
    metadata_key: str = filter.get('metadata_key', None)
    metadata_values: List[str] = filter.get('metadata_values', None)
    if metadata_values and not isinstance(metadata_values, list):
        metadata_values = [metadata_values]

    # TODO: for efficiency, combine filters without needing set<->list conversions
    try:
        if filename:
            filtered_ids = filtered_ids & filter_by_filename(filename, ds)
        if metadata_key or metadata_values:
            if metadata_key and metadata_values:
                filtered_ids = filtered_ids & filter_by_metadata(metadata_key, metadata_values)
            else:
                raise InvalidFilterParameters('Must specify a metadata_key and metadata_value.')
    except Exception as e:
        raise InvalidFilterParameters(f'{e}')
    
    return list(filtered_ids)


# --- filter by helpers -------------------------------------------------------
def filter_by_filename(filename: str, ds: DatasetProxy = dataset) -> Set[ImageId]:
    return set([id for id in ds.index if id.last == filename])

def filter_by_metadata(metadata_key: str, metadata_values: List[str], ds: DatasetProxy = dataset) -> Set[ImageId]:
    try: 
        assert metadata_key in get_valid_metadata_attributes(), 'Invalid metadata attribute.'
        valid_options = get_valid_metadata_attribute_options(metadata_key)
        for idx, metadata_value in enumerate(metadata_values):
            print(type(metadata_value))
            # TODO is there a better way to handle type conversions when the url parameters are always passed as strings from the frontend?
            if metadata_value.isnumeric() and metadata_value[0] != '0':
                print("was numeric", type(metadata_value))
                metadata_values[idx] = int(metadata_value)
            assert metadata_values[idx] in valid_options, (
                f'{metadata_values[idx]} of type {type(metadata_value[idx])} '
                'is an invalid metadata attribute value.')
    except AssertionError as e:
        raise AssertionError(e)

    image_id_strings = ds.metadata.df[ds.metadata.df[metadata_key].isin(metadata_values)].index.unique()
    return set([ImageId.from_str(id) for id in image_id_strings])


# ---- prediction api helper functions ----------------------------------------
def insert_annotation_prediction(prediction_record: dict, image_id: ImageId):
    """inserts an annotation style prediction into an image's list of annotations"""

    if prediction_record['annotator']['type'] != 'model':
        return f'Annotator type for predictions must be "model"', 400 

    try:
        dataset.annotations[image_id].insert(
            index=0, 
            value=Annotation.from_obj(prediction_record)
        )
    except Exception as e:
        return f'Could not insert prediction for {image_id} due to {e}', 500

    return '', 200

def insert_image_prediction():
    # TODO: upload a large image style prediction here
    return 'not implemented', 200

