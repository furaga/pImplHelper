#pragma once

class NewClass
{
public:
	NewClass();
	~NewClass();
	int F(int, int);
private:
	class Impl;
	Impl* pImpl;
};