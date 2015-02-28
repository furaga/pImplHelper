[[[ <%ClassName%>.h ]]]
#pragma once

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
[[[ <%ClassName%>.cpp ]]]
#include "<%ClassName%>.h"

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
		printf("create <%ClassName%>\n");
	}
	~Impl()
	{
		printf("delete <%ClassName%>\n");
	}
	void SetParent(<%ClassName%>* p)
	{
		this->parent = p;
	}
	void f()
	{
		printf("<%ClassName%>::f()\n");
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
<%ClassName%>::f()
{
	pImpl->f();
}
