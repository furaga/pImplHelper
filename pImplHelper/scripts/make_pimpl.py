# coding: UTF-8
import sys
import wrap_method
import util
from clang.cindex import CursorKind

#
#
# TODO: 元クラスのpublic変数を関数内で参照している場合、それを "parent->(変数名)"で置き換える
#
#

def get_field_ranges(klass, code, accessors):
    nodes = list(klass.get_children())
    if len(nodes) <= 0:
        return ''

    start_node = nodes[0]
    start_idx = start_node.extent.start.offset

    end_node = nodes[-1]
    end_idx = code.find('}', end_node.extent.end.offset)

    ranges = []
    prev_accessor = None
    for n in nodes:
        if n.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
            prev_accessor = n
        elif n.kind not in util.method_kinds:
            if util.get_accessor_type(prev_accessor, code, 'private:') in accessors:
                ranges.append((n.extent.start.offset, n.extent.end.offset))

    return ranges

def convert(header, cpp):
    outheader = header
    outcpp = cpp

    if '::Impl' in cpp:
        return (outheader, outcpp)

    # init
    code = header + '\n' + cpp

    remove_ranges = []

    private_field = "";
    protected_field = "";
    public_field = "";

    # parse
    tu = util.parse(code)
    tu_nodes = list(tu.cursor.get_children())
    klass =  util.get_class_cursor(tu_nodes, len(header))
    

    # private変数を::Implクラスにコピペ
    pri_ranges =  get_field_ranges(klass, code, ['private:'])
    # cut 
    for r in pri_ranges:
        remove_ranges.append(r)
    # paste
    for r in pri_ranges:
        private_field += code[r[0]:r[1]].strip() + ';\n'

    # private, protected, public関数を::Implにコピペ
    method_accessors = util.get_method_accessors(klass, code)

    # cut
    for (m, _) in method_accessors:
        remove_ranges.append((m.extent.start.offset, m.extent.end.offset))

    # method -> position in code
    m2i = {}
    for (m, _) in method_accessors:
        m2i[str(m)] = m.extent.start.offset

    # distribute methods
    public_field_snips = {}
    protected_field_snips = {}
    private_field_snips = {}

    for (m, acc) in method_accessors:
        method_code = code[m.extent.start.offset:m.extent.end.offset]

        # rename if m is constructor/destructor
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

    # find undefined methods
    undef_methods = []
    for (m, acc) in method_accessors:
        if not [n for n in list(m.get_children()) if n.kind == CursorKind.COMPOUND_STMT]:
            undef_methods.append((m, acc))

    # undef_methodsについて、クラス定義の外で関数が実装されている場合、それを::Implへコピペ
    global_methods = [n for n in tu_nodes if n.kind in util.method_kinds]
    for (m, acc) in undef_methods:
        for n in global_methods:
            if not util.is_same_method(m, n, True, code):
                continue

            _def = [_n for _n in list(n.get_children()) if _n.kind == CursorKind.COMPOUND_STMT]
            if not _def:
                continue

            def_code =  util.get_code(_def[0], code).replace('\n', '\n    ')
            if acc == 'public:':
                public_field_snips[str(m)] += def_code
            elif acc == 'protected:':
                protected_field_snips[str(m)] += def_code
            else:
                private_field_snips[str(m)] += def_code

            # 元のコードは削除
            remove_ranges.append((n.extent.start.offset, n.extent.end.offset))

    compare = lambda x: m2i[x[0]]
    for snip in sorted(public_field_snips.items(), key = compare):
        public_field += '    ' + snip[1].strip() + '\n'
    for snip in sorted(protected_field_snips.items(), key = compare):
        protected_field += '    ' + snip[1].strip() + '\n'
    for snip in sorted(private_field_snips.items(), key = compare):
        private_field += '    ' + snip[1].strip() + '\n'

    # implのコードを生成
    impl_code =  util.cpp_impl_template.replace('<%ClassName%>', klass.spelling.strip())
    impl_code = impl_code.replace('<%PrivateField%>', private_field.strip())
    impl_code = impl_code.replace('<%ProtectedField%>', protected_field.strip())
    impl_code = impl_code.replace('<%PublicField%>', public_field.strip())
    impl_code = impl_code.strip();

    # header, cppからimplにコピペしたコードを削除する
    t_header = header
    t_cpp = cpp
    offset = - len(header) - 1
    for r in sorted(remove_ranges, key = lambda _r: -_r[0]):
        if r[0] < len(header):
            t_header = t_header[:r[0]] + t_header[r[1]:]
        else:
            t_cpp = t_cpp[:r[0] + offset] + t_cpp[r[1] + offset:]

    # 余分な行を消す
    t_header2 = ""
    for line in t_header.split('\n'):
        if len(line.strip()) >= 1 and line.strip() != ';':
            t_header2 += line + '\n'

    # Implのクラス・インスタンスの宣言
    _p = t_header2.find('#pragma once')
    if _p >= 0:
        _p = t_header2.find('\n', _p) + 1
        t_header2 = t_header2[:_p] + '#include <memory>\n' + t_header2[_p:]
    _p = t_header2.find('{') + 1
    t_header2 = t_header2[:_p] + """
    class Impl;
    std::unique_ptr<Impl> pImpl;""" + t_header2[_p:]


    comment_ranges = []
    _p = 0
    while _p < len(t_cpp):
        _s = t_cpp.find('/*', _p)
        if _s >= 0:
            _e = t_cpp.find('*/', _s)
            if _e < 0:
                _e = len(t_cpp)
            comment_ranges.append((_s, _e))
        else:
            break
        _p = _e

    # ::ImplをCPPファイルに書き出し
    t_cpp = t_cpp.strip() + '\n'
    p = len(t_cpp) - 1
    while p >= 0:
        p = t_cpp[:p].rfind('#include ')
        if p < 0:
            p = 0
            break
        if not [r for r in comment_ranges if r[0] <= p and p <= r[1]]:
            break

    p = t_cpp.find('\n', p + 1) + 1
    t_cpp = t_cpp[:p] + '\n' + impl_code + t_cpp[p:]

    res = wrap_method.from_selection(t_header2, t_cpp, 0, len(t_cpp))

    return (res[0], res[1])


if len(sys.argv) == 3:    
    f = open(sys.argv[1])
    header = f.read() 
    f.close()

    f = open(sys.argv[2])
    cpp = f.read() 
    f.close()

    res = convert(header, cpp)

    print '*' * 40
    print res[0]
    print '*' * 40
    print res[1]
    print '*' * 40