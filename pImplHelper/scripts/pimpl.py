# coding: UTF-8
import sys;

def gen_new_class(class_name):
	header_name_template = """<%ClassName%>.h"""
	header_code_template = """#pragma once

class <%ClassName%>
{
public:
	<%ClassName%>();
	~<%ClassName%>();
	void f();
private:
	class Impl;
	Impl* pImpl;
};
"""
	cpp_name_template = """<%ClassName%>.cpp"""
	cpp_code_template = """#include "<%ClassName%>.h"
#include <stdio.h>
/*
How to use:
#include "<%ClassName%>.h"
int main()
{
	<%ClassName%>* inst = new <%ClassName%>();
	inst->f();
	delete inst;
	inst = nullptr;

	return 0;
}
*/

class <%ClassName%>::Impl{
	friend <%ClassName%>;
	<%ClassName%>* parent;
public:
	Impl()
	{
		printf("create <%ClassName%>\\n");
	}
	~Impl()
	{
		printf("delete <%ClassName%>\\n");
	}
	void SetParent(<%ClassName%>* p)
	{
		this->parent = p;
	}
	void f()
	{
		printf("<%ClassName%>::f()\\n");
	}
};

<%ClassName%>::<%ClassName%>()
{
	pImpl = new <%ClassName%>::Impl();
	pImpl->SetParent(this);
}
<%ClassName%>::~<%ClassName%>()
{
	if (pImpl != nullptr)
		delete pImpl;
	pImpl = nullptr;
}
void <%ClassName%>::f()
{
	pImpl->f();
}"""
	header_name = header_name_template.replace('<%ClassName%>', class_name)
	header_code = header_code_template.replace('<%ClassName%>', class_name)
	cpp_name = cpp_name_template.replace('<%ClassName%>', class_name)
	cpp_code = cpp_code_template.replace('<%ClassName%>', class_name)
	return (header_name, header_code, cpp_name, cpp_code)

def get_bracket_range(code, idx):
	start = code.find('{', idx)
	if start < 0:
		return (-1, 0)
	nest = 1
	pos = start + 1
	while True:
		p1 = code.find('{', pos)
		if p1 < 0:
			p1 = sys.maxint
		p2 = code.find('}', pos)
		if p2 < 0:
			p2 = sys.maxint
		if p1 == p2:
			return (-1, 0);
		if p1 < p2: # '{'
			pos = p1 + 1
			nest = nest + 1
		else: #'}'
			pos = p2 + 1
			nest = nest - 1
			if nest <= 0:
				break
	return (start, pos)

def get_method_ranges_from_selection(code, sel_start, sel_end):
	pos = code.find('::Impl')
	if pos < 0:
		return []
	(b_start, b_end) = get_bracket_range(code, pos)
	if sel_end <= b_start or b_end <= sel_start:
		return []
	pos = b_start + 1
	ranges = []
	while True:
		(s, e) = get_bracket_range(code, pos)
		if s <= b_start or b_end <= s:
			break
		if pos <= sel_end and sel_start <= e:
			snip = code[:s]
			mstart = max(snip.rfind('{'), snip.rfind('}'), snip.rfind(';'), snip.rfind(':')) + 1
			if mstart <= sel_end:
				ranges.append((mstart, e))
		pos = e + 1
	return ranges
	
def make_method_dclr(code, class_name, method_name):
	dclr = code[0:code.find('{')].strip() + ';'
	if method_name == 'Impl' or method_name == '~Impl':
		dclr = dclr.replace('Impl', class_name)
	return dclr

def get_class_name(code):
	pos1 = code.find('::Impl')
	pos2 = code.rfind(' ', 0, pos1)
	return code[pos2 + 1:pos1].strip()

def get_method_name_ret_args(code):
	pos1 = code.find('(')
	if pos1 < 0:
		return ()
	pos2 = code.find(')', pos1)
	if pos2 < 0:
		return ()
	ret_name_tokens = code[0:pos1].split()
	# 修飾子と型
	if len(ret_name_tokens) >= 2:
		prefix = ' '.join(ret_name_tokens[0:-2])
		type = ret_name_tokens[-2].strip()
		_p = code.find('{', pos2)
		if _p < 0:
			_p = code.find(';', pos2)
		suffix = code[pos2 + 1:_p].strip()
		ret_info = (prefix, type, suffix)
	else:
		ret_info = ('', '', '')
	method_name = ret_name_tokens[-1].strip()
	args = code[pos1 + 1:pos2].split(',')
	args_info = []
	for arg in args:
		ls = arg.strip().split()
		if len(ls) >= 2:
			args_info.append((' '.join(ls[0:-2]), ls[-2], ls[-1]))
	return (method_name, ret_info, args_info)

def get_method_start_pos(code, cursor):
	_code = code.replace('::', '--')
	mstart = max(
		_code.rfind('{', 0, cursor), 
		_code.rfind('}', 0, cursor), 
		_code.rfind(';', 0, cursor), 
		_code.rfind(':', 0, cursor)) + 1
	return mstart

def is_exist_method_dclr(code, class_name, method_name_ret_args):
	pos = -1
	
	method_name = method_name_ret_args[0]
	if method_name == 'Impl' or method_name == '~Impl':
		method_name = method_name.replace('Impl', class_name)
	ret = method_name_ret_args[1]
	args = method_name_ret_args[2]
	
	while True:
		pos = code.find(';', pos + 1)
		if pos < 0:
			break;
		mstart = get_method_start_pos(code, pos)
		method_code = code[mstart:pos + 1]
		method_info = get_method_name_ret_args(method_code)

		if len(method_info) != 3:
			continue;
		if method_info[0] != method_name: # 関数名
			continue
		same = True
		for i in range(0, 3):
			if method_info[1][i] != ret[i]: # 型
				same = False
				break;
		if same == False:
			continue

		if len(method_info[2]) != len(args): # 引数の個数
			continue
		for i in range(0, len(args)):
			for j in range(0, 3):
				if method_info[2][i][j] != args[i][j]:
					same = False
					break;
			if same == False:
				break;
		if same == False:
			continue

		return True
	return False
	
def is_exist_method_definition(code, class_name, method_name_ret_args):
	pos = -1
	
	method_name = method_name_ret_args[0]
	if method_name == 'Impl' or method_name == '~Impl':
		method_name = method_name.replace('Impl', class_name)
	ret = method_name_ret_args[1]
	args = method_name_ret_args[2]
	
	while True:
		pos = code.find('{', pos + 1)
		if pos < 0:
			break;
		mstart = get_method_start_pos(code, pos)
		method_code = code[mstart:pos + 1]
		method_info = get_method_name_ret_args(method_code)

		if len(method_info) != 3:
			continue;
		if method_info[0] != class_name + '::' + method_name: # 関数名
			continue
		if method_info[1][1] != ret[1]: # 型名
			continue
		if len(method_info[2]) != len(args): # 引数の個数
			continue

		arg_types1 = [arg[1] for arg in args]
		arg_types2 = [arg[1] for arg in method_info[2]]
		for i in range(0, len(arg_types1)):
			if arg_types1[i] != arg_types2[i]:
				continue
		return True
	return False

def make_bind_code(class_name, method_name_ret_args):
	name = method_name_ret_args[0]
	ret_info = method_name_ret_args[1]
	args_info = method_name_ret_args[2]
	
	arg_type_names = []
	arg_names = []
	for a in args_info:
		arg_type_names.append(a[-2] + ' ' + a[-1])
		arg_names.append(a[-1])
	
	arg_type_names_code = ', '.join(arg_type_names)
	arg_names_code = ', '.join(arg_names)
	
	if name == 'Impl':
		code = class_name + '::' + class_name + '(' + arg_type_names_code + ')\n'
		code += '{\n'
		code += '	pImpl = new ' + class_name + '::Impl(' + arg_names_code + ');\n'
		code += '	pImpl->SetParent(this);\n'
		code += '}\n'
	elif name == '~Impl':
		code = class_name + '::~' + class_name + '(' + arg_type_names_code + ')\n'
		code += '{\n'
		code += '	if (pImpl != nullptr)\n'
		code += '		delete pImpl;\n'
		code += '	pImpl = nullptr;\n'
		code += '}\n'
	else:
		code = ret_info[1] + ' ' + class_name + '::' + name + '(' + arg_type_names_code + ')\n'
		code += '{\n'
		if ret_info[1] == 'void':
			code += '	pImpl->' + name + '(' + arg_names_code +');\n'
		else:
			code += '	return pImpl->' + name + '(' + arg_names_code +');\n'
		code += '}\n'
	
	return code

def bind_pimpl_method(header, cpp, method_start, method_end):
	out_header = header
	out_cpp = cpp
	pimpl_method_code = cpp[method_start:method_end].strip()	
	class_name = get_class_name(cpp)
	method_name_ret_args = get_method_name_ret_args(pimpl_method_code)
	
	# setparent()は問答無用でBindしない
	if method_name_ret_args[0] == 'SetParent':
		return (out_header, out_cpp)
	
	if len(method_name_ret_args) != 3:
		raise Exception('Invalid method code:\n' + pimpl_method_code)
	
	# headerを書き変え
	dclr_exist = is_exist_method_dclr(header, class_name, method_name_ret_args)
	if not dclr_exist:
		dclr_code = make_method_dclr(pimpl_method_code, class_name, method_name_ret_args[0])
		dclr_code = dclr_code.replace('\r', ' ')
		dclr_code = dclr_code.replace('\n', ' ')
		pub_start = out_header.find('public:')
		class_end = out_header.rfind('};')
		if pub_start < 0:
			dclr_code = "public:\n\t" + dclr_code + "\n"
			out_header = out_header[:class_end] + dclr_code + out_header[class_end:]
		else:
			pri_start= out_header.find('private:', pub_start)
			if pri_start < 0:
				pri_start = sys.maxint
			pro_start= out_header.find('protected:', pub_start)
			if pro_start < 0:
				pro_start = sys.maxint
			insert_pos = min(pri_start, pro_start, class_end)
			dclr_code = "\t" + dclr_code + "\n"
			out_header = out_header[:insert_pos] + dclr_code + out_header[insert_pos:]
	
	# cppを書き変え
	bind_exist = is_exist_method_definition(cpp, class_name, method_name_ret_args)
	if not bind_exist:
		bind_code = make_bind_code(class_name, method_name_ret_args)
		out_cpp += '\n' + bind_code

	return (out_header, out_cpp)

def bind_pimpl_method_from_selection(header, cpp, sel_start, sel_end):
	out_header = header
	out_cpp = cpp
	ranges = get_method_ranges_from_selection(cpp, sel_start, sel_end)
	if len(ranges) <= 0:
		raise Exception('No public method is selected.')
	for (m_start, m_end) in ranges:
		if m_start < 0:
			continue
		res = bind_pimpl_method(out_header, out_cpp, m_start, m_end)
		out_header = res[0]
		out_cpp = res[1]
	return (out_header, out_cpp)
