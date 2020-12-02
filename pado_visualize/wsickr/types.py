"""json response types for the fake flickr API"""

from typing import TypedDict, List


class Photo(TypedDict):
    """photo info dictionary"""
    id: str  # numeric
    owner: str
    secret: str
    server: str
    farm: int
    title: str
    ispublic: int  # bool?
    isfriend: int  # bool?
    isfamily: int  # bool?
    ownername: str
    tags: str  # " ".join(tags)


class Photos(TypedDict):
    page: int
    pages: int
    perpage: int
    total: int
    photo: List[Photo]


class Extra(TypedDict):
    explore_date: str
    next_prelude_interval: int


class Size(TypedDict):
    label: str
    width: int
    height: int
    source: str
    url: str
    media: str


class Sizes(TypedDict):
    canblog: int  # bool?
    canprint: int  # bool?
    candownload: int  # bool?
    size: List[Size]


class ResponseGetList(TypedDict):
    """response for getList request"""
    photos: Photos
    extra: Extra
    stat: str


class ResponseGetSizes(TypedDict):
    """response for getSizes request"""
    sizes: Sizes
    stat: str
