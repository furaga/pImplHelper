# coding: UTF-8
import gc
import sys
import traceback
from clang.cindex import Index, File, Cursor, SourceRange, SourceLocation
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind

def convert(header, cpp):
	outheader = header
	outcpp = cpp
	return (outheader, outcpp)