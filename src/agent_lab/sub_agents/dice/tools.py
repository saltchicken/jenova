import random


def roll_die(sides: int) -> int:
    """Roll a die and return the rolled result.

  Args:
    sides: The integer number of sides the die has.

  Returns:
    An integer of the result of rolling the die.
  """
    return random.randint(1, sides)


def check_prime(numbers: list[int]) -> dict[str, list[int]]:
    """Check if a given list of numbers are prime."""
    primes = []
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
            primes.append(number)

    return {"primes_found": primes}
