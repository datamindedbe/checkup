"""
Module with intentional linting issues for testing.
"""

# Unused imports (F401)


# Undefined name (F821)
def use_undefined():
    return undefined_variable


# Unused variable (F841)
def unused_vars():
    x = 5
    y = 10
    z = 15
    return x


# Line too long (E501) - this is a really really really really really really really really really really really really long line
def long_line():
    return "This is a very long string that exceeds the default line length limit and should trigger a line too long error from ruff linter"


# Missing whitespace (E231)
def bad_spacing():
    my_list = [1, 2, 3, 4, 5]
    my_dict = {"a": 1, "b": 2, "c": 3}
    return my_list, my_dict


# Comparison to None (E711)
def bad_none_check(value):
    if value == None:
        return True
    return False


# Mutable default argument (B006)
def mutable_default(items=[]):
    items.append(1)
    return items


# Ambiguous variable name (E741)
def ambiguous_names():
    l = [1, 2, 3]
    O = 0
    I = 1
    return l, O, I


# Bare except (E722)
def bare_except():
    try:
        result = 1 / 0
    except:
        pass


# Lambda assignment (E731)
f = lambda x: x * 2

# Duplicate key (F601)
bad_dict = {"key": 1, "key": 2, "other": 3}


# Missing docstring (D100, D103)
class MyClass:
    def method_without_docstring(self):
        return 42


# Multiple imports on one line (E401)


# Unused function (also demonstrates complexity)
def unused_complex_function(a, b, c, d, e):
    if a > 0:
        if b > 0:
            if c > 0:
                if d > 0:
                    if e > 0:
                        return a + b + c + d + e
    return 0
