##
# utils/analyzer_state.py
#

##########
# verbosity is an integer value incremented in the analyzer

_verbosity = 0  #  Use a leading underscore to indicate it's internal to this module.


def set_verbosity(value):
    """Sets the value of the verbosity."""
    global _verbosity  # Declare intent to modify the module-level variable.
    _verbosity = value


def get_verbosity() -> int:
    """Returns the value of the verbosity."""
    return _verbosity
