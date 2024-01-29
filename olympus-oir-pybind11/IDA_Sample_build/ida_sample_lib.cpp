#include <pybind11/pybind11.h>
#include <pybind11/stl_bind.h>
#include "Idaldll.h"
#include "AxisInfo.h"
#include "ChannelInfo.h"
#include "AreaImageSize.h"
#include "FrameManager.h"
#include "SystemInfo.h"

PYBIND11_MAKE_OPAQUE(std::vector<IDA_AXIS_INFO>);

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
        .def(pybind11::init<IDA_HACCESSOR, IDA_HAREA, const wchar_t *, std::vector<IDA_AXIS_INFO>& , int>())
        .def("GetImageBody", &CFrameManager::GetImageBody)
        .def("ReleaseImageBody", &CFrameManager::ReleaseImageBody)
        .def("getBufferSize", &CFrameManager::getBufferSize)
        ;

    pybind11::class_<CSystemInfo>(m, "SystemInfo")
        .def(pybind11::init<IDA_HACCESSOR, IDA_HAREA>())
        .def("Print", &CSystemInfo::Print)
        ;
    pybind11::class_<IDA_AXIS_INFO>(m, "IDA_AXIS_INFO")
        .def(pybind11::init<>())
        .def_readwrite("nType", &IDA_AXIS_INFO::nType)
        .def_readwrite("nNumber", &IDA_AXIS_INFO::nNumber);
    pybind11::enum_<IDA_AxisType>(m, "IDA_AxisType")
        .value("IDA_AT_TIME", IDA_AxisType::IDA_AT_TIME)
        .value("IDA_AT_Z", IDA_AxisType::IDA_AT_Z)
        .value("IDA_AT_LAMBDA", IDA_AxisType::IDA_AT_LAMBDA);
    pybind11::bind_vector<std::vector<IDA_AXIS_INFO>>(m, "VectorAxisInfo")
        .def(pybind11::init<int>());
    pybind11::class_<CMN_RECT>(m, "CMN_RECT")
        .def(pybind11::init<>())
        .def_readwrite("x", &CMN_RECT::x)
        .def_readwrite("y", &CMN_RECT::y)
        .def_readwrite("width", &CMN_RECT::width)
        .def_readwrite("height", &CMN_RECT::height);
} 
