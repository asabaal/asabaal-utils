import importlib
import types

from pathlib import Path

def find_package_location(package_name_or_module: str | types.ModuleType) -> str:
    """
    Find the location of a package, whether it's already imported or not.

    This function determines the installation directory of a Python package by either
    importing it by name or using an already imported module object. It returns the
    parent directory path where the package is installed.

    Parameters
    ----------
    package_name_or_module : Union[str, types.ModuleType]
        Either a string representing the package name or an imported module object.
        For string inputs, the package must be installed and importable.
        For module objects, they must have a valid __file__ attribute.

    Returns
    -------
    str
        The absolute file path to the parent directory containing the package.
        This is typically the directory containing site-packages or similar.

    Raises
    ------
    ValueError
        If the input string is empty or contains only whitespace.
        >>> find_package_location("")
        ValueError: Empty module name
        >>> find_package_location("   ")
        ValueError: Empty module name

    TypeError
        If the input is neither a string nor a module object.
        >>> find_package_location(123)
        TypeError: Argument must be a string (package name) or a module object
        >>> find_package_location(None)
        TypeError: Argument must be a string (package name) or a module object

    ImportError
        If the package cannot be imported (when using string input).
        >>> find_package_location("nonexistent_package")
        ImportError: No module named 'nonexistent_package'

    AttributeError
        If the package location cannot be determined (e.g., built-in modules).
        >>> import sys
        >>> find_package_location(sys)
        AttributeError: Unable to determine the location of 'sys'. It might be a built-in module.

    Examples
    --------
    Using a string package name:
    >>> import os
    >>> path = find_package_location('numpy')
    >>> path
    '/usr/local/lib/python3.8'

    Using an imported module object:
    >>> import pandas as pd
    >>> path = find_package_location(pd)
    >>> path
    '/usr/local/lib/python3.8'

    Using a subpackage:
    >>> path = find_package_location('pandas.core')
    >>> path
    '/usr/local/lib/python3.8'

    Error cases:
    >>> try:
    ...     find_package_location('nonexistent_package')
    ... except ImportError as e:
    ...     print(f"Caught error: {e}")
    Caught error: No module named 'nonexistent_package'

    >>> try:
    ...     find_package_location(123)  # type: ignore
    ... except TypeError as e:
    ...     print(f"Caught error: {e}")
    Caught error: Argument must be a string (package name) or a module object

    Notes
    -----
    - The function returns the parent directory of the package installation,
      not the package directory itself.
    - For standard installations, this is typically the directory containing
      site-packages.
    - The function works with both regular packages and namespace packages.
    - Built-in modules and other modules without a __file__ attribute will
      raise AttributeError.

    See Also
    --------
    importlib.import_module : Used internally to import packages by name
    types.ModuleType : The type of module objects accepted by this function
    pathlib.Path : Used internally for path manipulation
    """
    package: types.ModuleType

    if isinstance(package_name_or_module, str):
        if not package_name_or_module.strip():
            raise ValueError("Empty module name")
        # If it's a string, treat it as a package name and try to import
        package = importlib.import_module(package_name_or_module)
    elif isinstance(package_name_or_module, types.ModuleType):
        # If it's already a module object, use it directly
        package = package_name_or_module
    else:
        raise TypeError("Argument must be a string (package name) or a module object.")
    
    # Get the file path of the package
    if not hasattr(package, '__file__'):
        raise AttributeError(
            f"Unable to determine the location of '{getattr(package, '__name__', 'unknown')}'. "
            "It might be a built-in module."
        )
    
    # Convert to Path object for more reliable path manipulation
    package_path: Path = Path(package.__file__)
    # Get the parent directory that contains all site-packages
    # This is typically two levels up from the module file for regular packages
    site_packages_parent: Path = package_path.parent.parent.parent
    return str(site_packages_parent)