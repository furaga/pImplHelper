# coding: UTF-8
import sys
import util
from clang.cindex import CursorKind

#################################################################
# ::Implクラス内のpublic関数を元クラスにバインド
#################################################################
	
# todo: アクセッサごとに挿入歌書を決める
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
			if accessor == 'public:':
				insert_pos = n.extent.start.offset
				break
			accessor = code[n.extent.start.offset:n.extent.end.offset].strip()
	if insert_pos < 0:
		insert_pos = code.rfind('};', parent.extent.end.offset)

	insert_methods = [m for m in methods if m.spelling != 'SetParent']

	# メソッド宣言がすでにある場合は省く
	for n in parent_nodes:
		if n.kind in util.method_kinds:
			if n.kind == CursorKind.CONSTRUCTOR or n.kind == CursorKind.DESTRUCTOR:
				for m in methods:
					if m.kind == n.kind and util.has_same_arguments(m, n, code):
						insert_methods.remove(m)
						break
			else:
				for m in methods:
					if util.is_same_method(m, n, False, code):
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

def gen_cpp_wrap_code(tu, klass, methods, code):
	insert_pos = len(code)
	parent = klass.semantic_parent
	nodes = list(tu.cursor.get_children())
	insert_methods = [m for m in methods if m.spelling != 'SetParent']
	for n in nodes:
		if n.kind in util.method_kinds and n.semantic_parent == parent:
			if n.kind == CursorKind.CONSTRUCTOR or n.kind == CursorKind.DESTRUCTOR:
				for m in methods:
					if m.kind == n.kind and util.has_same_arguments(m, n, code):
						insert_methods.remove(m)
						break
			else:
				for m in methods:
					if util.is_same_method(m, n, False, code):
						insert_methods.remove(m)
						break
	class_name = parent.spelling
	new_code = ""
	for m in insert_methods:
		arg_ranges = util.get_arg_ranges(m, code)
		arg_type_names_code = ', '.join(util.get_arg_type_names(arg_ranges, code))
		arg_names_code = ', '.join(util.get_arg_names(arg_ranges, code))
		if m.kind == CursorKind.CONSTRUCTOR:
			snip = util.constructor_def_template
			snip = snip.replace('<%ClassName%>', class_name)
			new_code += '\n' + snip.strip()
		elif m.kind == CursorKind.DESTRUCTOR:
			snip = util.destructor_def_template
			snip = snip.replace('<%ClassName%>', class_name)
			new_code += '\n' + snip.strip()
		else:
			ret_info = util.get_ret_info(m, code)
			if ret_info is not None:
				if ret_info[1] == 'void':
					snip = util.non_ret_method_template
				else:
					snip = util.ret_method_template
				snip = snip.replace('<%ClassName%>', class_name)
				snip = snip.replace('<%MethodName%>', m.spelling)
				snip = snip.replace('<%ArgTypeNames%>', arg_type_names_code)
				snip = snip.replace('<%ArgNames%>', arg_names_code)
				snip = snip.replace('<%Prefix%>', (ret_info[0] + ' ' + ret_info[1]).strip())
				snip = snip.replace('<%Suffix%>', ret_info[2])
				new_code += '\n' + snip.strip()
	return (new_code, insert_pos)

def from_selection(header, cpp, sel_start, sel_end):
	out_header = header
	out_cpp = cpp

	cpp = header + '\n' + cpp
	cpp_tu = util.parse(cpp)
	# 下だとなぜかうまくいかない
	#	cpp_tu = index.parse("./dummy.cpp", unsaved_files = [("./dummy.cpp", cpp), ("./dummy.h", header)])

	sel_start += len(header + '\n')
	sel_end += len(header + '\n')
	tu_nodes = list(cpp_tu.cursor.get_children())

	klass = util.get_impl_class_cursor(tu_nodes)
	methods = util.get_methods(klass, cpp, ['public:'])
	selecting_methods = [m for m in methods if m.extent.start.offset < sel_end and sel_start < m.extent.end.offset]
	(header_text, header_pos) = gen_header_wrap_code(cpp_tu, klass, selecting_methods, cpp)
	(cpp_text, cpp_pos) = gen_cpp_wrap_code(cpp_tu, klass, selecting_methods, cpp)
	out_header = out_header[:header_pos] + header_text + out_header[header_pos:]
	cpp_pos -= len(header + '\n')
	out_cpp = out_cpp[:cpp_pos] + cpp_text + out_cpp[cpp_pos:]
	return (out_header, out_cpp)


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