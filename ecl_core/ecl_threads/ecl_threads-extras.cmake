
find_package(ecl_build REQUIRED)

# ecl_detect_threads() does a bare include(FindThreads) rather than
# find_package(Threads). When this extras file runs as part of
# find_package(ecl_threads), CMAKE_FIND_PACKAGE_NAME is still "ecl_threads", so
# FindThreads' call to find_package_handle_standard_args reports a mismatched
# package name as an AUTHOR_WARNING. FPHSA_NAME_MISMATCHED is the documented way
# to say the mismatch is intentional.
set(FPHSA_NAME_MISMATCHED TRUE)
ecl_detect_threads()
unset(FPHSA_NAME_MISMATCHED)

if(ECL_PLATFORM_HAS_POSIX_THREADS)
  set(THREADS_PREFER_PTHREAD_FLAG ON)
  find_package(Threads REQUIRED)
endif()
