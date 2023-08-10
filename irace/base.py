from typing import Any

import pandas as pd

from ._rpackage import _irace
from .conversion import converter
from .params import ParameterSpace
from .scenario import Scenario


def irace(scenario: Scenario, params: ParameterSpace, return_df: bool = False,
          remove_metadata: bool = True) -> pd.DataFrame | list[dict[str, Any]]:
    """irace: Iterated Racing for Automatic Algorithm Configuration."""

    r_scenario, _r_target_runner = scenario.py2rpy()
    r_params = params.py2rpy()

    df = _irace.irace(r_scenario, r_params)
    df = converter.rpy2py(df)

    if remove_metadata:
        df = df.loc[:, ~df.columns.str.startswith('.')]

    if return_df:
        return df
    else:
        return df.to_dict('records')
