import numpy as np

from .define_class import LIST_OR_NUMPY


def possibleFactor(num: int) -> np.ndarray:
    listOfFactor = []
    if num > 0:
        for i in np.arange(1, num + 1):
            if num % i == 0: listOfFactor.append(i)
        return np.array(listOfFactor)
    print("Input number is not a int")
    return np.array(listOfFactor)


def findClosestNum(num: int, listOfNums: LIST_OR_NUMPY) -> np.ndarray:
    listOfNums = np.array(listOfNums)
    return listOfNums[np.argmin(np.abs(listOfNums - num))]


if __name__ == "__main__":
    listOfNum = np.random.randint(-3, 5, size=4)
    print(listOfNum, "\n", findClosestNum(2, listOfNum).tolist())
