PROJECT(TestOGRE)
cmake_minimum_required(VERSION 3.1)

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
CONAN_BASIC_SETUP()

SET(VERBOSE 1)
SET(CMAKE_VERBOSE_MAKEFILE 1)

ADD_EXECUTABLE(example example.cpp)
target_link_libraries(example ${CONAN_LIBS})
target_compile_features(example PRIVATE cxx_lambdas)
