#pragma once

class SampleClass
{
public:
	SampleClass();
	~SampleClass();
	template <typename X>
	X g(X x) const;
private:
	class Impl;
	Impl* pImpl;
};