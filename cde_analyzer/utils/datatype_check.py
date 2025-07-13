from typing import Tuple, Union


def check_number_type(s) -> Tuple[bool, Union[None, bool]]:
    """
    Determines if a string is number-like (integer, float as decimal, or scientific notation).
    If number-like, it also indicates whether it represents an integer.

    Args:
        s (str): The input string to check.

    Returns:
        tuple: A tuple containing:
            - bool: True if the string is number-like, False otherwise.
            - bool or None: True if it's an integer, False if it's a float, None if not number-like.
    """
    try:
        f_val = float(s)
        is_number_like = True

        # Check if it's an integer
        try:
            i_val = int(s)
            is_integer = f_val == i_val
        except ValueError:
            is_integer = False  # Not directly convertible to int, so it's a float

    except ValueError:
        is_number_like = False
        is_integer = None

    return is_number_like, is_integer


def is_string_shorter(input_string, character_limit) -> bool:
    """
    Checks if a given string is shorter than a specified character limit.

    Args:
        input_string (str): The string to check.
        character_limit (int): The maximum number of characters allowed.

    Returns:
        bool: True if the string is shorter than the limit, False otherwise.
    """
    return len(input_string) < character_limit
