"""
CodeGates - Code Analysis and Security Gate Evaluation System
"""

__version__ = "1.0.0"
__author__ = "CodeGates Team"
__description__ = "Code Analysis and Security Gate Evaluation System"

# Make the src directory a Python package
import sys
from pathlib import Path

# Add src to Python path for imports
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
