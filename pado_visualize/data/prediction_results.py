from pathlib import Path

import pandas as pd


XAI_RESULT_LOCATION = "/gpfs01/home/glsvu/pathological-suite/paxo/results"


class SlideScore:

    def __init__(self, csv_file: Path):
        self._df = pd.read_csv(csv_file)

    def __getitem__(self, ):



class XAIResults:

    def __init__(self, path: Path):
        self._path = Path(path)
        assert self._path.is_dir()

