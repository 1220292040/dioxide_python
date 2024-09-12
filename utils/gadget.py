def get_length_recalculated(str):
    i = 0
    bs = bytes(str)
    while i<len(str):
        print(bs[i])
        if bs[i] == 0:
            return i
        i += 1
    return i



