# coding: UTF-8
import gc
import util
#################################################################
# 新規pImplクラスの生成
#################################################################

def gen_new_class(class_name):
	header_name = util.header_name_template.replace('<%ClassName%>', class_name)
	header_code = util.header_code_template.replace('<%ClassName%>', class_name)
	cpp_name = util.cpp_name_template.replace('<%ClassName%>', class_name)
	cpp_code = util.cpp_code_template.replace('<%ClassName%>', class_name)
	return (header_name, header_code, cpp_name, cpp_code)