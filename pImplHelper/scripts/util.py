# coding: UTF-8
from clang.cindex import Index, CursorKind

############################################################################
#
# コードのテンプレート
#
############################################################################

header_name_template = """<%ClassName%>.h"""

header_impl_dclr = """
    class Impl;
    std::unique_ptr<Impl> pImpl;"""

header_code_template = """#pragma once
#include <memory>

class <%ClassName%>
{
public:
    <%ClassName%>();
    ~<%ClassName%>();
    void f();
private:""" + header_impl_dclr + """
};
"""

constructor_def_template = """<%ClassName%>::<%ClassName%>()
    : pImpl(new <%ClassName%>::Impl())
{
    pImpl->SetParent(this);
}"""
destructor_def_template = """<%ClassName%>::~<%ClassName%>()
{
}"""

ret_method_template = """<%Prefix%> <%ClassName%>::<%MethodName%>(<%ArgTypeNames%>) <%Suffix%>
{
    return pImpl-><%MethodName%>(<%ArgNames%>);
}"""

non_ret_method_template = """<%Prefix%> <%ClassName%>::<%MethodName%>(<%ArgTypeNames%>) <%Suffix%>
{
    pImpl-><%MethodName%>(<%ArgNames%>);
}"""

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

""" + constructor_def_template + """
""" + destructor_def_template + """
void <%ClassName%>::f()
{
    pImpl->f();
}"""

cpp_impl_template = """
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

############################################################################
#
# 
#
############################################################################


method_kinds = {
    CursorKind.CONSTRUCTOR, 
    CursorKind.DESTRUCTOR, 
    CursorKind.CXX_METHOD,
    CursorKind.FUNCTION_DECL,
    CursorKind.FUNCTION_TEMPLATE,
    CursorKind.CONVERSION_FUNCTION, 
}

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

# for debug
def print_nodes(nodes, depth):
    for n in nodes:
        if isinstance(n.lexical_parent, type(None)):
            print ('-' * depth) + str((n.kind, n.spelling, n.displayname, n.extent.start.offset, n.extent.end.offset))
        else:
            print ('-' * depth) + str((n.kind, n.lexical_parent.displayname, n.semantic_parent.displayname, n.spelling, n.displayname, n.extent.start.offset, n.extent.end.offset))
        print_nodes(list(n.get_children()), depth + 1)

# headerファイル内で一番後ろのクラス定義
def get_class_cursor(nodes, header_length):
    ans = None
    for n in nodes:
        if n.extent.start.offset >= header_length:
            break
        if n.kind == CursorKind.CLASS_DECL:
            ans = n
    return ans

def get_impl_class_cursor(nodes):
    for n in nodes:
        if n.kind == CursorKind.CLASS_DECL and n.displayname == 'Impl':
            return n
    return None

def get_code(n, code):
    if n is None:
        return ''
    return code[n.extent.start.offset:n.extent.end.offset]

def get_between_code(n1, n2, code, default_start, default_end):
    start = default_start
    end = default_end
    if n1 is not None:
        start = n1.extent.end.offset
    if n2 is not None:
        end = n2.extent.start.offset
    ans = code[start:end]
    return ans

def get_accessor_type(n, code, default):
    if n is None:
        acc_type = default
    else:
        acc_type = get_code(n, code).strip()
    return acc_type

def get_methods(klass, code, accessors):
    methods = []
    accessor = 'private:'
    for n in list(klass.get_children()):
        if n.kind == CursorKind.CXX_ACCESS_SPEC_DECL:
            accessor = code[n.extent.start.offset:n.extent.end.offset].strip()
        elif accessor in accessors:
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

def parse(code):
    name = '__dummy__.cpp'
    index = Index.create()
    tu = index.parse(name, unsaved_files = [(name, code)])
    return tu
