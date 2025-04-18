# Import Error Fix

## Issue
When running the `map_generator.py` script directly, the following error occurred:

```
Traceback (most recent call last):
  File "C:\APP\CODE\MapGenerator\python_rewrite\map_generator.py", line 6, in <module>
    from .tensor_field import TensorField, NoiseParams
ImportError: attempted relative import with no known parent package
```

## Cause
The error occurred because the script was using relative imports (with a dot prefix, e.g., `from .tensor_field import ...`), which are only valid when the module is part of a package. When running a script directly, Python doesn't recognize it as part of a package, so relative imports fail.

## Solution
The solution was to convert the relative imports to absolute imports by removing the dot prefix:

```python
# Before
from .tensor_field import TensorField, NoiseParams
from .streamlines import StreamlineParams, StreamlineGenerator
from .vector import Vector
from .svg_generator import SVGGenerator
from .model_generator import ModelGenerator
from .basis_field import Grid, Radial

# After
from tensor_field import TensorField, NoiseParams
from streamlines import StreamlineParams, StreamlineGenerator
from vector import Vector
from svg_generator import SVGGenerator
from model_generator import ModelGenerator
from basis_field import Grid, Radial
```

This change allows the script to be run directly without needing to be part of a package.

## Testing
After making this change, the original import error was resolved. However, a new error appeared:

```
ModuleNotFoundError: No module named 'numpy'
```

This is a dependency issue, indicating that the numpy package is not installed in the Python environment. To resolve this, you would need to install numpy:

```
pip install numpy
```

## Alternative Solutions
There are other ways to solve the original import error:

1. **Make the directory a proper package**: Create an `__init__.py` file in the `python_rewrite` directory and run the script as a module: `python -m python_rewrite.map_generator`

2. **Add the parent directory to the Python path**: Add the following at the top of the script:
   ```python
   import sys
   import os
   sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```

3. **Use a relative import with importlib**: Use the `importlib` module to import the modules dynamically.

The solution implemented (converting to absolute imports) was chosen for its simplicity and directness.