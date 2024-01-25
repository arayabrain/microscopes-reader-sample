#include <pybind11/pybind11.h>
#include "Idaldll.h"
#include "AxisInfo.h"
#include "ChannelInfo.h"
#include "AreaImageSize.h"
#include "FrameManager.h"
#include "SystemInfo.h"

PYBIND11_MODULE(ida_sample_lib, m) {
    pybind11::class_<CAxisInfo>(m, "AxisInfo")
        .def(pybind11::init<IDA_HACCESSOR, IDA_HAREA>())
        .def("GetAxis", &CAxisInfo::GetAxis)
        .def("Exits", &CAxisInfo::Exits)
        .def("Print", &CAxisInfo::Print)
        ;

    pybind11::class_<CAxis>(m, "Axis")
        .def(pybind11::init<>())
        .def("GetMax", &CAxis::GetMax)
        ;

    pybind11::class_<CAreaImageSize>(m, "AreaImageSize")
        .def(pybind11::init<IDA_HACCESSOR, IDA_HAREA>())
        .def("GetX", &CAreaImageSize::GetX)
        .def("GetY", &CAreaImageSize::GetY)
        .def("Print", &CAreaImageSize::Print)
        ;

    pybind11::class_<CChannelInfo>(m, "ChannelInfo")
        .def(pybind11::init<IDA_HACCESSOR, IDA_HAREA>())
        .def("GetChannelId", &CChannelInfo::GetChannelId)
        .def("Print", &CChannelInfo::Print)
        ;

    pybind11::class_<CFrameManager>(m, "FrameManager")
        .def(pybind11::init<IDA_HACCESSOR, IDA_HAREA, const wchar_t *, IDA_AXIS_INFO *, int>())
        .def("GetImageBody", &CFrameManager::GetImageBody)
        .def("ReleaseImageBody", &CFrameManager::ReleaseImageBody)
        .def("getBufferSize", &CFrameManager::getBufferSize)
        ;

    pybind11::class_<CSystemInfo>(m, "SystemInfo")
        .def(pybind11::init<IDA_HACCESSOR, IDA_HAREA>())
        .def("Print", &CSystemInfo::Print)
        ;
} 
