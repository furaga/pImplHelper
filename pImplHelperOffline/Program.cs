using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using IronPython.Hosting;
using Microsoft.Scripting.Hosting;

namespace pImplHelperOffline
{
    // 実験用のプロジェクト
    class Program
    {
        class CodeTemplate
        {
            public string className;
            public string filename;
            public string code;
            public CodeTemplate(string className, string filename, string code)
            {
                this.className = className;
                this.filename = filename;
                this.code = code;
            }
        }

        static void Main(string[] args)
        {
            var templates = CreatePImplTemplates("SampleClass");
            CreateMethod(templates, "SampleClass", "f", "int", new List<string>() { "int", "float" }, new List<string>() { "e", "a" });
            CreateMethodVoid(templates, "SampleClass", "g", new List<string>() { "SampleClass" }, new List<string>() { "he" });
            CreateMethod(templates, "SampleClass", "h", "int",
                new List<string>() { "bool", "float", "float", "float" },
                new List<string>() { "transform", "x", "y", "z" });

            string output = "";
            foreach (var t in templates)
                output += "[" + t.className + ":" + t.filename + "]\n" + t.code + "\n";


//            var python = Python.CreateEngine();
//            dynamic makePImplScript = python.ExecuteFile("MakePImpl.py");
            string header = System.IO.File.ReadAllText("../../../TestCodes/NewClass.h");
            string cpp = System.IO.File.ReadAllText("../../../TestCodes/NewClass.cpp");
//            dynamic makeNonPImplScript = python.ExecuteFile("MakeNonPImpl.py");
//            makePImplScript.MakePImpl(headerCode, cppCode);
            
            string outheader, outcpp;
            //MakeNonPImpl(header, cpp, out outheader, out outcpp);

            string outheader2, outcpp2;
            int methodStart_, methodEnd_;
            int methodStart, methodEnd;
            //System.Diagnostics.Debug.Assert(IsPointPublicField(cpp, cpp.IndexOf("return x * y;")) == true);
            //System.Diagnostics.Debug.Assert(IsPointPublicField(cpp, cpp.IndexOf("int A(int a);")) == false);
            //System.Diagnostics.Debug.Assert(IsPointPublicField(cpp, cpp.IndexOf("rotected:")) == false);
            //System.Diagnostics.Debug.Assert(IsPointPublicField(cpp, cpp.IndexOf("ublic:")) == true);

            GetPImplMethodRange(cpp, cpp.IndexOf("return x * y;"), out methodStart_, out methodEnd_);
            GetPImplMethodRange_python(cpp, cpp.IndexOf("return x * y;"), out methodStart, out methodEnd);
            //BindPImplMethod(header, cpp, methodStart, methodEnd, out outheader2, out outcpp2);
            
            BindPImplMethod_python(header, cpp, methodStart, methodEnd, out outheader2, out outcpp2);

            System.IO.File.WriteAllText("output.cpp", output);
            System.Console.WriteLine(output);


            Console.Read();
        }

        static bool BindPImplMethod_python(string header, string cpp, int methodStart, int methodEnd, out string outheader, out string outcpp)
        {
            var python = Python.CreateEngine();
            dynamic global = python.ExecuteFile("MakePImpl.py");
            var header_cpp = global.bind_pimpl_method(header, cpp, methodStart, methodEnd);
            outheader = header_cpp[0];
            outcpp = header_cpp[1];
            Console.WriteLine(outheader);
            Console.WriteLine("---------");
            Console.WriteLine(outcpp);
            return true;
        }

        static bool GetPImplMethodRange_python(string cpp, int cursor, out int methodStart, out int methodEnd)
        {
            var python = Python.CreateEngine();
            dynamic global = python.ExecuteFile("MakePImpl.py");
            var range = global.get_focused_method_range(cpp, cursor);
            methodStart = range[0];
            methodEnd = range[1];
            Console.WriteLine(methodStart + ", " + methodEnd);
            return true;
        }

        static bool IsPointPublicField(string cpp, int cursor)
        {
            int classStart;
            int classEnd;
            int classDefStart;
            int classDefEnd;
            string className;
            bool res = FindImplClass(ref cpp, out classStart, out classEnd, out classDefStart, out classDefEnd, out className);
            if (!res)
                return false;

            if (classDefStart < cursor && cursor < classDefEnd)
            {
                int idx = 0;
                string curacc = "private";
                while (true)
                {
                    string acctype;
                    int nextidx = NextAccessor(ref cpp, idx, cpp.Length, out acctype);
                    if (nextidx >= cpp.Length)
                    {
                        break;
                    }
                    if (idx <= cursor && cursor <= nextidx)
                    {
                        if (curacc == "public")
                            return true;
                        else
                            return false;
                    }
                    idx = nextidx + 1;
                    curacc = acctype;
                }
            }

            return false;
        }

        static bool GetPImplMethodRange(string cpp, int cursor, out int methodStart, out int methodEnd)
        {
            methodStart = methodEnd = -1;

            int classStart;
            int classEnd;
            int classDefStart;
            int classDefEnd;
            string className;
            bool res = FindImplClass(ref cpp, out classStart, out classEnd, out classDefStart, out classDefEnd, out className);
            if (!res)
                return false;

            int idx = classDefStart + 1;
            while (true)
            {
                int _s, _e;
                res = FindNest(ref cpp, idx, "{", "}", out _s, out _e);
                if (!res)
                    return false;

                int startIdx = cpp.LastIndexOfAny(new[] { ':', ';', '}', '{' }, _s - 1) + 1;
                if (startIdx <= cursor && cursor <= _e)
                {
                    methodStart = startIdx;
                    methodEnd = _e;
                    return true;
                }
                
                idx = _e + 1;
                if (idx > cursor)
                    break;
            }

            return false;
        }

        static bool BindPImplMethod(string header, string cpp, int methodStart, int methodEnd, out string outheader, out string outcpp)
        {
            string orgHeader = header;
            string orgcpp = cpp;
            outheader = header;
            outcpp = cpp;

            // headerにmethodの宣言を追加

            int startBrace = cpp.IndexOf("{", methodStart);
            string methodDecl = "\t" + orgcpp.Substring(methodStart, startBrace - methodStart).Trim() + ";\n";

            int publicStart = -1, publicEnd = -1;
            int idx = 0;
            while (publicStart < 0 || publicEnd < 0)
            {
                string acctype;
                idx = NextAccessor(ref outheader, idx, outheader.Length, out acctype);
                if (idx >= outheader.Length)
                {
                    break;
                }

                if (publicStart < 0)
                {
                    if (acctype == "public")
                    {
                        publicStart = idx;
                    }
                }
                else
                {
                    publicEnd = idx;
                }
                idx++;
            }

            if (publicStart < 0)
                methodDecl = "public:\n" + methodDecl;

            if (publicEnd < 0)
                publicEnd = outheader.Length;

            outheader = outheader.Insert(publicEnd, methodDecl);


            // cppにmethodのbind関数を作る
            string _snip = outcpp.Substring(methodStart, methodEnd - methodStart).Trim();
            List<string> types = new List<string>();

            int classImplStart = cpp.IndexOf("::Impl");
            if (classImplStart < 0)
                return false;
            string className = cpp.Substring(cpp.IndexOf("class "), classImplStart - cpp.IndexOf("class ")).Split(' ').Where(t => !string.IsNullOrWhiteSpace(t)).Last();

            _snip = _snip.Replace("(", " (");
            _snip = _snip.Replace(")", ") ");
            var tokens = _snip.Split(' ').Where(t => !string.IsNullOrWhiteSpace(t)).Select(t => t.Trim()).ToList();

            bool constructor = false;
            bool destructor = false;
            for (int i = 0; i < tokens.Count - 1; i++)
            {
                if (tokens[i + 1].StartsWith("("))
                {
                    if (tokens[i] == "Impl")
                    {
                        constructor = true;
                        tokens[i] = className + "::" + className;
                    }
                    else if (tokens[i] == "~Impl")
                    {
                        destructor = true;
                        tokens[i] = className + "::~" + className;
                    }
                    else
                    {
                        tokens[i] = className + "::" + tokens[i];
                    }
                    break;
                }
            }

            string methodName;
            MethodNameTypes(ref _snip, out methodName, new List<string>());
            int _s, _e;
            FindNest(ref _snip, 0, "(", ")", out _s, out _e);
            string argCode = _snip.Substring(_s + 1, _e - _s - 2).Trim();
            var argNames = argCode.Split(',').Select(arg => arg.Split(' ').Last().Trim()).ToArray();

            string newSnip = "\n";
            for (int i = 0; i < tokens.Count; i++)
            {
                newSnip += " " + tokens[i];
                if (tokens[i].EndsWith(")"))
                    break;
            }

            if (constructor)
            {
                newSnip += string.Format(@"
{{
    pImpl-> = new {0}::Impl();
    pImpl->SetParent(this);
}}", className);
            }
            else if (destructor)
            {
                newSnip += string.Format(@"
{{
	if (pImpl != nullptr)
		delete pImpl;
	pImpl = nullptr;
}}");
            }
            else
            {
                newSnip += string.Format(@"
{{
    pImpl->{0}({1});
}}", methodName, string.Join(", ", argNames));
            }

            outcpp += newSnip;

            return true;
        }



        static string RemoveMethod(ref string code, string methodName, int start, int end)
        {
            int idx = code.IndexOf(methodName + "(", start);
            int startIdx = code.LastIndexOfAny(new[] { ':', ';', '}' }, idx) + 1;

            int nextIdx = code.IndexOfAny(new[] { ';', '{' }, idx);
            if (nextIdx < 0 || nextIdx >= end)
                return code;

            string removed;
            switch (code[nextIdx])
            {
                case ';':
                    removed = code.Remove(startIdx, nextIdx + 1 - startIdx);
                    break;
                default: // case '{':
                    int _start, _end;
                    bool res = FindNest(ref code, idx, "{", "}", out _start, out _end);
                    if (res == false || _end >= end)
                        return code;
                    removed = code.Remove(startIdx, _end + "}".Length - startIdx);
                    break;
            }

            return removed;
        }

        static bool RemoveUnuseCode(ref string header, ref string cpp)
        {
            // headerから::Implの宣言を消す
            string[] unuses_h = new string[] { "class Impl;", "Impl* pImpl;" };
            foreach (var unuse in unuses_h)
            {
                int start = header.IndexOf(unuse);
                if (start >= 0)
                    header = header.Remove(start, unuse.Length);
            }
            // cppから::Impl特有のコードを消す
            string[] unuses_cpp = new string[] { "friend NewClass;", "NewClass* parent;" };
            foreach (var unuse in unuses_cpp)
            {
                int start = cpp.IndexOf(unuse);
                if (start >= 0)
                   cpp = cpp.Remove(start, unuse.Length);
            }
            cpp = RemoveMethod(ref cpp, "SetParent", 0, cpp.Length);
            return true;
        }


        static bool MakeNonPImpl(string header, string cpp, out string outheader, out string outcpp)
        {
            string orgHeader = header;
            string orgcpp = cpp;
            outheader = header;
            outcpp = cpp;

            // cppをいじる Implのpublic関数の定義をcpp内の元関数と置換する
            // Implのprivate, protectedをheaderにうつす


            bool res = RemoveUnuseCode(ref outheader, ref outcpp);
            if (!res)
                return false;

            int classStart;
            int classEnd;
            int classDefStart;
            int classDefEnd;
            string className;
            res = FindImplClass(ref outcpp, out classStart, out classEnd, out classDefStart, out classDefEnd, out className);
            if (!res)
                return false;

            string publicSnippet;
            string privateSnippet;
            string protectedSnippet;
            GetClassDefSnippets(ref outcpp, classDefStart, classDefEnd, out publicSnippet, out privateSnippet, out protectedSnippet);

            // Implを削除してしまう
            outcpp = outcpp.Remove(classStart, classEnd - classStart + 1);

            // 
            List<string> methodVarsPublic = MethodVariableDefinitions(ref publicSnippet);
            List<string> methodVarsPrivate = MethodVariableDefinitions(ref privateSnippet);
            List<string> methodVarsProtected = MethodVariableDefinitions(ref protectedSnippet);
            List<string> varsPublic = new List<string>();
            List<string> vars = new List<string>();

            List<string> missed = new List<string>();

            string newHeaderSnippets = "public:\n";

            // publicの関数定義を置換する
            foreach (var snip in methodVarsPublic)
            {
                if (snip.EndsWith(";"))
                {
                    // 変数宣言
                    newHeaderSnippets += "    " + snip + "\n";
                }
                else
                {
                    string mname;
                    List<string> types = new List<string>();
                    var _snip = snip;
                    res = MethodNameTypes(ref _snip, out mname, types);
                    if (!res)
                    {
                        missed.Add(snip);
                        continue;
                    }
                    if (mname == "Impl")
                        mname = className;
                    if (mname == "~Impl")
                        mname = "~" + className;
                    int idx = outcpp.IndexOf(className + "::" + mname);
                    if (idx < 0)
                    {
                        missed.Add(snip);
                        continue;
                    }

                    int start = outcpp.IndexOf('(', idx);
                    int _s, _e;
                    res = FindNest(ref outcpp, idx, "{", "}", out _s, out _e);
                    if (start < 0 || res == false)
                    {
                        missed.Add(snip);
                        continue;
                    }

                    outcpp = outcpp.Remove(start, _e - start);
                    outcpp = outcpp.Insert(start, snip.Substring(snip.IndexOf('(')));

                }
            }


            // private/protectedの関数定義を追加する
            string newSnippets = "";
            foreach (var methodVars in new[] { methodVarsProtected, methodVarsPrivate })
            {
                if (methodVars == methodVarsProtected)
                {
                    newHeaderSnippets += "protected:\n";
                }
                else
                {
                    newHeaderSnippets += "private:\n";
                }

                foreach (var snip in methodVars)
                {
                    if (string.IsNullOrWhiteSpace(snip))
                        continue;

                    if (snip.EndsWith(";"))
                    {
                        // 変数宣言
                        newHeaderSnippets += "    " + snip + "\n";
                    }
                    else
                    {
                        // 関数宣言
                        newHeaderSnippets += "    " + snip.Substring(0, snip.IndexOf(')') + 1) + ";\n";

                        // 関数
                        var tokens = snip.Replace("(", " (").Split(' ').Where(t => !string.IsNullOrWhiteSpace(t)).ToArray();
                        for (int i = 0; i < tokens.Length - 1; i++)
                        {
                            if (tokens[i + 1].StartsWith("("))
                            {
                                tokens[i] = className + "::" + tokens[i].Trim();
                                break;
                            }
                        }
                        newSnippets += string.Join(" ", tokens) + "\n";
                    }
                }
            }

            outheader = outheader.Insert(outheader.IndexOf("};"), newHeaderSnippets);

            outcpp += newSnippets;

            return true;
        }

        static bool GetClassDefSnippets(ref string cpp, int classDefStart, int classDefEnd, out string publicSnippet, out string privateSnippet, out string protectedSnippet)
        {
            // '{', '}'は含めない
            classDefStart++;
            classDefEnd--;

            // public, private, protected のクラス定義を取得
            publicSnippet = "";
            privateSnippet = "";
            protectedSnippet = "";

            int start = classDefStart + 1;
            string curacc = "private";
            while (start < classDefEnd)
            {
                string acctype;
                int nextacc = NextAccessor(ref cpp, start, classDefEnd, out acctype);
                switch (curacc)
                {
                    case "public":
                        publicSnippet += cpp.Substring(start - 1, 1 + nextacc - start);
                        break;
                    case "private":
                        privateSnippet += cpp.Substring(start - 1, 1 + nextacc - start);
                        break;
                    case "protected":
                        protectedSnippet += cpp.Substring(start - 1, 1 + nextacc - start);
                        break;
                }
                start = nextacc + 1;
                curacc = acctype;
            }

            return true;
        }
        static bool MethodNameTypes(ref string methodCode, out string methodName, List<string> types)
        {
            methodName = "";

            var tokens = methodCode.Replace("(", " (").Split(' ').Where(t => !string.IsNullOrWhiteSpace(t)).ToArray();
            for (int i = 0; i < tokens.Length - 1; i++)
            {
                if (tokens[i + 1].StartsWith("("))
                {
                    methodName = tokens[i].Trim();
                    break;
                }
            }

            if (methodName == "")
                return false;

            var start = methodCode.IndexOf('(');
            var end = methodCode.IndexOf(')', start);
            if (start < 0 || end < 0)
                return false;

            if (end - start - 2 < 0)
                return true;

            string typeCode = methodCode.Substring(start + 1, end - start - 1);
            if (string.IsNullOrWhiteSpace(typeCode))
                return true;

            var types_ = typeCode.Split(',')
                .Select(token => token.Trim().Substring(0, token.Trim().LastIndexOf(' ')).Trim())
                .ToList();

            foreach (var t in types_)
                types.Add(t);

            return true;
        }
        static List<string> MethodVariableDefinitions(ref string code)
        {
            int start = code.IndexOf(':'); // public: , private: のあとから走査を始める
            if (start < 0)
                start = 0;
            else
                start++;

            int idx = start;

            List<int> braceStartPoints = new List<int>();
            List<int> braceEndPoints = new List<int>();
            braceStartPoints.Add(start);
            braceEndPoints.Add(start);
            while (true)
            {
                int _s, _e;
                bool res = FindNest(ref code, idx, "{", "}", out _s, out _e);
                if (res == false)
                    break;
                braceStartPoints.Add(_s);
                braceEndPoints.Add(_e);
                idx = _e;
            }
            braceStartPoints.Add(code.Length - 1);
            braceEndPoints.Add(code.Length - 1);

            System.Diagnostics.Debug.Assert(braceStartPoints.Count == braceEndPoints.Count);

            HashSet<int> cutPoints = new HashSet<int>();
            cutPoints.Add(start);

            for (int i = 1; i < braceEndPoints.Count; i++)
            {
                cutPoints.Add(braceEndPoints[i]);
            }
            for (int i = 0; i < braceEndPoints.Count - 1; i++)
            {
                int s = braceEndPoints[i];
                int e = braceStartPoints[i + 1];
                int _idx = s + 1;
                while (true)
                {
                    _idx = code.IndexOf(';', _idx, e - _idx + 1);
                    if (_idx < 0)
                        break;
                    cutPoints.Add(_idx);
                    _idx++;
                }
            }

            List<int> sortedCutPoints = cutPoints.OrderBy(_i => _i).ToList();
            int cur = start;
            List<string> snippets = new List<string>();
            for (int i = 0; i < sortedCutPoints.Count; i++)
            {
                snippets.Add(code.Substring(cur, sortedCutPoints[i] - cur + 1).Trim());
                cur = sortedCutPoints[i] + 1;
            }

            return snippets;
        }
        static int NextAccessor(ref string code, int start , int end, out string accessorType)
        {
            accessorType = "private";

            int pubidx = code.IndexOf("public:", start);
            if (pubidx < 0)
                pubidx = int.MaxValue;
            int priidx = code.IndexOf("private:", start);
            if (priidx < 0)
                priidx = int.MaxValue;
            int proidx = code.IndexOf("protected:", start);
            if (proidx < 0)
                proidx = int.MaxValue;

            int min = Math.Min(Math.Min(pubidx, priidx), proidx);
            if (min >= end)
                return end;

            if (pubidx < priidx && pubidx < proidx)
            {
                accessorType = "public";
                return pubidx;
            }
            if (priidx < pubidx && priidx < proidx)
            {
                accessorType = "private";
                return priidx;
            }
            if (proidx < pubidx && proidx < priidx)
            {
                accessorType = "protected";
                return proidx;
            }

            return end;
        }
        static bool FindNest(ref string code, int cursor, string sToken, string eToken, out int start, out int end)
        {
            int nest = 0;
            int idx = cursor;
            
            start = code.IndexOf(sToken, idx);
            end = start;

            if (start <= 0)
            {
                return false;
            }
            idx = start + sToken.Length;
            nest++;

            while (idx < code.Length)
            {
                int snext = code.IndexOf(sToken, idx);
                if (snext < 0)
                    snext = int.MaxValue;
                int enext = code.IndexOf(eToken, idx);
                if (enext < 0)
                    enext = int.MaxValue;
                if (snext == enext)
                    return false;

                if (snext < enext)
                {
                    // { が先
                    nest++;
                    idx = snext + sToken.Length;
                }
                else
                {
                    // } が先
                    nest--;
                    idx = enext + eToken.Length;
                    if (nest <= 0)
                    {
                        end = enext + eToken.Length;
                        return true;
                    }
                }
            }

            return false;
        }
        static bool FindImplClass(ref string cpp, out int classStart, out int classEnd, out int classDefStart, out int classDefEnd, out string className)
        {
            classStart = classEnd = classDefStart = classDefEnd = -1;
            className = "";

            classStart = cpp.IndexOf("class ");
            if (classStart < 0)
                return false;

            int classImplStart = cpp.IndexOf("::Impl");
            if (classImplStart < 0)
                return false;
            className = cpp.Substring(classStart, classImplStart - classStart).Split(' ').Where(t => !string.IsNullOrWhiteSpace(t)).Last();

            int braceStart, braceEnd;
            bool res = FindNest(ref cpp, classStart, "{", "}", out braceStart, out braceEnd);
            if (!res)
                return false;
            classEnd = braceEnd;

            classDefStart = braceStart + "[".Length;
            classDefEnd = braceEnd - "]".Length;
            classDefEnd = cpp.IndexOf(';', classDefEnd);
            if (classDefEnd < 0)
                return false;

            return true;
        }

        //-----------------------------------------------------

        static List<CodeTemplate> CreatePImplTemplates(string className)
        {
            var template = System.IO.File.ReadAllText("../../../Templates/pImplCreateClass.cpp");
            template = template.Replace(@"<%ClassName%>", className);

            var codes = template.Split(new[] { "[[[", "]]]" }, StringSplitOptions.RemoveEmptyEntries);
            codes = codes.Where(c => !string.IsNullOrWhiteSpace(c)).ToArray();
            System.Diagnostics.Debug.Assert(codes.Length % 2 == 0);
            List<CodeTemplate> ls = new List<CodeTemplate>();
            for (int i = 0; i < codes.Length / 2; i++)
            {
                string filename = codes[2 * i].Trim();
                string code = codes[2 * i + 1].Trim('\r', '\n');
                ls.Add(new CodeTemplate(className, filename, code));
            }
            return ls;
        }

        static void CreateMethod(List<CodeTemplate> templates, string className, string methodName, string returnType,
            List<string> argTypes, List<string> argNames)
        {
            System.Diagnostics.Debug.Assert(argTypes.Count == argNames.Count);

            var template = System.IO.File.ReadAllText("../../../Templates/pImplCreateMethod.cpp");
            template = template.Replace(@"<%ClassName%>", className);
            template = template.Replace(@"<%MethodName%>", methodName);
            template = template.Replace(@"<%ReturnType%>", returnType);
            template = template.Replace(@"<%ArgmentsType%>", string.Join(", ", argTypes));
            template = template.Replace(@"<%ArgmentsName%>", string.Join(", ", argNames));
            template = template.Replace(@"<%ArgmentsTypeName%>",
                 string.Join(", ", Enumerable.Range(0, argTypes.Count).Select(i => argTypes[i] + " " + argNames[i])));

            ModifyCode(templates, template);
        }

        static void CreateMethodVoid(List<CodeTemplate> templates, string className, string methodName, List<string> argTypes, List<string> argNames)
        {
            System.Diagnostics.Debug.Assert(argTypes.Count == argNames.Count);

            var template = System.IO.File.ReadAllText("../../../Templates/pImplCreateMethodVoid.cpp");
            template = template.Replace(@"<%ClassName%>", className);
            template = template.Replace(@"<%MethodName%>", methodName);
            template = template.Replace(@"<%ArgmentsType%>", string.Join(", ", argTypes));
            template = template.Replace(@"<%ArgmentsName%>", string.Join(", ", argNames));
            template = template.Replace(@"<%ArgmentsTypeName%>",
                 string.Join(", ", Enumerable.Range(0, argTypes.Count).Select(i => argTypes[i] + " " + argNames[i])));

            ModifyCode(templates, template);
        }

        static void ModifyCode(List<CodeTemplate> templates, string template)
        {
            var codes = template.Split(new[] { "[[[", "]]]" }, StringSplitOptions.RemoveEmptyEntries);
            codes = codes.Where(c => !string.IsNullOrWhiteSpace(c)).ToArray();
            System.Diagnostics.Debug.Assert(codes.Length % 2 == 0);

            for (int i = 0; i < codes.Length / 2; i++)
            {
                var tokens = codes[2 * i].Split(',').Select(t => t.Trim()).ToArray();
                System.Diagnostics.Debug.Assert(tokens.Length == 2);
                string filename = tokens[0];
                string replaceTarget = tokens[1].Trim();
                var codeTemplate = templates.First(t => t.filename == filename);

                string replaceCode = codes[2 * i + 1].Trim('\r', '\n');
                string newCode = "";
                foreach (var line in codeTemplate.code.Split('\n'))
                {
                    newCode += line + "\n";
                    if (line.Contains(replaceTarget))
                        newCode += replaceCode + "\n"; // !!ここが大事
                }
                codeTemplate.code = newCode;
            }
        }
    }
}