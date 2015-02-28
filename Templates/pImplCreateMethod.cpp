[[[ <%ClassName%>.h, <%PublicMethodList%> ]]]
	<%ReturnType%> <%MethodName%>(<%ArgmentsTypeName%>);
[[[ <%ClassName%>.cpp, <%PublicMethodList_Impl%> ]]]
	<%ReturnType%> <%MethodName%>(<%ArgmentsTypeName%>)
	{
		// write logic here
		return (<%ReturnType%>)0;
	}
[[[ <%ClassName%>.cpp, <%PublicMethodList_Bind%> ]]]
<%ReturnType%> <%ClassName%>::<%MethodName%>(<%ArgmentsTypeName%>) { return pImpl-><%MethodName%>(<%ArgmentsName%>); }