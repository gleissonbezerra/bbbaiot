FROM python:3.9-slim-bullseye

RUN apt-get update
RUN apt-get upgrade 

RUN apt-get install -y  \
        build-essential \
        cmake \
        git \
        wget \
        unzip \
        pkg-config \
        python3-dev \
        python3-numpy

RUN apt-get install -y  \
        libjpeg-dev libpng-dev \
        libavcodec-dev libavformat-dev \
        libswscale-dev libdc1394-22-dev \
        libv4l-dev v4l-utils \
        libgtk2.0-dev libcanberra-gtk* libgtk-3-dev \
        libtbb2 libtbb-dev

WORKDIR /opt

RUN git clone --depth=1 https://github.com/opencv/opencv.git 

WORKDIR /opt/build

RUN cmake \
        -D ENABLE_NEON=ON \
        -D BUILD_opencv_java=OFF \
        -D WITH_CUDA=OFF \
        -D WITH_OPENGL=ON \
        -D WITH_V4L=ON \
        -D INSTALL_PYTHON_EXAMPLES=OFF \
        -D BUILD_EXAMPLES=OFF\
        -D BUILD_TESTS=OFF \
        -D BUILD_PERF_TESTS=OFF \
        -D CMAKE_BUILD_TYPE=RELEASE \
        -D CMAKE_INSTALL_PREFIX=$(python3.9 -c "import sys; print(sys.prefix)") \
        -D PYTHON_EXECUTABLE=$(which python3.9) \
        -D PYTHON_INCLUDE_DIR=$(python3.9 -c "from distutils.sysconfig import get_python_inc; print(get_python_inc())") \
        -D PYTHON_PACKAGES_PATH=$(python3.9 -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())") \
        /opt/opencv

RUN make -j4

RUN make install

RUN ldconfig

RUN apt-get update

RUN rm -rf /opt/build/* \
    && rm -rf /opt/opencv \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get -qq autoremove \
    && apt-get -qq clean