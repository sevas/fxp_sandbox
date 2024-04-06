cmake_minimum_required(VERSION 3.20)
project(fxp_sandbox)
set(CMAKE_CXX_STANDARD 17)



add_executable(fxp_sandbox main.cpp
    scoped_timer/scoped_timer.cpp
    scoped_timer/scoped_timer.hpp

)
target_include_directories(fxp_sandbox 
    PRIVATE 
        deps/fpm/include
        deps/stb
        scoped_timer
)
add_custom_command(TARGET fxp_sandbox POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/data/camera.png $<TARGET_FILE_DIR:fxp_sandbox>

)

if(MSVC)
    set_target_properties(fxp_sandbox
        PROPERTIES VS_DEBUGGER_WORKING_DIRECTORY $<TARGET_FILE_DIR:fxp_sandbox>)
endif()