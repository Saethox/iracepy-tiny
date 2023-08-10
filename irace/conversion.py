from collections import OrderedDict
from typing import Any

import numpy as np
from rpy2 import rinterface, robjects
from rpy2.robjects import numpy2ri, pandas2ri

converter = robjects.default_converter + robjects.numpy2ri.converter + robjects.pandas2ri.converter


def rpy2py_recursive(data: Any) -> Any:
    """
    Step through an R object recursively and convert the types to python types as appropriate.
    Leaves will be converted to e.g. numpy arrays or lists as appropriate and the whole tree to a dictionary.
    """

    if data == rinterface.NULL:
        return None
    elif data == rinterface.na_values.NA_Character:
        return None
    elif type(data) in [robjects.DataFrame, robjects.ListVector]:
        if len(data) == 1:
            return rpy2py_recursive(data[0])
        else:
            return OrderedDict(zip(data.names, [rpy2py_recursive(elt) for elt in data]))
    elif type(data) in [robjects.StrVector]:
        if len(data) == 1:
            return rpy2py_recursive(data[0])
        else:
            return [rpy2py_recursive(elt) for elt in data]
    elif type(data) in [robjects.FloatVector, robjects.IntVector]:
        if len(data) == 1:
            return rpy2py_recursive(data[0])
        else:
            return np.array(data)
    else:
        if hasattr(data, "rclass"):  # An unsupported r class
            raise KeyError('Could not proceed, type {} is not defined'
                           'to add support for this type, just add it to the imports '
                           'and to the appropriate type list above'.format(type(data)))
        else:
            return data  # We reached the end of recursion
