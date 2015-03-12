# coding: UTF-8
import gc
import sys
import traceback
import wrap_method
from clang.cindex import Index, File, Cursor, SourceRange, SourceLocation
from clang.cindex import CursorKind
from clang.cindex import TranslationUnit
from clang.cindex import TypeKind


method_kinds = {
	CursorKind.CONSTRUCTOR, 
	CursorKind.DESTRUCTOR, 
	CursorKind.CXX_METHOD,
	CursorKind.FUNCTION_DECL,
	CursorKind.FUNCTION_TEMPLATE,
	CursorKind.CONVERSION_FUNCTION, 
}


# headerファイル内で一番後ろのクラス定義
def get_class_cursor(nodes, header_length):
	ans = None
	for n in nodes:
		if n.extent.start.offset >= header_length:
			break
		if n.kind == CursorKind.CLASS_DECL:
			ans = n
	return ans

def get_code(n, code):
	if n is None:
		return ''
	return code[n.extent.start.offset:n.extent.end.offset]

def get_accessor_type(n, code, default):
	if n is None:
		acc_type = default
	else:
		acc_type = get_code(n, code).strip()
	return acc_type

def get_between_code(n1, n2, code, default_start, default_end):
	start = default_start
	end = default_end
	if n1 is not None:
		start = n1.extent.end.offset
	if n2 is not None:
		end = n2.extent.start.offset
	ans = code[start:end]
	return ans

def get_private_field_ranges(klass, code):
	nodes = list(klass.get_children())
	if len(nodes) <= 0:
		return ''

	start_node = nodes[0]
	start_idx = start_node.extent.start.offset

	end_node = nodes[-1]
	end_idx = code.find('}', end_node.extent.end.offset)

	pri_field_ranges = []
	prev_accessor = None
	for n in nodes:
		if n.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
			prev_accessor = n
		elif n.kind not in method_kinds:
			if get_accessor_type(prev_accessor, code, 'private:') == 'private:':
				pri_field_ranges.append((n.extent.start.offset, n.extent.end.offset))
	return pri_field_ranges

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


def get_method_accessors(klass, code):
	methods = []
	accessor = 'private:'
	for n in list(klass.get_children()):
		if n.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
			accessor = code[n.extent.start.offset:n.extent.end.offset].strip()
		if n.kind in method_kinds:
			methods.append((n, accessor))
	return methods

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

def convert(header, cpp):
	outheader = header
	outcpp = cpp

	# parse
	name = '__dummy__.cpp'
	code = header + '\n' + cpp
	index = Index.create()
	tu = index.parse(name, unsaved_files = [(name, code)])

	tu_nodes = list(tu.cursor.get_children())
	klass = get_class_cursor(tu_nodes, len(header))

	private_field = "";
	protected_field = "";
	public_field = "";


	impl_code = """
class <%ClassName%>::Impl{
	friend <%ClassName%>;
	<%ClassName%>* parent;
private:
	<%PrivateField%>
protected:
	<%ProtectedField%>
public:
	<%PublicField%>
	void SetParent(<%ClassName%>* p)
	{
		this->parent = p;
	}
};"""

	impl_code = impl_code.replace('<%ClassName%>', klass.spelling.strip())

	
	remove_ranges = []

	#
	# privateフィールドを::Implクラスにコピペ
	#
	pri_ranges = get_private_field_ranges(klass, code)
	for r in remove_ranges:
		remove_ranges.append(r)
	for r in pri_ranges:
		private_field += code[r[0]:r[1]].strip() + ';\n'

	
	#
	# public, protectedフィールドは変数・関数宣言はそのまま。関数定義は::Implにコピペして、元々のコード片は宣言で置き換える
	#

	method_accessors = get_method_accessors(klass, code)

	for (m, _) in method_accessors:
		remove_ranges.append((m.extent.start.offset, m.extent.end.offset))

	m2i_ls = [(m, m.extent.start.offset) for (m, _) in method_accessors]
	m2i = {}
	for tpl in m2i_ls:
		m2i[str(tpl[0])] = tpl[1]

	public_field_snips = {}
	protected_field_snips = {}
	private_field_snips = {}

	# クラス内に直接定義が書かれていない関数
	undef_methods = []

	for (m, acc) in method_accessors:
		s = m.extent.start.offset
		e = m.extent.end.offset
		method_code = code[s:e]

		if m.kind == CursorKind.CONSTRUCTOR or m.kind == CursorKind.DESTRUCTOR:
			_e = method_code.rfind('(')
			_s = method_code[:_e].rfind(klass.spelling)
			method_code = method_code[:_s] + 'Impl' + method_code[_e:]

		if acc == 'public:':
			public_field_snips[str(m)] = method_code.strip()
		elif acc == 'protected:':
			protected_field_snips[str(m)] = method_code.strip()
		else:
			private_field_snips[str(m)] = method_code.strip()

		ls = [n for n in list(m.get_children()) if n.kind == CursorKind.COMPOUND_STMT]
		if not ls: # is empty
			undef_methods.append((m, acc))

	# 各関数について、定義がクラス外にある場合は、それを::Implにコピペ
	# private関数ならもとのコードは削除、さもなくばwrapコードを生成

	global_methods = [n for n in tu_nodes if n.kind in method_kinds]
	for (m, acc) in undef_methods:
		for n in global_methods:
			if is_same_method(m, n, True, code):
				_def = [_n for _n in list(n.get_children()) if _n.kind == CursorKind.COMPOUND_STMT]
				if _def:
					def_code = get_code(_def[0], code).replace('\n', '\n\t')
					if acc == 'public:':
						public_field_snips[str(m)] = public_field_snips[str(m)] + def_code
					if acc == 'protected:':
						protected_field_snips[str(m)] = protected_field_snips[str(m)] + def_code
					if acc == 'private:':
						private_field_snips[str(m)] = private_field_snips[str(m)] + def_code
					remove_ranges.append((n.extent.start.offset, n.extent.end.offset))

	for snip in sorted(public_field_snips.items(), key=lambda x: m2i[x[0]]):
		public_field += '\t' + snip[1].strip() + '\n'
	for snip in sorted(protected_field_snips.items(), key=lambda x: m2i[x[0]]):
		protected_field += '\t' + snip[1].strip() + '\n'
	for snip in sorted(private_field_snips.items(), key=lambda x: m2i[x[0]]):
		private_field += '\t' + snip[1].strip() + '\n'

	impl_code = impl_code.replace('<%PrivateField%>', private_field.strip())
	impl_code = impl_code.replace('<%ProtectedField%>', protected_field.strip())
	impl_code = impl_code.replace('<%PublicField%>', public_field.strip())
	impl_code = impl_code.strip();


	# todo: ::Implからprivate関数のかぶりを消す
	# todo: headerのクラス定義から実装を削除
	# tood: グローバル関数からクラス関数の定義を削除

	for r in sorted(remove_ranges, key = lambda _r: -_r[0]):
		if r[0] < len(header):
			outheader = outheader[:r[0]] + outheader[r[1]:]
		else:
			outcpp = outcpp[:r[0] - len(header) - 1] + outcpp[r[1] - len(header) - 1:]

	_outheader = ""
	for line in outheader.split('\n'):
		if len(line.strip()) <= 0 or line.strip() == ';':
			continue
		_outheader += line + '\n'
	outheader = _outheader
	_p = outheader.find('{') + 1
	outheader = outheader[:_p] + """
	class Impl;
	std::unique_ptr<Impl> pImpl;""" + outheader[_p:]
	
	outcpp = outcpp.strip() + '\n'
	p = outcpp.rfind('#include ')
	p = outcpp.find('\n', p) + 1
	outcpp = outcpp[:p] + '\n' + impl_code + outcpp[p:]

	print '-' * 40
	print outheader
	print '=' * 40
	print outcpp
	print '=' * 40

	res = wrap_method.from_selection(outheader, outcpp, 0, len(outcpp))
#	print '-' * 40
#	print impl_code
	print '-' * 40
	print res[0]
	print '=' * 40
	print res[1]
	print '=' * 40
#	print [n[0].spelling for n in undef_methods]

	return (outheader, outcpp)