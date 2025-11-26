# simple_utility.py

def add_numbers(a, b):
    """
    주어진 두 숫자를 더하여 반환하는 함수입니다.
    이것은 n8n 자동화 테스트를 위한 초기 버전입니다.
    """
    return a + b

if __name__ == "__main__":
    result = add_numbers(5, 3)
    print(f"5 + 3의 결과: {result}")
