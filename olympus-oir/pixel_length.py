import lib


ida = lib.ida


class PixelLength:
    def __init__(self, hAccessor, hArea):
        self.m_dX = 0
        self.m_dY = 0

        result, hProp = lib.get_area_property(hAccessor, hArea, "PixelLength")

        result, pPixelLength = lib.get_property_value(hAccessor, hProp, "xLength")
        self.m_dX = pPixelLength[0].value.dDouble
        del pPixelLength

        result, pPixelLength = lib.get_property_value(hAccessor, hProp, "yLength")
        self.m_dY = pPixelLength[0].value.dDouble
        del pPixelLength

        if hProp:
            ida.ReleaseProperty(hAccessor, hProp)

    def print(self):
        print("Pixel length[um]")
        print(f"\tx = {self.m_dX}")
        print(f"\ty = {self.m_dY}")

    def get_pixel_length_x(self):
        return self.m_dX

    def get_pixel_length_y(self):
        return self.m_dY
