#include "NewClass.h"
#define USE_FACT2

NewClass::NewClass()
{
	printf("NewClass()");
}
NewClass::~NewClass()
{
	printf("~NewClass()");
}
int NewClass::F(int a, int b)
{
#ifdef USE_FACT2
		return fact * (A(a) + B(b));
#else
		return fact2 * (A(a) + B(b));
#endif
}
int NewClass::A(int a)
{
	if (a <= 1)
		return 1;
	return a * A(a -1);
}
int NewClass::B(int x)
{
	if (x <= 1)
		return 1;
	return x * B(x -1);
}
