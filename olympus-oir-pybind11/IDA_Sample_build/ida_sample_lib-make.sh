# make `ida_sample_lib*.so` command.
g++ -O3 -Wall -shared -std=c++11 -fPIC $(python3 -m pybind11 --includes) \
  ida_sample_lib.cpp AxisInfo.cpp AreaImageSize.cpp ChannelInfo.cpp FrameManager.cpp RoiCollection.cpp SystemInfo.cpp Tiff.cpp \
  -I ../../IDAL/include -L../../IDAL/lib -lIdaldll -ltiff -o ida_sample_lib$(python3-config --extension-suffix)
