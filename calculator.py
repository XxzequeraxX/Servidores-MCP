# ============================================================
# Simple Calculator
# A beginner-friendly Python calculator for terminal use.
# ============================================================


def add(a, b):
    """Returns the sum of two numbers."""
    return a + b


def subtract(a, b):
    """Returns the difference of two numbers."""
    return a - b


def multiply(a, b):
    """Returns the product of two numbers."""
    return a * b


def divide(a, b):
    """
    Returns the result of dividing a by b.
    Returns None if division by zero is attempted.
    """
    if b == 0:
        return None  # Signal that division by zero occurred
    return a / b


def get_number(prompt):
    """
    Asks the user to enter a number.
    Keeps asking until a valid number is entered.
    """
    while True:
        user_input = input(prompt)
        try:
            number = float(user_input)  # Try to convert the input to a decimal number
            return number
        except ValueError:
            # If conversion fails, the input was not a valid number
            print("  [!] Invalid input. Please enter a valid number.\n")


def get_operation():
    """
    Shows the operation menu and asks the user to choose one.
    Keeps asking until a valid choice is made.
    """
    print("\n  Select an operation:")
    print("    1. Addition       (+)")
    print("    2. Subtraction    (-)")
    print("    3. Multiplication (*)")
    print("    4. Division       (/)")

    while True:
        choice = input("\n  Enter the number of the operation (1/2/3/4): ").strip()
        if choice in ("1", "2", "3", "4"):
            return choice
        else:
            print("  [!] Invalid choice. Please enter 1, 2, 3, or 4.")


def calculate(choice, num1, num2):
    """
    Performs the chosen operation on the two numbers.
    Returns a tuple: (result, operation_symbol).
    result is None if division by zero occurs.
    """
    if choice == "1":
        return add(num1, num2), "+"
    elif choice == "2":
        return subtract(num1, num2), "-"
    elif choice == "3":
        return multiply(num1, num2), "*"
    elif choice == "4":
        return divide(num1, num2), "/"


def format_number(n):
    """
    Displays a number as an integer if it has no decimal part (e.g., 5.0 → 5),
    otherwise shows it as a decimal (e.g., 2.5 → 2.5).
    """
    return int(n) if n == int(n) else n


def main():
    """Main function that runs the calculator loop."""

    # --- Welcome Banner ---
    print("=" * 40)
    print("       Simple Python Calculator")
    print("=" * 40)

    # Keep running until the user decides to quit
    while True:
        print()

        # --- Step 1: Get the two numbers from the user ---
        num1 = get_number("  Enter the first number : ")
        num2 = get_number("  Enter the second number: ")

        # --- Step 2: Get the desired operation ---
        choice = get_operation()

        # --- Step 3: Perform the calculation ---
        result, symbol = calculate(choice, num1, num2)

        # --- Step 4: Display the result ---
        print()
        if result is None:
            # This happens only when dividing by zero
            print("  [ERROR] Division by zero is not allowed.")
        else:
            # Format numbers nicely before printing
            n1 = format_number(num1)
            n2 = format_number(num2)
            res = format_number(result)
            print(f"  Result: {n1} {symbol} {n2} = {res}")

        # --- Step 5: Ask the user if they want to continue ---
        print()
        again = input("  Would you like to perform another calculation? (yes / no): ").strip().lower()

        # Accept "yes", "y", or just pressing Enter as "yes"
        if again not in ("yes", "y", ""):
            print()
            print("  Thank you for using Simple Calculator. Goodbye!")
            print("=" * 40)
            break  # Exit the while loop and end the program


# --- Program Entry Point ---
# This block runs only when the script is executed directly,
# not when it is imported as a module.
if __name__ == "__main__":
    main()
