#include "Hoge.h"
#include <stdio.h>
/*
How to use:
#include "Hoge.h"
int main()
{
	Hoge* inst = new Hoge();
	inst->f();
	delete inst;
	inst = nullptr;

	return 0;
}
*/



Hoge::Hoge()
{
	printf("createaa Hoge\n");
}
Hoge::~Hoge()
{
	printf("delete Hoge\n");
}
void Hoge::f()
{
	printf("Hoge::f()\n");
}
void Hoge::g()
{
	printf("Hoge::g()\n");
}

void Hoge::h(int x, int y)
{
	printf("Hoge::g()\n");
}

