#include "NewClass.h"
#define USE_FACT2

class NewClass::Impl{
	friend NewClass;
	NewClass* parent;
public:
	Impl()
	{
		printf("NewClass()");
	}
	~Impl()
	{
		printf("~NewClass()");
	}
	void SetParent(NewClass* p)
	{
		this->parent = p;
	}
	int fact3 = 1;
	int F(int a, int b)
	{
#ifdef USE_FACT2
		return fact * (A(a) + B(b));
#else
		return fact2 * (A(a) + B(b));
#endif
	}
	
	int g(float x, float y)
	{
		return x * y;
	}
protected:
	int A(int a)
	{
		if (a <= 1)
			return 1;
		return a * A(a -1);
	}
	long fact = 50;
private:
	int B(int x)
	{
		if (x <= 1)
			return 1;
		return x * B(x -1);
	}
	long fact2 = 10;
};

NewClass::NewClass()
{
	pImpl = new NewClass::Impl();
	pImpl->SetParent(this);
}
NewClass::~NewClass()
{
	if (pImpl != nullptr)
		delete pImpl;
	pImpl = nullptr;
}
int NewClass::F(int x, int y)
{
	pImpl->F(x, y);
}