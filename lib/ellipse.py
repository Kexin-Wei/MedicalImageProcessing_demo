import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as pat


def kidney_displacement(t: float, A: float, T: float, varphi: float) -> float:
    # y = A*sin(2*pi / T * t + varphi)
    return A * np.sin(2 * np.pi / T * t + varphi)


def draw_ellipse(
    ax: plt.Axes,
    width: float,
    height: float,
    angle: float = 0,
    xc: float = 0,
    yc: float = 0,
    **kwargs,
) -> None:
    e = pat.Ellipse(
        (xc, yc), width, height, angle=np.rad2deg(angle), fill=False, **kwargs
    )
    ax.add_patch(e)


def intersection_of_line_ellipse(k: float, c: float, a: float, b: float) -> list:
    # line: y = kx + c, k = arctan(lineAnlge)
    # ellipse: x^2 / a^2 + y^2 / b^2 = 1
    A = (a * k) ** 2 + b**2
    B = 2 * a**2 * k * c
    C = (a * c) ** 2 - (a * b) ** 2
    xPos = (-B + np.sqrt(B**2 - 4 * A * C)) / 2 / A
    xNeg = (-B - np.sqrt(B**2 - 4 * A * C)) / 2 / A
    yPos = k * xPos + c
    yNeg = k * xNeg + c
    return [xNeg, xPos, yNeg, yPos]


def draw_line(
    ax: plt.Axes, xStart: float, xEnd: float, c: float, k: float = 0, *args, **kwargs
) -> None:
    if xStart != np.nan and xEnd != np.nan:
        xs = np.linspace(xStart, xEnd, int(5e2), True)
        ax.plot(xs, k * xs + c, *args, **kwargs)


def ellipse_x(y: float, a: float, b: float) -> float:
    # return positive x given a y in an ellipse
    return np.sqrt((1 - y**2 / b**2) * a**2)
