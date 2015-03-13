# coding: UTF-8
import unittest
import gen_class
import wrap_method
import make_pimpl
import make_nonpimpl
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
        self.input_nonpimpl = Input('TestCodes/SampleClass_nonpimpl.h', 'TestCodes/SampleClass_nonpimpl.cpp')
        self.input_hoge = Input('TestCodes/Hoge.h', 'TestCodes/Hoge.cpp')
        
    def teadDown(self):
        pass
    
    ###################################################################333
    # test: gen_class
    ###################################################################333
    def test_gen_new_class(self):
        res = gen_class.gen_new_class('SampleKlass')
        assert res[0] == 'SampleKlass.h'
        assert len(res[1]) > 0
        assert 'class Impl;' in res[1]
        assert res[2] == 'SampleKlass.cpp'
        assert len(res[3]) > 0
        assert 'class SampleKlass::Impl' in res[3]

    ###################################################################333
    # test: wrap_method
    ###################################################################333
    def test_from_selection(self):
        (header, cpp) = wrap_method.from_selection(
            self.input.header, 
            self.input.cpp, 
            0,
            len(self.input.cpp))
        (hminus, hplus) = get_diff_lines(self.input.header, header)
        (cminus, cplus) = get_diff_lines(self.input.cpp, cpp)
#        print '\n'.join(hplus)
#        print '\n'.join(cplus)
        assert len(hminus) <= 0, ("len", len(hminus))
        assert len(hplus) == 1, ("len", len(hplus))
        assert len(cminus) <= 0, ("len", len(mminus))
        assert len(cplus) == 4, ("len", len(mplus))
        
    ###################################################################333
    # test: make pimpl
    ###################################################################333
    def test_make_pimpl(self):
        (outheader, outcpp) = make_pimpl.convert(self.input_nonpimpl.header, self.input_nonpimpl.cpp)
        # print '*' * 40
        # print outheader
        # print '*' * 40
        # print outcpp
        # print '/' * 40

        (outheader, outcpp) = make_pimpl.convert(self.input_hoge.header, self.input_hoge.cpp)
        print '*' * 40
        print outheader
        print '*' * 40
        print outcpp
        print '*' * 40
        assert ('class Impl;' in outheader)
        assert ('::Impl' in outcpp)
        pass

    ###################################################################333
    # test: make nonpimpl
    ###################################################################333
    def test_make_nonpimpl(self):
        (header, cpp) = wrap_method.from_selection(
            self.input.header, 
            self.input.cpp, 
            0,
            len(self.input.cpp))
        (outheader, outcpp) = make_nonpimpl.convert(header, cpp)
        assert not ('class Impl;' in outheader)
        assert not ('::Impl' in outcpp)
        pass

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