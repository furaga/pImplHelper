# coding: UTF-8
import gc
import sys
import traceback
from clang.cindex import Index, File, Cursor, SourceRange, SourceLocation
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind

#################################################################
# ::Implクラス内のpublic関数を元クラスにバインド
#################################################################

def get_impl_class_cursor(nodes):
	for n in nodes:
		if n.kind == CursorKind.CLASS_DECL and n.displayname == 'Impl':
			return n
	return None

method_kinds = {
	CursorKind.CONSTRUCTOR, 
	CursorKind.DESTRUCTOR, 
	CursorKind.CXX_METHOD,
	CursorKind.FUNCTION_DECL,
	CursorKind.FUNCTION_TEMPLATE,
	CursorKind.CONVERSION_FUNCTION, 
}

def get_public_methods(klass, code):
	methods = []
	accessor = 'private:'
	for n in list(klass.get_children()):
		if n.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
			accessor = code[n.extent.start.offset:n.extent.end.offset].strip()
		elif accessor == 'public:' or accessor == 'protected:':
			if n.kind in method_kinds:
				methods.append(n)
	return methods

def get_arg_types(arg_ranges, code):
	types = []
	for r in arg_ranges:
		tokens = code[r[0]:r[1]].split()
		if len(tokens) <= 1:
			types.append(' ')
		if not ('<' in tokens):
			types.append(tokens[-2])
		else:
			idx = tokens.index('<') - 1
			if idx < 0:
				types.append(' ')
			else:
				types.append(' '.join(tokens[idx:-1]))
	return types

def get_arg_names(arg_ranges, code):
	types = []
	for r in arg_ranges:
		tokens = code[r[0]:r[1]].split()
		if len(tokens) <= 0:
			types.append(' ')
		else:
			types.append(tokens[-1])
	return types

def get_arg_type_names(arg_ranges, code):
	types = get_arg_types(arg_ranges, code)
	names = get_arg_names(arg_ranges, code)
	assert len(types) == len(names)
	ret = []
	for i in range(0, len(types)):
		ret.append(types[i] + ' ' + names[i])
	return ret

def get_arg_ranges(m, code):
	arg_start = code.find('(', m.extent.start.offset)
	arg_end = code.find(')', arg_start)
	if arg_start < 0 or arg_end < 0:
		return []
	args_code = code[arg_start + 1:arg_end].strip()
	if len(args_code) <= 0:
		return []
	ranges = []
	pos = arg_start
	while True:
		e = code.find(',', pos + 1)
		if e < 0 or arg_end < e:
			ranges.append((pos + 1, arg_end))
			return ranges
		else:
			ranges.append((pos + 1, e))
		pos = e

def has_same_arguments(m1, m2, code):
	# TODO:引数が同一か. todo: f(int x) <-> f(int) のような場合
	args1 = get_arg_ranges(m1, code)
	args2 = get_arg_ranges(m2, code)
	if len(args1) != len(args2):
		return False
	for i in range(0, len(args1)):
		a1 = args1[i]
		a2 = args2[i]
		tokens1 = code[a1[0]:a1[1]].replace('<', ' < ').replace('>', ' > ').split()
		tokens2 = code[a2[0]:a2[1]].split()
		for j in range(1, min(len(tokens1), len(tokens2))):
			if tokens1[-j - 1] != tokens2[-j - 1]:
				return False
	return True
	
def is_same_method(m1, m2, check_class, code):
	if m1.kind != m2.kind:
		return False;
	if m1.spelling != m2.spelling:
		return False;
	if check_class:
		if m1.semantic_parent != m2.semantic_parent:
			return False
	if has_same_arguments(m1, m2, code):
		return True
	return False
	
def gen_header_wrap_code(tu, klass, methods, code):
	parent = klass.semantic_parent
	if parent is None:
		return ("", -1)
		
	# 挿入箇所
	accessor = 'private:'
	insert_pos = -1
	parent_nodes = list(parent.get_children())
	for n in parent_nodes:
		if n.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
			if accessor == 'public:' or accessor == 'protected:':
				insert_pos = n.extent.start.offset
				break
			accessor = code[n.extent.start.offset:n.extent.end.offset].strip()
	if insert_pos < 0:
		insert_pos = code.rfind('};', parent.extent.end.offset)

	insert_methods = [m for m in methods if m.spelling != 'SetParent']

	# メソッド宣言がすでにある場合は省く
	for n in parent_nodes:
		if n.kind in method_kinds:
			if n.kind == CursorKind.CONSTRUCTOR or n.kind == CursorKind.DESTRUCTOR:
				for m in methods:
					if m.kind == n.kind and has_same_arguments(m, n, code):
						insert_methods.remove(m)
						break
			else:
				for m in methods:
					if is_same_method(m, n, False, code):
						insert_methods.remove(m)
						break

	class_name = parent.spelling
	# 挿入文字列
	text = ""
	for m in insert_methods:
		start = m.extent.start.offset
		end = m.extent.end.offset
		children = list(m.get_children())

		for c in children:
			if c.kind == CursorKind.COMPOUND_STMT:
				end = c.extent.start.offset
				break

		add = '\t' + code[start:end].strip() + ';\n'
		if m.kind == CursorKind.CONSTRUCTOR or m.kind == CursorKind.DESTRUCTOR:
			p = add[:add.rfind('(')].rfind('Impl')
			add = add[:p] + class_name + add[p + len('Impl'):]
		text += add

	return (text, insert_pos);

def get_ret_info(m, code):
	pos1 = code.find('(', m.extent.start.offset)
	if pos1 < 0:
		return ()
	pos2 = code.find(')', pos1)
	if pos2 < 0:
		return ()
	ret_name_tokens = code[m.extent.start.offset:pos1].split()
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
	return ret_info

def gen_cpp_wrap_code(tu, klass, methods, code):
	insert_pos = len(code)
	parent = klass.semantic_parent
	nodes = list(tu.cursor.get_children())
	insert_methods = [m for m in methods if m.spelling != 'SetParent']
	for n in nodes:
		if n.kind in method_kinds and n.semantic_parent == parent:
			if n.kind == CursorKind.CONSTRUCTOR or n.kind == CursorKind.DESTRUCTOR:
				for m in methods:
					if m.kind == n.kind and has_same_arguments(m, n, code):
						insert_methods.remove(m)
						break
			else:
				for m in methods:
					if is_same_method(m, n, False, code):
						insert_methods.remove(m)
						break
	class_name = parent.spelling
	new_code = ""
	for m in insert_methods:
		arg_ranges = get_arg_ranges(m, code)
		arg_type_names_code = ', '.join(get_arg_type_names(arg_ranges, code))
		arg_names_code = ', '.join(get_arg_names(arg_ranges, code))
		if m.kind == CursorKind.CONSTRUCTOR:
			new_code += '\n' + class_name + '::' + class_name + '(' + arg_type_names_code + ')\n'
			new_code += '{\n'
			new_code += '	pImpl = new ' + class_name + '::Impl(' + arg_names_code + ');\n'
			new_code += '	pImpl->SetParent(this);\n'
			new_code += '}\n'
		elif m.kind == CursorKind.DESTRUCTOR:
			new_code += '\n' + class_name + '::~' + class_name + '(' + arg_type_names_code + ')\n'
			new_code += '{\n'
			new_code += '	if (pImpl != nullptr)\n'
			new_code += '		delete pImpl;\n'
			new_code += '	pImpl = nullptr;\n'
			new_code += '}\n'
		else:
			ret_info = get_ret_info(m, code)
			if ret_info is not None:
				new_code += '\n' + ret_info[0] + ' ' + ret_info[1] + ' ' + class_name + '::' + m.spelling + '(' + arg_type_names_code + ') ' + ret_info[2] + '\n'
				new_code += '{\n'
				if ret_info[1] == 'void':
					new_code += '	pImpl->' + m.spelling + '(' + arg_names_code +');\n'
				else:
					new_code += '	return pImpl->' + m.spelling + '(' + arg_names_code +');\n'
				new_code += '}'
	return (new_code, insert_pos)

def from_selection(header, cpp, sel_start, sel_end):
	out_header = header
	out_cpp = cpp
	name = '__dummy__.cpp'
	index = Index.create()
	cpp = header + '\n' + cpp
	cpp_tu = index.parse(name, unsaved_files = [(name, cpp)])
	# 下だとなぜかうまくいかない
	#	cpp_tu = index.parse("./dummy.cpp", unsaved_files = [("./dummy.cpp", cpp), ("./dummy.h", header)])
	sel_start += len(header + '\n')
	sel_end += len(header + '\n')
	tu_nodes = list(cpp_tu.cursor.get_children())
	klass = get_impl_class_cursor(tu_nodes)
	methods = get_public_methods(klass, cpp)
	selecting_methods = [m for m in methods if m.extent.start.offset < sel_end and sel_start < m.extent.end.offset]
	(header_text, header_pos) = gen_header_wrap_code(cpp_tu, klass, selecting_methods, cpp)
	(cpp_text, cpp_pos) = gen_cpp_wrap_code(cpp_tu, klass, selecting_methods, cpp)
	out_header = out_header[:header_pos] + header_text + out_header[header_pos:]
	cpp_pos -= len(header + '\n')
	out_cpp = out_cpp[:cpp_pos] + cpp_text + out_cpp[cpp_pos:]
	return (out_header, out_cpp)

# for debug
def print_nodes(nodes, depth):
	for n in nodes:
		if isinstance(n.lexical_parent, type(None)):
			print ('-' * depth) + str((n.kind, n.spelling, n.displayname, n.extent.start.offset, n.extent.end.offset))
		else:
			print ('-' * depth) + str((n.kind, n.lexical_parent.displayname, n.semantic_parent.displayname, n.spelling, n.displayname, n.extent.start.offset, n.extent.end.offset))
		print_nodes(list(n.get_children()), depth + 1)

if len(sys.argv) == 5:	
	f = open(sys.argv[1])
	header = f.read() 
	f.close()

	f = open(sys.argv[2])
	cpp = f.read() 
	f.close()

	sel_start = int(sys.argv[3])
	sel_end = int(sys.argv[4])
	res = from_selection(header, cpp, sel_start, sel_end)

	print '*' * 40
	print res[0]
	print '*' * 40
	print res[1]
	print '*' * 40