cmake_minimum_required(VERSION 3.5)
project(rosslt_py_msgs)

# Default to C99
if(NOT CMAKE_C_STANDARD)
  set(CMAKE_C_STANDARD 99)
endif()

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(visualization_msgs REQUIRED)
find_package(builtin_interfaces REQUIRED)
find_package(rosidl_default_generators REQUIRED)

rosidl_generate_interfaces(rosslt_py_msgs
  "msg/Expression.msg"
  "msg/Location.msg"
  "msg/LocationHeader.msg"
  "msg/SetValue.msg"
  "msg/TrackedInt32.msg"
  "msg/TrackedMarker.msg"
  "msg/TrackedPose.msg"
  "srv/GetValue.srv"
  DEPENDENCIES builtin_interfaces std_msgs visualization_msgs
)

ament_package()
