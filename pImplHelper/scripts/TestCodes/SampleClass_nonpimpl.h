#pragma once

class SampleClass
{
	int a;
public:
	SampleClass();
	~SampleClass();
	template <typename X >
	X g(X x) const;
	float h(float a, float b)
	{
		return a * b;
	}

protected:
	int ff() {
		return 3;
	}
private:
	int fib() {
		return 0;
	}
	int fib2();
};

int SampleClass::fib2()
{
	return 1;
}