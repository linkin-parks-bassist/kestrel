set(SQLITE_AMALGAMATION_DIR "$ENV{SQLITE_AMALGAMATION_DIR}")
if(NOT EXISTS "${SQLITE_AMALGAMATION_DIR}/sqlite3.c" OR
   NOT EXISTS "${SQLITE_AMALGAMATION_DIR}/sqlite3.h")
    message(FATAL_ERROR "Set SQLITE_AMALGAMATION_DIR to the verified amalgamation directory")
endif()
idf_component_register(SRCS "probe.c" "probe_sd.c" "composed.c" "${SQLITE_AMALGAMATION_DIR}/sqlite3.c"
    INCLUDE_DIRS "${SQLITE_AMALGAMATION_DIR}"
    REQUIRES esp_timer fatfs sdmmc esp_driver_sdmmc)
target_compile_definitions(${COMPONENT_LIB} PRIVATE
    SQLITE_OS_OTHER=1 SQLITE_THREADSAFE=0 SQLITE_OMIT_LOAD_EXTENSION
    KT_PROBE_ROWS=${CONFIG_KT_PROBE_ROWS})
set_source_files_properties("${SQLITE_AMALGAMATION_DIR}/sqlite3.c" PROPERTIES
    COMPILE_OPTIONS "-include;${CMAKE_CURRENT_SOURCE_DIR}/sqlite_release_assert.h")
