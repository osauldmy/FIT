from typing import Optional, Sized


def validate_nonzero_length(value: Optional[Sized]) -> Optional[Sized]:
    if value is not None and len(value) == 0:
        raise ValueError("Must be either null or not empty.")
    return value
