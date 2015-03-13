# coding: UTF-8
import sys
from clang.cindex import CursorKind

def convert(header, cpp):
    outheader = header
    outcpp = cpp
    return (outheader, outcpp)