// Guids.cs
// MUST match guids.h
using System;

namespace Company.pImplHelper
{
    static class GuidList
    {
        public const string guidpImplHelperPkgString = "bba77246-ea50-4caa-bb2e-21f5507584e6";
        public const string guidpImplHelperCmdSetString = "f74f94a7-0f1a-41d1-9f92-57238847ef2d";
        public const string guidToolWindowPersistanceString = "3a5128f2-7c7d-4eb9-bcb3-df504dfe0849";
        public static readonly Guid guidpImplHelperCmdSet = new Guid(guidpImplHelperCmdSetString);
    };
}