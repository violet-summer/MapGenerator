from vector import Vector
from util import Util

def main():
    """
    Main function to demonstrate the usage of Vector and Util classes.
    """
    v1 = Vector(3, 4)
    v2 = Vector(1, 2)

    print("Vector 1:", v1)
    print("Vector 2:", v2)

    v3 = v1.add(v2)
    print("Sum of vectors:", v3)

    v4 = v1.sub(v2)
    print("Difference of vectors:", v4)

    random_value = Util.random_range(0, 10)
    print("Random value between 0 and 10:", random_value)

if __name__ == "__main__":
    main()
