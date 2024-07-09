def next_bigger_number(n):
    # Convert the number to a list of its digits
    digits = list(str(n))
    length = len(digits)

    # Step 1: Find the rightmost pair where the left digit is smaller than the right digit
    for i in range(length - 2, -1, -1):
        if digits[i] < digits[i + 1]:
            break
    else:
        # If no such pair is found, there is no larger number possible with these digits
        return -1

    # Step 2: Find the smallest digit to the right of digits[i] that is larger than digits[i]
    for j in range(length - 1, i, -1):
        if digits[j] > digits[i]:
            # Step 3: Swap these two digits
            digits[i], digits[j] = digits[j], digits[i]
            break

    # Step 4: Sort the digits to the right of digits[i] in ascending order
    digits = digits[:i + 1] + sorted(digits[i + 1:])

    # Convert the list of digits back to an integer
    return int(''.join(digits))

# Test the function
today_count = 364
print(next_bigger_number(today_count))  # Should print 76
