[[[ <%ClassName%>.h, <%PublicMethodList%> ]]]
	void <%MethodName%>(<%ArgmentsTypeName%>);

[[[ <%ClassName%>.cpp, <%PublicMethodList_Impl%> ]]]
	void <%MethodName%>(<%ArgmentsTypeName%>)
	{
		// write logic here
	}
[[[ <%ClassName%>.cpp, <%PublicMethodList_Bind%> ]]]
void <%ClassName%>::<%MethodName%>(<%ArgmentsTypeName%>) { pImpl-><%MethodName%>(<%ArgmentsName%>); }