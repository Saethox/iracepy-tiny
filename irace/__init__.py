import logging

import rpy2.rinterface_lib.callbacks

from .base import irace
from .experiment import Experiment
from .params import ParameterSpace, Real, Integer, Categorical, Ordinal, Bool
from .scenario import Scenario

rpy2.rinterface_lib.callbacks.logger.setLevel(logging.ERROR)  # will display errors, but not warnings
