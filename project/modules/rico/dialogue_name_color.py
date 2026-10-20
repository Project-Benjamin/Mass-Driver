"""Compatibility import for the shared USA dialogue name-color renderer."""
from shared.tools import xgdialog_name_color as _shared

# Keep private inspection helpers available to older analysis callers, while
# functions and constants retain one canonical implementation.
globals().update({name: value for name, value in vars(_shared).items()
                  if not name.startswith("__")})
