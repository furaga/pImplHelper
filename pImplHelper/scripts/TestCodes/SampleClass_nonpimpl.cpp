#include "SampleClass.h"
#include <stdio.h>

SampleClass::SampleClass()
{
	printf("create SampleClass\n");
}
SampleClass::~SampleClass()
{
	printf("delete SampleClass\n");
}
void SampleClass::f(int a, int b)
{
	printf("SampleClass::f()\n");
}
template <typename X>
X SampleClass::g(X x)
{
	printf("SampleClass::g()\n");
}
