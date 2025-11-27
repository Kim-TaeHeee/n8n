def add_numbers(a, b):
    return a + b

def subtract_numbers(a, b):
    return a - b

def multiply_numbers(a, b):
    return a * b

if __name__ == "__main__":
    result = add_numbers(5, 3)
    print(f"5 + 3의 결과: {result}")
    result = subtract_numbers(5, 3)
    print(f"5 - 3의 결과: {result}")
    result = multiply_numbers(5, 3)
    print(f"5 * 3의 결과: {result}")