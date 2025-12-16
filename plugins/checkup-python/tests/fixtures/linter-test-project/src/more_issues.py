"""Another module with different types of issues."""

# Star import (F403, F405)
from os import *


# Redefined built-in (A001)
def list(items):
    return items


# Shadowing outer scope (F812)
name = "outer"


def function():
    name = "inner"
    return name


# Type comparison (E721)
def bad_type_check(value):
    if type(value) == str:
        return True
    return False


# String concatenation in loop (PERF401)
def inefficient_concat():
    result = ""
    for i in range(100):
        result = result + str(i)
    return result


# Boolean comparison (E712)
def bad_bool_check(flag):
    if flag == True:
        return "yes"
    if flag == False:
        return "no"


# Unnecessary pass (PIE790)
def empty_function():
    pass
    pass


# F-string without placeholders (F541)
def useless_fstring():
    return "This is just a regular string"


class BadClass:
    # Missing space after comment#like this
    def method(self):
        return 1
