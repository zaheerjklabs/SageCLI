"""Simple Calculator Application.

Provides standard arithmetic operations via both function calls
and an interactive command-line interface.
"""

from typing import Union

Number = Union[int, float]


class Calculator:
    """A standard arithmetic calculator."""

    def add(self, a: Number, b: Number) -> Number:
        """Return the sum of a and b."""
        return a + b

    def subtract(self, a: Number, b: Number) -> Number:
        """Return the difference of a and b."""
        return a - b

    def multiply(self, a: Number, b: Number) -> Number:
        """Return the product of a and b."""
        return a * b

    def divide(self, a: Number, b: Number) -> float:
        """Return the division of a by b. Raises ValueError on division by zero."""
        if b == 0:
            raise ValueError("Cannot divide by zero.")
        return a / b

    def power(self, a: Number, b: Number) -> Number:
        """Return a raised to the power of b."""
        return a ** b

    def modulo(self, a: Number, b: Number) -> Number:
        """Return the remainder of dividing a by b."""
        if b == 0:
            raise ValueError("Cannot perform modulo by zero.")
        return a % b


def main() -> None:
    """Interactive CLI runner for the calculator."""
    calc = Calculator()
    operations = {
        "1": ("Add (+)", calc.add),
        "2": ("Subtract (-)", calc.subtract),
        "3": ("Multiply (*)", calc.multiply),
        "4": ("Divide (/)", calc.divide),
        "5": ("Power (^)", calc.power),
        "6": ("Modulo (%)", calc.modulo),
    }

    print("=" * 40)
    print("        Simple Calculator")
    print("=" * 40)

    for key, (name, _) in operations.items():
        print(f"  {key}. {name}")
    print("  0. Exit")
    print("=" * 40)

    while True:
        choice = input("\nSelect operation (0-6): ").strip()

        if choice == "0":
            print("Exiting calculator. Goodbye!")
            break

        if choice not in operations:
            print("Invalid choice. Please select an option between 0 and 6.")
            continue

        op_name, op_func = operations[choice]

        try:
            val1 = float(input("Enter first number: "))
            val2 = float(input("Enter second number: "))
            result = op_func(val1, val2)
            # Format integer outputs cleanly if whole number
            formatted_res = int(result) if isinstance(result, float) and result.is_integer() else result
            print(f"Result [{op_name}]: {formatted_res}")
        except ValueError as err:
            print(f"Error: {err}")
        except Exception as e:
            print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
