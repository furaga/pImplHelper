#include "NewClass245.h"
#include <stdio.h>
/*
How to use:
#include "NewClass245.h"
int main()
{
	NewClass245* inst = new NewClass245();
	inst->f();
	delete inst;
	inst = nullptr;

	return 0;
}
*/

class NewClass245::Impl{
	friend NewClass245;
	NewClass245* parent;
public:
	Impl()
	{
		printf("create NewClass245\n");
	}
	~Impl()
	{
		printf("delete NewClass245\n");
	}
	void SetParent(NewClass245* p)
	{
		this->parent = p;
	}
	void f()
	{
		printf("NewClass245::f()\n");
	}
private:
	void g()
	{
		printf("NewClass245::g()\n");
	}
public:
	void h()
	{
		printf("NewClass245::h()\n");
	}
};

NewClass245::NewClass245()
{
	pImpl = new NewClass245::Impl();
	pImpl->SetParent(this);
}
NewClass245::~NewClass245()
{
	if (pImpl != nullptr)
		delete pImpl;
	pImpl = nullptr;
}
void NewClass245::f()
{
	pImpl->f();
}