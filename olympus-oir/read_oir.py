import ctypes as ct
import sys

import os
import numpy as np

from area_image_size import AreaImageSize
from axis_info import AxisInfo
from channel_info import ChannelInfo
from frame_manager import FrameManager
from h_ida import CMN_RECT, IDA_AXIS_INFO, IDA_AxisType, IDA_OpenMode, IDA_Result
from lib import ida
from roi_collection import RoiCollection


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
    result = ida.Open(hAccessor, filepath, IDA_OpenMode.IDA_OM_READ, ct.byref(hFile))

    # GetNumberOfGroup
    num_of_group = ct.c_int()
    ida.GetNumOfGroups(hAccessor, hFile, ct.byref(num_of_group))

    # Get Group Handle
    hGroup = ct.c_void_p()
    specify_group = 0  # OIR Data has only 1 group, omp2info file may have more groups
    ida.GetGroup(hAccessor, hFile, specify_group, ct.byref(hGroup))

    # GetLevelImageSize
    rect = CMN_RECT()
    specify_layer = 0  # OIR and omp2info file has only 1 layer
    ida.GetLevelImageSize(hAccessor, hGroup, specify_layer, ct.byref(rect))
    layer_width = rect.width
    layer_height = rect.height

    # GetArea
    hArea = ct.c_void_p()
    specify_area = ct.c_int()
    ida.GetArea(hAccessor, hGroup, specify_layer, specify_area, ct.byref(hArea))

    # Imaging ROI Information
    imaging_roi = RoiCollection(hAccessor, hArea, "ImagingROIList", "ImagingROIInfo")

    # Channel Information
    channel_info = ChannelInfo(hAccessor, hArea)
    channel_info.print()

    # Image Size
    area_image_size = AreaImageSize(hAccessor, hArea)
    area_image_size.print()

    # Axes Information
    axis_info = AxisInfo(hAccessor, hArea)
    axis_info.print()

    pAxes = (IDA_AXIS_INFO * 3)()

    nLLoop = nTLoop = nZLoop = 0

    # For Max Loop Values for lambda, z, t
    if axis_info.exist("LAMBDA"):
        nLLoop = axis_info.get_axis("LAMBDA").get_max()
    if axis_info.exist("ZSTACK"):
        nZLoop = axis_info.get_axis("ZSTACK").get_max()
    if axis_info.exist("TIMELAPSE"):
        nTLoop = axis_info.get_axis("TIMELAPSE").get_max()

    nLLoop = nLLoop or 1
    nTLoop = nTLoop or 1
    nZLoop = nZLoop or 1

    # Prepare mex matrices
    # TODO:

    # Retrieve all imaged area
    rect.width = area_image_size.get_x()
    rect.height = area_image_size.get_y()
    rect.x = 0
    rect.y = 0

    m_pucImageBuffer = None

    # Specify channel number
    # TODO: Finally, channel_no shall be externally specifiable.
    channel_no = 0

    # Variable for storing results (image stack)
    result_stack = []

    # Retrieve Image data and TimeStamp frame-by-frame
    for i in range(nLLoop):
        for j in range(nZLoop):
            for k in range(nTLoop):
                nAxisCount = set_frame_axis_index(
                    i, j, k, imaging_roi, axis_info, pAxes, 0
                )

                # Create Frame Manager
                frame_manager = FrameManager(
                    hAccessor, hArea, channel_info.get_channel_id(0), pAxes, nAxisCount
                )
                # Get Image Body
                m_pucImageBuffer = frame_manager.get_image_body(rect)

                # NOTE: Since there are concerns about the efficiency of this process
                #       (acquiring pixel data one dot at a time), 
                #       another process (using ndarray) is used.
                # # Store Image Data Pixel by Pixel
                # frame_manager.pucBuffer_to_WORD_TM()
                # for nDataCnt in range(rect.width * rect.height):
                #     result = frame_manager.get_pixel_value_tm(nDataCnt)
                #     result += 1

                # Obtain image data in ndarray format
                pucBuffer_to_WORD_TM = frame_manager.pucBuffer_to_WORD_TM()
                pucBuffer_ndarray = np.ctypeslib.as_array(pucBuffer_to_WORD_TM)
                result_stack.append(pucBuffer_ndarray)

                frame_manager.release_image_body()

                frame_manager.get_frame_position()
                frame_manager.write_frame_position()

    # ====================
    # Output
    # ====================

    # Save image stack (tiff format)
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
    bHasAxis = [pAxisInfo.exist(key) for key in KEY]
    pAxis = [pAxisInfo.get_axis(key) for key in KEY]
    pnAxisCount = 0
    for i in range(3):
        if bHasAxis[i]:
            nSize[i] = pAxis[i].get_max()
    if pRoiCollection.has_point_roi():
        pAxes[0].nNumber = nTIndex
        pAxes[0].nType = IDA_AxisType.IDA_AT_TIME
        pnAxisCount = 1
    elif pRoiCollection.has_multi_point_roi():
        pAxes[0].nNumber = nTIndex
        pAxes[0].nType = IDA_AxisType.IDA_AT_TIME
        pnAxisCount = 1
    elif pRoiCollection.has_mapping_roi():
        if bHasAxis[1] == False:
            pAxes[0].nNumber = nTIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 1
        else:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_Z
            pAxes[1].nNumber = nTIndex
            pAxes[1].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 2
    elif pRoiCollection.has_line_roi():
        if bHasAxis[0] == False and bHasAxis[1] == False and bHasAxis[2] == True:
            pAxes[0].nNumber = nTIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 1
        elif bHasAxis[0] == False and bHasAxis[1] == True and bHasAxis[2] == False:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_Z
            pnAxisCount = 1
        elif bHasAxis[0] == False and bHasAxis[1] == True and bHasAxis[2] == True:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_Z
            pAxes[1].nNumber = nTIndex
            pAxes[1].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 2
        else:
            # TODO: What?
            pass
    else:
        if nSize[0] != 0 and nSize[1] != 0 and nSzie[2] != 0:
            pAxes[0].nNumber = nLIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_LAMBDA
            pAxes[1].nNumber = nZIndex
            pAxes[1].nType = IDA_AxisType.IDA_AT_Z
            pAxes[2].nNumber = nTIndex
            pAxes[2].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 3
        elif nSize[0] != 0 and nSize[1] != 0 and nSize[2] == 0:
            pAxes[0].nNumber = nLIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_LAMBDA
            pAxes[1].nNumber = nZIndex
            pAxes[1].nType = IDA_AxisType.IDA_AT_Z
            pnAxisCount = 2
        elif nSize[0] != 0 and nSize[1] == 0 and nSize[2] != 0:
            pAxes[0].nNumber = nLIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_LAMBDA
            pAxes[1].nNumber = nTIndex
            pAxes[1].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 2
        elif nSize[0] == 0 and nSize[1] != 0 and nSize[2] != 0:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_Z
            pAxes[1].nNumber = nTIndex
            pAxes[1].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 2
        elif nSize[0] != 0 and nSize[1] == 0 and nSize[2] == 0:
            pAxes[0].nNumber = nLIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_LAMBDA
            pnAxisCount = 1
        elif nSize[0] == 0 and nSize[1] != 0 and nSize[2] == 0:
            pAxes[0].nNumber = nZIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_Z
            pnAxisCount = 1
        elif nSize[0] == 0 and nSize[1] == 0 and nSize[2] != 0:
            pAxes[0].nNumber = nTIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 1
        elif nSize[0] == 0 and nSize[1] == 0 and nSize[2] == 0:
            pAxes[0].nNumber = nTIndex
            pAxes[0].nType = IDA_AxisType.IDA_AT_TIME
            pnAxisCount = 1
    del pAxis
    return pnAxisCount


if __name__ == "__main__":
    filepath = sys.argv[1]
    main(filepath)
