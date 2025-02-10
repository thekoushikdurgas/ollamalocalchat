
from typing import Dict, Any, Callable

def add_two_numbers(a: int, b: int) -> int:
    """Add two numbers together and return their sum."""
    return a + b

def subtract_two_numbers(a: int, b: int) -> int:
    """Subtract b from a and return the difference."""
    return a - b

def multiply_two_numbers(a: int, b: int) -> int:
    """Multiply two numbers together and return their product."""
    return a * b

# Tool definitions for model interaction
TOOL_DEFINITIONS = [
    {
        'type': 'function',
        'function': {
            'name': 'add_two_numbers',
            'description': 'Add two numbers together',
            'parameters': {
                'type': 'object',
                'required': ['a', 'b'],
                'properties': {
                    'a': {'type': 'integer', 'description': 'First number'},
                    'b': {'type': 'integer', 'description': 'Second number'}
                }
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'subtract_two_numbers',
            'description': 'Subtract two numbers',
            'parameters': {
                'type': 'object',
                'required': ['a', 'b'],
                'properties': {
                    'a': {'type': 'integer', 'description': 'First number'},
                    'b': {'type': 'integer', 'description': 'Second number'}
                }
            }
        }
    },
    {
        'type': 'function',
        'function': {
            'name': 'multiply_two_numbers',
            'description': 'Multiply two numbers',
            'parameters': {
                'type': 'object',
                'required': ['a', 'b'],
                'properties': {
                    'a': {'type': 'integer', 'description': 'First number'},
                    'b': {'type': 'integer', 'description': 'Second number'}
                }
            }
        }
    }
]

# Map of available functions
AVAILABLE_FUNCTIONS: Dict[str, Callable] = {
    'add_two_numbers': add_two_numbers,
    'subtract_two_numbers': subtract_two_numbers,
    'multiply_two_numbers': multiply_two_numbers
}
