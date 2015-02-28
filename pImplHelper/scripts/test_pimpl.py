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

	def test_get_method_ranges_from_selection(self):
		code = self.input.header
		ranges = pimpl.get_method_ranges_from_selection(code, 0, len(code))
		assert len(ranges) == 0
		code = self.input.cpp
		ranges = pimpl.get_method_ranges_from_selection(code, 0, len(code))
		funcs = [
			'Impl()', 
			'~Impl()', 
			'void SetParent(SampleClass* p)', 
			'const void f(const  int x , int z)', 
			'X g(X x)'
		]
		assert len(ranges) == len(funcs)
		for i in range(0, len(ranges)):
			method_code = code[ranges[i][0]:ranges[i][1]]
			assert method_code.find(funcs[i]) >= 0

	def test_get_class_name(self):
		cpp = pimpl.gen_new_class('SampleKlass')[3]
		assert pimpl.get_class_name(cpp) == 'SampleKlass'
		cpp = self.input.cpp
		assert pimpl.get_class_name(cpp) == 'SampleClass'

	def test_get_method_name_ret_args(self):
		code = self.input.cpp
		ranges = pimpl.get_method_ranges_from_selection(code, 0, len(code))
		expect = [
			('Impl', ('', '', ''), []),
			('~Impl', ('', '', ''), []),
			('SetParent', ('', 'void', ''), [('', 'SampleClass*', 'p')]),
			('f', ('const', 'void', ''), [('const', 'int', 'x'), ('', 'int', 'z')]),
			('g', ('template <typename X>', 'X', 'const'), [('', 'X', 'x')]),
		]
		for i in range(0, len(ranges)):
			method_code = code[ranges[i][0]:ranges[i][1]]
			res = pimpl.get_method_name_ret_args(method_code)
			exp = expect[i]
			assert len(exp) == len(res)
			for j in range(0, len(res)):
				assert len(exp[j]) == len(res[j])
				for k in range(0, len(res[j])):
					assert exp[j][k] == res[j][k]

	def test_bind_pimpl_method_from_selection(self):
#	def test_bind_pimpl_method_from_selection(header, cpp, sel_start, sel_end):
		(header, cpp) = pimpl.bind_pimpl_method_from_selection(
			self.input.header, 
			self.input.cpp, 
			0,
			len(self.input.cpp))
		(hminus, hplus) = get_diff_lines(self.input.header, header)
		(cminus, cplus) = get_diff_lines(self.input.cpp, cpp)
		print '\n'.join(hplus)
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