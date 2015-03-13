# coding: UTF-8
import gc
import sys
import util
import re
from clang.cindex import CursorKind

#
#
# TODO: "parent->(変数名)"を"this->(変数名)"で置き換える
#
#

def is_same_constructor_or_destructor(m, n, code):
    if n.kind in { CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR }:
        if n.kind == m.kind and util.has_same_arguments(m, n, code):
            return True
    return False

def convert(header, cpp):
    outheader = header
    outcpp = cpp

    if '::Impl' not in cpp:
        return (outheader, outcpp)

    # init
    code = header + '\n' + cpp

    remove_ranges = []

    # parse
    tu = util.parse(code)
    tu_nodes = list(tu.cursor.get_children())
    tu_method_accessors = util.get_method_accessors(tu.cursor, code)

    klass =  util.get_impl_class_cursor(tu_nodes)
    klass_nodes = list(klass.get_children())    
    klass_method_accessors = util.get_method_accessors(klass, code)

    parent = klass.semantic_parent
    parent_nodes = list(parent.get_children())
    parent_method_accessors = util.get_method_accessors(parent, code)

    # 元クラスだけにある変数・関数宣言を探す
    to_add = []
    accessor = 'private:'
    for n1 in parent_nodes:
        if n1.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
            accessor = util.get_code(n1, code)
        elif n1.kind in { CursorKind.CONSTRUCTOR, CursorKind.DESTRUCTOR }:
            pass
        elif n1.kind in util.method_kinds:
            found_same_node = [n for n in klass_nodes if util.is_same_method(n, n1, False, code)]
            if not found_same_node:
                to_add.append((n1, accessor))
        else:
            tokens1 = util.get_code(n1, code).split()
            found_same_node = [n for n in klass_nodes if util.get_code(n, code).split() == tokens1]
            if not found_same_node:
                to_add.append((n1, accessor))

    to_add = [n for n in to_add 
        if  util.get_code(n[0], code).split() != ['class', 'Impl']
        and util.get_code(n[0], code).split() != ['Impl*', 'pImpl']]

    # 元クラスだけにある変数・関数宣言をImplに追加
    add_text = ''
    to_add_pri = [n for n in to_add if n[1] == 'private:']
    if len(to_add_pri) >= 1:
        add_text = 'private:\n'
        for (n, acc) in to_add_pri:
            add_text += '    ' + util.get_code(n, code).strip() + ';\n'
    to_add_pro = [n for n in to_add if n[1] == 'protected:']
    if len(to_add_pro) >= 1:
        add_text += 'protected:\n'
        for (n, acc) in to_add_pro:
            add_text += '    ' + util.get_code(n, code).strip() + ';\n'
    to_add_pub = [n for n in to_add if n[1] == 'public:']
    if len(to_add_pub) >= 1:
        add_text += 'public:\n'
        for (n, acc) in to_add_pub:
            add_text += '    ' + util.get_code(n, code).strip() + ';\n'

    # Implの定義で元クラスの定義を置き換え
    new_klass_code = util.get_code(klass, code)
    new_klass_code = new_klass_code.replace('::Impl', '')
    new_klass_code = new_klass_code.replace('Impl', parent.spelling)
    new_klass_code = new_klass_code.replace('friend ' + parent.spelling + ';', '')
    new_klass_code = new_klass_code.replace(parent.spelling + '* parent;', '')

    s = new_klass_code.find('void SetParent(' + parent.spelling + '*')
    e = new_klass_code.find('}', s) + 1
    new_klass_code = new_klass_code[:s] + new_klass_code[e:]

    p = new_klass_code.rfind('}')
    new_klass_code = new_klass_code[:p] + add_text + new_klass_code[p:]

    # header, cppの書きかえ手順
    replace_list = []

    # グローバル領域の関数定義をImplで置き換える
    for n in tu_nodes:
        if n.kind in util.method_kinds:
            if n.semantic_parent == parent:
                # Implクラスに関数定義があればコピペする
                ls = [m for m in klass_nodes if util.is_same_method(m, n, False, code) or is_same_constructor_or_destructor(m, n, code)]
                if len(ls) <= 0:
                    continue
                m = ls[0]
                ls2 = [d for d in list(m.get_children()) if d.kind == CursorKind.COMPOUND_STMT]
                if len(ls2) <= 0:
                    continue
                md = ls2[0]
                ls3 = [d for d in list(n.get_children()) if d.kind == CursorKind.COMPOUND_STMT]
                if len(ls3) <= 0:
                    continue
                nd = ls3[0]
                new_klass_code = new_klass_code.replace(util.get_code(md, code), ';')
                replace_list.append((nd.extent.start.offset, nd.extent.end.offset, util.get_code(md, code).replace('\n\t', '\n').replace('\n    ', '\n')))

    # Implを消して元クラスの定義を置き換え
    replace_list.append((parent.extent.start.offset, parent.extent.end.offset, new_klass_code))
    replace_list.append((klass.extent.start.offset, klass.extent.end.offset + 1, ''))

    offset = -len(header) - 1
    for (_s, _e, _t) in sorted(replace_list, key = lambda (_s, _e, _t) : -_s):
        if _s < len(header):
            outheader = outheader[:_s] + _t + outheader[_e:]
        else:
            outcpp = outcpp[:_s + offset] + _t + outcpp[_e + offset:]

    outheader = re.sub(r'\s+;', ';', outheader)
    outcpp = re.sub(r'\s+;', ';', outcpp)
    outcpp = outcpp.replace(': pImpl(new Hoge::Impl())', '')

    return (outheader, outcpp)


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
