import ctypes as ct
import json
import os
import sys

from area_image_size import AreaImageSize
from axis_info import AxisInfo
from channel_info import ChannelInfo
from file_creation_time import FileCreationTime
from h_ida import CMN_RECT, IDA_OpenMode, IDA_Result
from lib import ida
from objective_lens_info import ObjectiveLensInfo
from pixel_length import PixelLength
from system_info import SystemInfo
from user_comment import UserComment


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

    # GetNumberOfLevels
    num_of_layer = ct.c_int()
    ida.GetNumOfLevels(hAccessor, hGroup, ct.byref(num_of_layer))

    # GetLevelImageSize
    rect = CMN_RECT()
    specify_layer = 0  # OIR and omp2info file has only 1 layer
    ida.GetLevelImageSize(hAccessor, hGroup, specify_layer, ct.byref(rect))
    layer_width = rect.width
    layer_height = rect.height

    # GetNumOfArea
    num_of_area = ct.c_int()
    ida.GetNumOfArea(hAccessor, hGroup, specify_layer, ct.byref(num_of_area))

    # GetArea
    hArea = ct.c_void_p()
    specify_area = ct.c_int()
    ida.GetArea(hAccessor, hGroup, specify_layer, specify_area, ct.byref(hArea))

    # ==============================
    # Get Area Properties
    # ==============================

    # Channel Information
    channel_info = ChannelInfo(hAccessor, hArea)

    # Image Size
    area_image_size = AreaImageSize(hAccessor, hArea)
    area_image_size.print()

    # Axes Information
    axis_info = AxisInfo(hAccessor, hArea)
    axis_info.print()

    # Pixel Length
    pixel_length = PixelLength(hAccessor, hArea)
    pixel_length.print()

    # Objective Lens Info
    objective_lens_info = ObjectiveLensInfo(hAccessor, hArea)
    objective_lens_info.print()

    # File Creation Time
    file_creation_time = FileCreationTime(hAccessor, hArea)
    file_creation_time.print()

    # System Information
    system_info = SystemInfo(hAccessor, hArea)
    system_info.print()

    # User Comment
    user_comment = UserComment(hAccessor, hArea)
    user_comment.print()

    # ====================
    # Something here
    # ====================
    nLLoop = nTLoop = nZLoop = 0
    Zstep = Zstart = Zend = Tstep = 0.0

    if axis_info.exist("LAMBDA"):
        axis = axis_info.get_axis("LAMBDA")
        nLLoop = axis.get_max()
    nLLoop = nLLoop or 1
    if axis_info.exist("ZSTACK"):
        axis = axis_info.get_axis("ZSTACK")
        nZLoop = axis.get_max()
        Zstep = axis.get_step()
        Zstart = axis.get_start()
        Zend = axis.get_end()
    nZLoop = nZLoop or 1
    if axis_info.exist("TIMELAPSE"):
        axis = axis_info.get_axis("TIMELAPSE")
        nTLoop = axis.get_max()
        Tstep = axis.get_step()
    nTLoop = nTLoop or 1
    print(nLLoop, nTLoop, nZLoop)

    # ====================
    # Output
    # ====================

    result_data = {
        "uiWidth": rect.width,
        "uiHeight": rect.height,
        "Loops": nTLoop,
        "ZSlicenum": nZLoop,
        "nChannel": channel_info.get_num_of_channel(),
        "PixelLengthX": pixel_length.get_pixel_length_x(),
        "PixelLengthY": pixel_length.get_pixel_length_y(),
        "ZInterval": Zstep,
        "TInterval": Tstep,
        "ZStart": Zstart,
        "ZEnd": Zend,
        "ObjectiveName": "",  # TODO: need to convert to str.
        # "ObjectiveName": # objective_lens_info.get_name_tm(hAccessor, hArea),
        "ObjectiveMag": objective_lens_info.get_magnification_tm(),
        "ObjectiveNA": objective_lens_info.get_na_tm(),
        "ReflectiveIndex": objective_lens_info.get_reflective_index_tm(),
        "Immersion": "",  # TODO: need to convert to str.
        # "Immersion": objective_lens_info.get_immersion_tm(),
        "Date": "",  # TODO: need to convert to str.
        # "Date": file_creation_time.get_file_creation_time_tm(hAccessor, hArea),
        "NumberOfGroup": num_of_group.value,
        "NumberOfLevel": num_of_layer.value,
        "NumberOfArea": num_of_area.value,
        "ByteDepthCh0": "",  # TODO: Need to resolve get_depth_of_ch0_tm() error.
        # "ByteDepthCh0": channel_info.get_depth_of_ch0_tm(),
        "SystemName": system_info.m_szSystemName,
        "SystemVersion": system_info.m_szSystemVersion,
        "DeviceName": system_info.m_szDeviceName,
        "UserName": system_info.m_szUserName,
        "CommentByUser": user_comment.m_szComment,
    }

    print("------------ result_data:")
    print(json.dumps(result_data, indent=2))
    save_path = os.path.basename(filepath) + f".out.metadata.json"
    with open(save_path, "w") as f:
        json.dump(result_data, f, indent=2)

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
    filepath = sys.argv[1]
    main(filepath)
