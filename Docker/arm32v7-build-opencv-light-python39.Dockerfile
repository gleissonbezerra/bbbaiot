FROM python:3.9-slim-bullseye

RUN apt-get -qq update \
    && apt-get -qq install -y --no-install-recommends \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
        pkg-config \
        python3-dev 

RUN apt-get -qq update \
    && apt-get -qq install -y --no-install-recommends \
        libjpeg-dev libpng-dev \
        libavcodec-dev libavformat-dev \
        libswscale-dev libdc1394-22-dev \
        libv4l-dev v4l-utils \
        libgtk2.0-dev libcanberra-gtk* libgtk-3-dev \
        libtbb2 libtbb-dev

RUN pip install numpy

WORKDIR /opt

RUN git clone --depth=1 https://github.com/opencv/opencv.git 

WORKDIR /opt/build

RUN cmake \
        -D CMAKE_BUILD_TYPE=RELEASE \
        -D ENABLE_NEON=ON \
        -D ENABLE_VFPV3=ON \
        -D BUILD_ZLIB=ON \
        -D BUILD_OPENMP=ON \
        -D BUILD_TIFF=OFF \
        -D BUILD_OPENJPEG=OFF \
        -D BUILD_JASPER=OFF \
        -D BUILD_OPENEXR=OFF \
        -D BUILD_WEBP=OFF \
        -D BUILD_TBB=ON \
        -D BUILD_IPP_IW=OFF \
        -D BUILD_ITT=OFF \
        -D WITH_CUDA=OFF \
        -D WITH_OPENMP=ON \
        -D WITH_OPENCL=OFF \
        -D WITH_AVFOUNDATION=OFF \
        -D WITH_CAP_IOS=OFF \
        -D WITH_CAROTENE=OFF \
        -D WITH_CPUFEATURES=OFF \
        -D WITH_EIGEN=OFF \
        -D WITH_GSTREAMER=ON \
        -D WITH_GTK=OFF \
        -D WITH_IPP=OFF \
        -D WITH_HALIDE=OFF \
        -D WITH_VULKAN=OFF \
        -D WITH_INF_ENGINE=OFF \
        -D WITH_NGRAPH=OFF \
        -D WITH_JASPER=OFF \
        -D WITH_OPENJPEG=OFF \
        -D WITH_WEBP=OFF \
        -D WITH_OPENEXR=OFF \
        -D WITH_TIFF=OFF \
        -D WITH_OPENVX=OFF \
        -D WITH_GDCM=OFF \
        -D WITH_TBB=ON \
        -D WITH_HPX=OFF \
        -D WITH_EIGEN=OFF \
        -D WITH_V4L=ON \
        -D WITH_LIBV4L=ON \
        -D WITH_VTK=OFF \
        -D WITH_QT=OFF \
        -D BUILD_TESTS=OFF \
        -D BUILD_PERF_TESTS=OFF \
        -D BUILD_opencv_python3=ON \
        -D BUILD_opencv_java=OFF \
        -D BUILD_opencv_gapi=OFF \
        -D BUILD_opencv_objc=OFF \
        -D BUILD_opencv_js=OFF \
        -D BUILD_opencv_ts=OFF \
        -D BUILD_opencv_dnn=OFF \
        -D BUILD_opencv_calib3d=OFF \
        -D BUILD_opencv_objdetect=OFF \
        -D BUILD_opencv_stitching=OFF \
        -D BUILD_opencv_ml=OFF \
        -D BUILD_opencv_world=OFF \
        -D BUILD_EXAMPLES=OFF \
        -D OPENCV_ENABLE_NONFREE=OFF \
        -D OPENCV_GENERATE_PKGCONFIG=ON \
        -D INSTALL_C_EXAMPLES=OFF \
        -D INSTALL_PYTHON_EXAMPLES=OFF \
        -D CMAKE_INSTALL_PREFIX=$(python3.9 -c "import sys; print(sys.prefix)") \
        -D PYTHON_EXECUTABLE=$(which python3.9) \
        -D PYTHON_INCLUDE_DIR=$(python3.9 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
        -D PYTHON_PACKAGES_PATH=$(python3.9 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
        /opt/opencv

RUN make -j5

RUN make install

RUN ldconfig

RUN apt-get update

RUN rm -rf /opt/build/* \
    && rm -rf /opt/opencv \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get -qq autoremove \
    && apt-get -qq clean