import sys
import ctypes as ct
import ida_sample_lib


from h_ida import (
    IDA_AXIS_INFO,
    IDA_OpenMode,
    CMN_RECT,
)

ida = ct.cdll.LoadLibrary("./libs/libIdaldll.so")


def main(filepath):
    hAccessor = ct.c_void_p()
    hFile = ct.c_void_p()

    # Initialize
    ida.Initialize()

    # Get Accessor
    ida.GetAccessor(filepath, ct.byref(hAccessor))
    if not hAccessor:
        print("Please check the File path")
        return

    # Connect
    ida.Connect(hAccessor)

    # Open file
    ida.Open(hAccessor, filepath, IDA_OpenMode.IDA_OM_READ, ct.byref(hFile))

    # ==============================
    # Get Properties
    # ==============================

    # Get Group Handle
    hGroup = ct.c_void_p()
    specify_group = 0  # OIR Data has only 1 group, omp2info file may have more groups
    ida.GetGroup(hAccessor, hFile, specify_group, ct.byref(hGroup))

    # GetLevelImageSize
    rect = CMN_RECT()
    specify_layer = 0  # OIR and omp2info file has only 1 layer
    ida.GetLevelImageSize(hAccessor, hGroup, specify_layer, ct.byref(rect))

    # GetArea
    hArea = ct.c_void_p()
    specify_area = ct.c_int()
    ida.GetArea(hAccessor, hGroup, specify_layer, specify_area, ct.byref(hArea))

    # make PyCapsule void pointer.
    ct.pythonapi.PyCapsule_New.restype = ct.py_object
    cps_hAccessor = ct.pythonapi.PyCapsule_New(hAccessor, None, None)
    cps_hArea = ct.pythonapi.PyCapsule_New(hArea, None, None)

    # Channel Information
    channel_info = ida_sample_lib.ChannelInfo(cps_hAccessor, cps_hArea)
    channel_info.Print()

    # Image Size
    area_image_size = ida_sample_lib.AreaImageSize(cps_hAccessor, cps_hArea)
    area_image_size.Print()

    # Get SystemInfo
    system_info = ida_sample_lib.SystemInfo(cps_hAccessor, cps_hArea)
    system_info.Print()

    # Axes Information
    axis_info = ida_sample_lib.AxisInfo(cps_hAccessor, cps_hArea)
    axis_info.Print()

    nLLoop = nTLoop = nZLoop = 0
    axis = ida_sample_lib.Axis()

    if axis_info.Exits("LAMBDA"):
        axis_info.GetAxis("LAMBDA", axis)
        nLLoop = axis.GetMax()
    if axis_info.Exits("ZSTACK"):
        axis_info.GetAxis("ZSTACK", axis)
        nZLoop = axis.GetMax()
    if axis_info.Exits("TIMELAPSE"):
        axis_info.GetAxis("TIMELAPSE", axis)
        nTLoop = axis.GetMax()

    print("nLLoop, nZLoop, nTLoop:", nLLoop, nZLoop, nTLoop)

    # Retrieve all imaged area
    rect = CMN_RECT()
    rect.width = area_image_size.GetX()
    rect.height = area_image_size.GetY()
    rect.x = 0
    rect.y = 0

    # ==============================
    # Read Image Stack
    # ==============================

    # TODO: Requires implementation.

    pAxes = (IDA_AXIS_INFO * 3)()
    nAxisCount = 1  # dummy

    # Create Frame Manager
    # TODO: Arguments must be of the appropriate type (pAxes)
    frame_manager = ida_sample_lib.FrameManager(
        cps_hAccessor, cps_hArea, channel_info.GetChannelId(0), pAxes, nAxisCount
    )

    # Get Image Body
    m_pucImageBuffer = frame_manager.GetImageBody(rect)

    # Release Image Body
    frame_manager.ReleaseImageBody()

    # ====================
    # Cleaning
    # ====================

    # Area
    ida.ReleaseArea(hAccessor, hArea)

    # Group
    ida.ReleaseGroup(hAccessor, hGroup)

    # File
    ida.Close(hAccessor, hFile)

    # Disconnect
    ida.Disconnect(hAccessor)

    # ReleaseAccessor
    ida.ReleaseAccessor(hAccessor)

    # Terminate
    ida.Terminate()


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    main(filepath)
