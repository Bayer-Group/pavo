from typing import List
from typing import Set

from pado.images import ImageId
from pado.annotations import Annotation

from pado_visualize.data import DatasetProxy
from pado_visualize.data import dataset


# --- filtering ---------------------------------------------------------------
class InvalidFilterParameters(Exception):
    pass

def get_filtered_images(filter: dict, ds: DatasetProxy = dataset) -> List[ImageId]:
    """returns tupe of ImageIds which match the given filter"""
    
    filtered_ids = set(ds.index)
    
    filename: str = filter.get('filename', None)
    metadata_key: str = filter.get('metadata_key', None)
    metadata_values: List[str] = filter.get('metadata_values', None)

    # TODO: for efficiency, apply filters in succession without the set conversions
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
        for metadata_value in metadata_values:
            print(valid_options)
            assert metadata_value in valid_options, f'{metadata_value} is an invalid metadata attribute value.'
    except AssertionError as e:
        raise AssertionError(e)

    image_id_strings = ds.metadata.df[ds.metadata.df[metadata_key].isin(metadata_values)].index.unique()
    return set([ImageId.from_str(id) for id in image_id_strings])

def get_valid_metadata_attributes(ds: DatasetProxy = dataset) -> List[str]:
    """return all the attributes present in the metadata provider"""
    return list(ds.metadata.df.columns)

def get_valid_metadata_attribute_options(metadata_attribute: str, ds: DatasetProxy = dataset) -> List[str]:
    """return all the options given for a single attribute present in the metadata provider"""
    try:
        return list(dataset.metadata.df[metadata_attribute].unique())
    except KeyError as e:
        raise KeyError(f'Invalid metadata attribute {e} caused a key error.')


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

