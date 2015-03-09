# coding: UTF-8
import unittest
import pimpl
import sys
import difflib
class Input(object):
	def __init__(self, header_path, cpp_path):
		f = open(header_path)
		self.header = f.read()  # ファイル終端まで全て読んだデータを返す
		f.close()
		f = open(cpp_path)
		self.cpp = f.read()  # ファイル終端まで全て読んだデータを返す
		f.close()

class Test(unittest.TestCase):
	def setUp(self):
		self.input = Input('TestCodes/SampleClass.h', 'TestCodes/SampleClass.cpp')
		
	def teadDown(self):
		pass
	
	def test_gen_new_class(self):
		res = pimpl.gen_new_class('SampleKlass')
		assert res[0] == 'SampleKlass.h'
		assert len(res[1]) > 0
		assert res[2] == 'SampleKlass.cpp'
		assert len(res[3]) > 0

	def test_bind_pimpl_method_from_selection(self):
#	def test_bind_pimpl_method_from_selection(header, cpp, sel_start, sel_end):
		(header, cpp) = pimpl.bind_pimpl_method_from_selection(
			self.input.header, 
			self.input.cpp, 
			0,
			len(self.input.cpp))
		(hminus, hplus) = get_diff_lines(self.input.header, header)
		(cminus, cplus) = get_diff_lines(self.input.cpp, cpp)
#		print '\n'.join(hplus)
#		print '\n'.join(cplus)
		assert len(hminus) <= 0, ("len", len(hminus))
		assert len(hplus) == 1, ("len", len(hplus))
		assert len(cminus) <= 0, ("len", len(mminus))
		assert len(cplus) == 4, ("len", len(mplus))
		
def print_diff(a, b):
	diff = difflib.unified_diff(a.splitlines(), b.splitlines())
	print '\n'.join(list(diff))
	
def get_diff_lines(a, b):
	diff = difflib.unified_diff(a.splitlines(), b.splitlines())
	lines = list(diff)
	minus = [l for l in lines if l.startswith('-') and not l.startswith('---')]
	plus = [l for l in lines if l.startswith('+') and not l.startswith('+++')]
	return (minus, plus)


unittest.main()