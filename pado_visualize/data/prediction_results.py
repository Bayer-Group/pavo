from __future__ import annotations

import math
from collections import UserDict
from pathlib import Path
from typing import Optional
from typing import TypedDict

import numpy as np
import pandas as pd


class SlideScoreValue(TypedDict):
    necrosis: Optional[float]
    colloid_alteration: Optional[float]
    hypertrophy: Optional[float]


class SlideScore(UserDict):
    """temporary implementation for getting slide scores working"""
    df: pd.DataFrame

    def __init__(self, csv_file: Path = None):
        if csv_file is not None:
            self._odf = self._df = pd.read_csv(csv_file)
            assert set(self._df.columns) == {'slide_name', 'necrosis', 'colloid', 'hyper'}
            self.df = self._df.rename(columns={
                'necrosis': 'necrosis',
                'colloid': 'colloid_alteration',
                'hyper': 'hypertrophy',
            }).set_index('slide_name')
                # .where(pd.notnull(self._df), None)
            super(SlideScore, self).__init__(
                self.df.to_dict(orient="index")
            )
        else:
            self.df = pd.DataFrame(index=[], columns=["necrosis", "colloid_alteration", "hypertrophy"])
            super(SlideScore, self).__init__()

    def __getitem__(self, item) -> SlideScoreValue:
        # noinspection PyProtectedMember
        from pado_visualize.routes._route_utils import _image_path_from_image_id

        try:
            val = super().__getitem__(item)
            return {k: None if math.isnan(v) else v for k, v in val.items()}
        except KeyError:
            pass
        p = _image_path_from_image_id(image_id=item)
        if p:
            file_name = p.name
            try:
                val = super().__getitem__(file_name)
                return {k: None if math.isnan(v) else v for k, v in val.items()}
            except KeyError:
                raise KeyError(f"'{item}' --> '{file_name}'")
        else:
            raise KeyError(item)

    def has_necrosis_prediction(self, item):
        try:
            return self[item].get("necrosis") is not None
        except KeyError:
            return False

    def has_hypertrophy_prediction(self, item):
        try:
            return self[item].get("hypertrophy") is not None
        except KeyError:
            return False

    def has_colloid_alteration_prediction(self, item):
        try:
            return self[item].get("colloid_alteration") is not None
        except KeyError:
            return False


class SlidePredictionAnnotations(UserDict):

    def __init__(self, path=None, fmt=None):
        if path is None:
            super().__init__()
            return

        # path provided
        self._path = Path(path)
        if fmt is None:
            raise ValueError("need to provide fmt function for json filename")

        m = {}
        for p in self._path.glob("*.svs"):
            if not p.is_dir():
                continue
            target = p.joinpath(fmt(p.name))
            if target.is_file():
                m[p.name] = target

        super().__init__(m)

    def __getitem__(self, item):
        # noinspection PyProtectedMember
        from pado_visualize.routes._route_utils import _image_path_from_image_id

        try:
            val = super().__getitem__(item)
            return val
        except KeyError:
            pass
        p = _image_path_from_image_id(image_id=item)
        if p:
            file_name = p.name
            try:
                val = super().__getitem__(file_name)
                return val
            except KeyError:
                raise KeyError(f"'{item}' --> '{file_name}'")
        else:
            raise KeyError(item)


if __name__ == "__main__":
    s = SlideScore("./pred_results.csv")
