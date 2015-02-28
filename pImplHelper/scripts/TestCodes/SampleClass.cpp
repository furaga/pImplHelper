#include "SampleClass.h"
#include <stdio.h>
/*
How to use:
#include "SampleClass.h"
int main()
{
	SampleClass* inst = new SampleClass();
	inst->f();
	delete inst;
	inst = nullptr;

	return 0;
}
*/

class SampleClass::Impl{
	friend SampleClass;
	SampleClass* parent;
public:
	Impl()
	{
		printf("create SampleClass\n");
	}
	~Impl()
	{
		printf("delete SampleClass\n");
	}
	void SetParent(SampleClass* p)
	{
		this->parent = p;
	}
	const void f(const  int x , int z)
	{
		printf("SampleClass::f()\n");
	}
	
	template <typename X>
	X g(X x) const
	{
		printf("SampleClass::g()\n");
	}
};

SampleClass::SampleClass()
{
	pImpl = new SampleClass::Impl();
	pImpl->SetParent(this);
}
SampleClass::~SampleClass()
{
	if (pImpl != nullptr)
		delete pImpl;
	pImpl = nullptr;
}
void SampleClass::f(int a, int b)
{
	pImpl->f(a, b);
}