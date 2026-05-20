import random


def roll_die(sides: int) -> int:
    """Roll a die and return the rolled result.

  Args:
    sides: The integer number of sides the die has.

  Returns:
    An integer of the result of rolling the die.
  """
    return random.randint(1, sides)


def check_prime(numbers: list[int]) -> str:
    """Check if a given list of numbers are prime.

  Args:
    numbers: The list of numbers to check.

  Returns:
    A str indicating which number is prime.
  """
    primes = set()
    for number in numbers:
        number = int(number)
        if number <= 1:
            continue
        is_prime = True
        for i in range(2, int(number**0.5) + 1):
            if number % i == 0:
                is_prime = False
                break
        if is_prime:
            primes.add(number)
    return ("No prime numbers found." if not primes else
            f"{', '.join(str(num) for num in primes)} are prime numbers.")
