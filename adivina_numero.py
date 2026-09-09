import random

# Generate a random secret number between 1 and 100 (inclusive)
secret_number = random.randint(1, 100)

# Initialize the attempt counter
attempts = 0

print("Welcome to Guess the Number!")
print("I'm thinking of a number between 1 and 100.")
print("Can you guess what it is?\n")

# Keep looping until the player guesses correctly
while True:
    # Ask the player to enter a guess
    guess_input = input("Enter your guess: ")

    # Convert the input from text to an integer
    guess = int(guess_input)

    # Increase the attempt counter by 1
    attempts += 1

    # Compare the guess with the secret number and give a hint
    if guess < secret_number:
        print("Too low! The number is HIGHER than", guess)
    elif guess > secret_number:
        print("Too high! The number is LOWER than", guess)
    else:
        # The player guessed correctly
        print(f"\n🎉 Congratulations! You guessed the secret number: {secret_number}")
        print(f"It took you {attempts} attempt(s).")
        break  # Exit the loop since the game is over
