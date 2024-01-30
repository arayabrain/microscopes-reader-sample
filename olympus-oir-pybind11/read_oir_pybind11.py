import os
import sys
import ctypes as ct
import ida_sample_lib

import numpy as np

from h_ida import (
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

    # Imaging ROI Information
    imaging_roi = ida_sample_lib.RoiCollection(
        cps_hAccessor,
        cps_hArea,
        "ImagingROIList",
        "ImagingROIInfo"
    )

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

    nLLoop = nLLoop or 1
    nZLoop = nZLoop or 1
    nTLoop = nTLoop or 1

    print("nLLoop, nZLoop, nTLoop:", nLLoop, nZLoop, nTLoop)

    # Retrieve all imaged area
    rect = ida_sample_lib.CMN_RECT()
    rect.width = area_image_size.GetX()
    rect.height = area_image_size.GetY()
    rect.x = 0
    rect.y = 0

    # ==============================
    # Read Image Stack
    # ==============================

    pAxes = ida_sample_lib.VectorAxisInfo(3)
    nAxisCount = 1  # dummy

    result_stack = []

    for i in range(nLLoop):
        for j in range(nZLoop):
            for k in range(nTLoop):
                nAxisCount = set_frame_axis_index(
                    i, j, k, imaging_roi, axis_info, pAxes, 0
                )

                # Create Frame Manager
                frame_manager = ida_sample_lib.FrameManager(
                    cps_hAccessor, cps_hArea, channel_info.GetChannelId(0), pAxes, nAxisCount
                )

                # Get Image Body
                m_pucImageBuffer = frame_manager.GetImageBody(rect)

                # Obtain Image data in ndarray format
                buffer_size = ct.c_uint16 * area_image_size.GetX() * area_image_size.GetY()
                pucBuffer = buffer_size.from_buffer(bytearray(m_pucImageBuffer))
                pucBuffer_ndarray = np.ctypeslib.as_array(pucBuffer)
                result_stack.append(pucBuffer_ndarray)

                frame_manager.ReleaseImageBody()

                frame_manager.GetFramePosition()
                frame_manager.WriteFramePosition()

    # ====================
    # Output
    # ====================

    # Save image stack (tiff format)
    channel_no = 0
    from PIL import Image
    save_stack = [Image.fromarray(frame) for frame in result_stack]
    save_path = (
        os.path.basename(filepath) + f".out.ch{channel_no}.tiff"
    )
    print(f"save image: {save_path}")
    save_stack[0].save(
        save_path,
        compression="tiff_deflate",
        save_all=True,
        append_images=save_stack[1:],
    )


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


def set_frame_axis_index(
    nLIndex, nZIndex, nTIndex, pRoiCollection, pAxisInfo, pAxes, pnAxisCount
):
    # 0: LAxis
    # 1: ZAxis
    # 2: TAxis
    KEY = ["LAMBDA", "ZSTACK", "TIMELAPSE"]
    nSize = [0] * 3
    bHasAxis = [pAxisInfo.Exits(key) for key in KEY]
    pAxis = [ida_sample_lib.Axis() for key in KEY]
    for key, axis in zip(KEY, pAxis):
        pAxisInfo.GetAxis(key, axis)
    pnAxisCount = 0
    for i in range(3):
        if bHasAxis[i]:
            nSize[i] = pAxis[i].GetMax()

    if pRoiCollection.hasPointROI():
        pAxes[0].nNumber = nTIndex
        pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
        pnAxisCount = 1
    elif pRoiCollection.hasMultipointROI():
        pAxes[0].nNumber = nTIndex
        pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
        pnAxisCount = 1
    elif pRoiCollection.hasMappingROI():
        if bHasAxis[1] == False:
            pAxes[0].nNumber = nTIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 1
        else:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_Z
            pAxes[1].nNumber = nTIndex
            pAxes[1].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 2
    elif pRoiCollection.hasLineROI():
        if bHasAxis[0] == False and bHasAxis[1] == False and bHasAxis[2] == True:
            pAxes[0].nNumber = nTIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 1
        elif bHasAxis[0] == False and bHasAxis[1] == True and bHasAxis[2] == False:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_Z
            pnAxisCount = 1
        elif bHasAxis[0] == False and bHasAxis[1] == True and bHasAxis[2] == True:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_Z
            pAxes[1].nNumber = nTIndex
            pAxes[1].nType = ida_samle_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 2
        else:
            pass
    else:
        if nSize[0] != 0 and nSize[1] != 0 and nSzie[2] != 0:
            pAxes[0].nNumber = nLIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_LAMBDA
            pAxes[1].nNumber = nZIndex
            pAxes[1].nType = ida_sample_lib.IDA_AxisType.IDA_AT_Z
            pAxes[2].nNumber = nTIndex
            pAxes[2].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 3
        elif nSize[0] != 0 and nSize[1] != 0 and nSize[2] == 0:
            pAxes[0].nNumber = nLIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_LAMBDA
            pAxes[1].nNumber = nZIndex
            pAxes[1].nType = ida_sample_lib.IDA_AxisType.IDA_AT_Z
            pnAxisCount = 2
        elif nSize[0] != 0 and nSize[1] == 0 and nSize[2] != 0:
            pAxes[0].nNumber = nLIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_LAMBDA
            pAxes[1].nNumber = nTIndex
            pAxes[1].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 2
        elif nSize[0] == 0 and nSize[1] != 0 and nSize[2] != 0:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_Z
            pAxes[1].nNumber = nTIndex
            pAxes[1].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 2
        elif nSize[0] != 0 and nSize[1] == 0 and nSize[2] == 0:
            pAxes[0].nNumber = nLIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_LAMBDA
            pnAxisCount = 1
        elif nSize[0] == 0 and nSize[1] != 0 and nSize[2] == 0:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_Z
            pnAxisCount = 1
        elif nSize[0] == 0 and nSize[1] == 0 and nSize[2] != 0:
            pAxes[0].nNumber = nTIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 1
        elif nSize[0] == 0 and nSize[1] == 0 and nSize[2] == 0:
            pAxes[0].nNumber = nTIndex
            pAxes[0].nType = ida_sample_lib.IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 1
    del pAxis
    return pnAxisCount


if __name__ == "__main__":
    filepath = sys.argv[1] if len(sys.argv) > 1 else None
    main(filepath)
