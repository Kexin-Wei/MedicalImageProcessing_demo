cmake_minimum_required(VERSION 3.20)

project(SystematicPlan LANGUAGES CXX)

SET(CMAKE_CXX_STANDARD 11)
SET (CMAKE_CXX_STANDARD_REQUIRED ON)
SET(CMAKE_INCLUDE_CURRENT_DIR ON)
SET(CMAKE_AUTOUIC ON)
SET(CMAKE_AUTOMOC ON)
SET(CMAKE_AUTORCC ON)

# set(CMAKE_DEBUG_POSTFIX "d")

find_package(libs REQUIRED)
find_package(VTK REQUIRED COMPONENTS
    vtkCommonCore
    vtkFiltersCore
    vtkIOImage
    vtkIOGeometry
    vtkInteractionStyle
    vtkInteractionWidgets
    vtkImagingCore
    vtkRenderingCore
    vtkRenderingOpenGL2
    vtkRenderingAnnotation
)
include(${VTK_USE_FILE})

FIND_PACKAGE(Qt5 REQUIRED COMPONENTS 
    #add the components you need for qt here
    Core
    Widgets
)

set(PROJECT_HDRS
    SystematicPointPlanner.h
    SystematicPointPlanner2.h
    SystematicPointPlanner3.h
)

set(PROJECT_SOURCES
    SystematicPointPlanner.cpp
    SystematicPointPlanner2.cpp
    SystematicPointPlanner3.cpp
)

set(QT_LIBRARIES
    Qt5::Core
    Qt5::Widgets
)

set(OTHER_LIBRARIES
    ${VTK_LIBRARIES}
)
add_executable(${PROJECT_NAME} 
    main.cpp
    ${PROJECT_HDRS} 
    ${PROJECT_SOURCES}
)

target_link_libraries(${PROJECT_NAME} PUBLIC
    ${OTHER_LIBRARIES}
    ${QT_LIBRARIES}
)

SET(CONFIG_DIR ${CMAKE_CURRENT_BINARY_DIR}/$<CONFIG>)

GET_TARGET_PROPERTY(_qmake_executable Qt5::qmake IMPORTED_LOCATION)
GET_FILENAME_COMPONENT(_qt_bin_dir "${_qmake_executable}" DIRECTORY)
FIND_PROGRAM(WINDEPLOYQT_EXECUTABLE windeployqt HINTS "${_qt_bin_dir}")

ADD_CUSTOM_COMMAND(TARGET ${PROJECT_NAME} POST_BUILD 
  COMMAND "${CMAKE_COMMAND}" -E
  env PATH="${_qt_bin_dir}" "${WINDEPLOYQT_EXECUTABLE}"
  --verbose 0
  --no-compiler-runtime
  --no-angle
  --no-webkit2
  --no-quick-import
  --no-translations
  --dir $<CONFIG> $<TARGET_FILE:${PROJECT_NAME}>
)
