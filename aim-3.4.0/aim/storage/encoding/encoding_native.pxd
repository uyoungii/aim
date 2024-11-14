# distutils: language = c++
# cython: wraparound = False
# cython: boundscheck = False
# cython: cdivision=True
# cython: nonecheck=False

from libcpp.vector cimport vector
from libcpp.pair cimport pair


cpdef enum:
    PATH_SENTINEL_CODE = 0xfe

ctypedef long long int64

cpdef bytes encode_int64_big_endian(int64 value)

cpdef bytes encode_int64(int64 value)

cpdef int64 decode_int64_big_endian(const unsigned char* b) nogil

cpdef int64 decode_int64(const unsigned char* buffer) nogil

cpdef vector[pair[int64, int64]] split_path(
    const unsigned char* buffer,
    int64 length
) nogil

cpdef decode_path(bytes buffer)

cpdef bytes encode_double(double value)

cpdef double decode_double(const unsigned char* bytes) nogil

cpdef bytes encode_utf_8_str(str value)

cpdef str decode_utf_8_str(bytes buffer)
