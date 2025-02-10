from typing import Dict, Any, Callable

class MathTools:
    """Collection of mathematical operations"""

    @staticmethod
    def add_two_numbers(a: int, b: int) -> int:
        """Add two numbers together"""
        return a + b

    @staticmethod
    def subtract_two_numbers(a: int, b: int) -> int:
        """Subtract b from a"""
        return a - b

    @staticmethod
    def multiply_two_numbers(a: int, b: int) -> int:
        """Multiply two numbers"""
        return a * b

def create_tool_definition(name: str, description: str) -> dict:
    """Create a standard tool definition structure"""
    return {
        'type': 'function',
        'function': {
            'name': name,
            'description': description,
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

# Tool definitions
TOOL_DEFINITIONS = [
    create_tool_definition('add_two_numbers', 'Add two numbers together'),
    create_tool_definition('subtract_two_numbers', 'Subtract two numbers'),
    create_tool_definition('multiply_two_numbers', 'Multiply two numbers')
]

# Available functions map
AVAILABLE_FUNCTIONS: Dict[str, Callable] = {
    'add_two_numbers': MathTools.add_two_numbers,
    'subtract_two_numbers': MathTools.subtract_two_numbers,
    'multiply_two_numbers': MathTools.multiply_two_numbers
}