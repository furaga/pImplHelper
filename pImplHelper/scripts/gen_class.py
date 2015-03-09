# coding: UTF-8
import gc

#################################################################
# 新規pImplクラスの生成
#################################################################

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