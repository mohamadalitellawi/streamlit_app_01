from handcalcs.decorator import handcalc


@handcalc()
def calc_Mr(b: float, d: float, phi: float, f_y: float):
    """
    Calculates Mr of a rectangular section
    """
    S_x = (b * d**2) / 6  # Section modulus
    M_r = phi * S_x * f_y
    return M_r