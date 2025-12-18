
# 1. Linear (simple)
def linear_example(x):
    y = x + 1
    return y

# 2. Binary branching
def binary_branch(x):
    if x > 0:
        return 'positive'
    else:
        return 'negative'

# 3. Multi-way branching  
def multi_branch(x):
    if x > 100:
        return 'high'
    elif x > 50:
        return 'medium'
    elif x > 0:
        return 'low'
    else:
        return 'negative'

# 4. Loop structure
def loop_example(n):
    total = 0
    for i in range(n):
        total += i
    return total

# 5. Nested structures
def nested_example(x, y):
    if x > 0:
        for i in range(x):
            if i > y:
                return i
    return 0

# 6. Exception handling
def exception_example(x):
    try:
        result = 10 / x
    except ZeroDivisionError:
        result = None
    finally:
        print('done')
    return result

# 7. Multiple returns
def multi_return(x):
    if x < 0:
        return None
    if x > 100:
        return 'too big'
    return x * 2
