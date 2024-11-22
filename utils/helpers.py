def validate_positive_integer(value):
    """Waliduje, czy wartość jest dodatnią liczbą całkowitą."""
    try:
        num = int(value)
        if num <= 0:
            raise ValueError
        return num
    except ValueError:
        print("Podaj poprawną dodatnią liczbę całkowitą.")
        return None
