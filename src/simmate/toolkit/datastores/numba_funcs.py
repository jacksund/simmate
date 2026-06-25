from numba import carray, cfunc, njit, types

numba_signature_u8 = types.float32(
    types.CPointer(types.uint8),
    types.CPointer(types.uint8),
)

numba_signature_u32 = types.float32(
    types.CPointer(types.uint32),
    types.CPointer(types.uint32),
)


@njit("int_(uint32)")
def word_popcount(v):
    """
    Count set bits in a 32-bit unsigned integer using bitwise operations.
    """
    v = v - ((v >> 1) & 0x55555555)
    v = (v & 0x33333333) + ((v >> 2) & 0x33333333)
    c = types.uint32((v + (v >> 4) & 0xF0F0F0F) * 0x1010101) >> 24
    return c


@cfunc(numba_signature_u8)
def tanimoto_maccs(a, b):
    """
    Compute Tanimoto distance for MACCS fingerprints (166 bits = 21 bytes).
    """
    a_array = carray(a, 21)
    b_array = carray(b, 21)
    ands = 0
    ors = 0
    for i in range(21):
        ands += word_popcount(types.uint32(a_array[i] & b_array[i]))
        ors += word_popcount(types.uint32(a_array[i] | b_array[i]))
    return 1 - types.float32(ands) / ors


@cfunc(numba_signature_u32)
def tanimoto_ecfp4(a, b):
    """
    Compute Tanimoto distance for ECFP4 fingerprints (2048 bits = 64 uint32 words).
    """
    a_array = carray(a, 64)
    b_array = carray(b, 64)
    ands = 0
    ors = 0
    for i in range(64):
        ands += word_popcount(a_array[i] & b_array[i])
        ors += word_popcount(a_array[i] | b_array[i])
    return 1 - types.float32(ands) / ors
