using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using IronPython.Hosting;
using Microsoft.Scripting.Hosting;

namespace Company.pImplHelper
{
    // pImplHelperの処理の実態。コードの自動生成や自動編集を行う
    class pImplHelper
    {
        //-----------------------------------------------------------------------
        // Pythonスクリプトの実行
        //-----------------------------------------------------------------------

        // ビルド時に scripts/pimpl.py が Debug(Release)直下にコピーされる 
        static string pythonPath
        {
            get
            {
#if DEBUG
                string path = "scripts/pimpl.py";
#else
                string root = System.Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                string path = System.IO.Path.Combine(root, "pImplHelper", "scripts/pimpl.py");
#endif
                return path;
            }
        }

        static ScriptEngine _python = null;
        static ScriptEngine python
        {
            get
            {
                if (_python == null)
                {
                    _python = Python.CreateEngine();
                    var paths = _python.GetSearchPaths();
                    paths.Add(System.IO.Path.GetDirectoryName(pythonPath));
                    paths.Add(@"C:\Program Files (x86)\IronPython 2.7\Lib");
                    _python.SetSearchPaths(paths);
                }
                return _python;
            }
        }

        static List<CodeTemplate> CreatePImplClass_python(string className)
        {
            dynamic pimpl = python.ExecuteFile(pythonPath);
            var res = pimpl.gen_new_class(className);
            List<CodeTemplate> ls = new List<CodeTemplate>()
            {
                new CodeTemplate(className, res[0], res[1]),
                new CodeTemplate(className, res[2], res[3]),
            };
            return ls;
        }

        static bool BindMethod_python(string header, string cpp, int selectStart, int selectEnd, out string outheader, out string outcpp)
        {
            try
            {
                dynamic pimpl = python.ExecuteFile(pythonPath);
                var header_cpp = pimpl.bind_pimpl_method_from_selection(header, cpp, selectStart, selectEnd);
                outheader = header_cpp[0];
                outcpp = header_cpp[1];
            }
            catch (Exception ex)
            {
                outheader = header;
                outcpp = cpp;
            }
            return true;
        }
        
        //-----------------------------------------------------------------------
        // 新規クラスの生成
        //-----------------------------------------------------------------------

        public static void GenerateNewClass()
        {
            if (VSInfo.DTE2 == null)
            {
                System.Windows.Forms.MessageBox.Show(
                    "Plugin have not been initialized. Please retry after opening a source code (.cpp or .cs).",
                    "Error",
                    System.Windows.Forms.MessageBoxButtons.OK,
                    System.Windows.Forms.MessageBoxIcon.Error);
                return;
            }

            var proj = GetProjectFromSelectedItems(VSInfo.DTE2.SelectedItems);
            if (proj == null)
            {
                System.Windows.Forms.MessageBox.Show(
                    "Any project is not selected",
                    "Error",
                    System.Windows.Forms.MessageBoxButtons.OK,
                    System.Windows.Forms.MessageBoxIcon.Error);
                return;
            }

            using (var win = new GeneratePImplClassForm(System.IO.Path.GetDirectoryName(proj.FullName)))
            {
                win.ShowDialog();
                if (string.IsNullOrWhiteSpace(win.ClassName))
                    return;

                var templates = CreatePImplClass_python(win.ClassName);

                System.Diagnostics.Debug.Assert(templates.Count == 2);
                System.Diagnostics.Debug.Assert(templates[0].className == win.ClassName);
                System.Diagnostics.Debug.Assert(templates[0].className == templates[1].className);
                System.Diagnostics.Debug.Assert(templates[0].filename.EndsWith(".h"));
                System.Diagnostics.Debug.Assert(templates[1].filename.EndsWith(".cpp"));

                templates[0].path = win.HeaderPath;
                templates[1].path = win.CppPath;

                foreach (var t in templates)
                {
                    // すでに存在していたら上書きするか確認
                    if (System.IO.File.Exists(t.path))
                    {
                        if (System.Windows.Forms.MessageBox.Show(
                                t.path + " already exists. Overwrite the existing file?", 
                                "File already exists", 
                                System.Windows.Forms.MessageBoxButtons.OKCancel, 
                                System.Windows.Forms.MessageBoxIcon.Warning, 
                                System.Windows.Forms.MessageBoxDefaultButton.Button2) != System.Windows.Forms.DialogResult.OK)
                            continue;
                    }
                    // 書き出し
                    System.IO.File.WriteAllText(t.path, t.code);
                    proj.ProjectItems.AddFromFile(t.path);
                }

                System.Windows.Forms.MessageBox.Show(
                    string.Format("class \"{0}\" have been created in {1} and {2}",
                    templates[0].className, templates[0].path, templates[1].path));
            }
        }

        static EnvDTE.Project GetProjectFromSelectedItems(EnvDTE.SelectedItems items)
        {
            if (items.Count != 1)
                return null;
            EnvDTE.Project proj = null;
            foreach (EnvDTE.SelectedItem item in items)
            {
                proj = item.Project;
                break;
            }
            return proj;
        }

        class CodeTemplate
        {
            public string className;
            public string filename;
            public string code;
            public string path;
            public CodeTemplate(string className, string filename, string code)
            {
                this.className = className;
                this.filename = filename;
                this.code = code;
            }
        }
        
        //-----------------------------------------------------------------------
        // メソッドのバインド
        //-----------------------------------------------------------------------

        public static bool BindMethod()
        {
            // カーソル取得
            int selectStart, selectEnd;
            GetSelection(out selectStart, out selectEnd);

            // ファイルのパス
            var path = VSInfo.DTE2.ActiveDocument.FullName;
            if (!path.EndsWith(".cpp"))
                return false;
            string headerpath = path.Substring(0, path.Length - 3) + "h";
            string cpppath = path;
            if (!System.IO.File.Exists(cpppath) || !System.IO.File.Exists(headerpath))
                return false;

            // コードを取得
            string header, cpp;
            EnvDTE.Document cppdoc, headerdoc;
            GetHeaderCppCode(headerpath, cpppath, out header, out headerdoc, out cpp, out cppdoc);

            // コード書き換え
            header = header.Replace("\r\n", "\n");
            cpp = cpp.Replace("\r\n", "\n");
            string outheader, outcpp;
            bool res = BindMethod_python(header, cpp, selectStart, selectEnd, out outheader, out outcpp);
            if (res == false)
                return false;

            // 書き換えたコードをファイルとエディタに反映
            if (header != outheader)
            {
                outheader = outheader.Replace("\n", "\r\n");
                if (headerdoc == null)
                    System.IO.File.WriteAllText(headerpath, outheader);
                else
                    SetTextFromDocument(headerdoc, outheader);
            }
            if (cpp != outcpp)
            {
                outcpp = outcpp.Replace("\n", "\r\n");
                if (cppdoc == null)
                    System.IO.File.WriteAllText(cpppath, outcpp);
                else
                    SetTextFromDocument(cppdoc, outcpp);
            }

            return true;
        }
        
        static string GetTextFromDocument(EnvDTE.Document doc)
        {
            var textdoc = doc.Object("TextDocument") as EnvDTE.TextDocument;
            EnvDTE.EditPoint editPoint = textdoc.StartPoint.CreateEditPoint();
            string code = editPoint.GetText(textdoc.EndPoint);
            return code;
        }
        
        static void SetTextFromDocument(EnvDTE.Document doc, string value)
        {
            var textdoc = doc.Object("TextDocument") as EnvDTE.TextDocument;
            textdoc.Selection.SelectAll();
            textdoc.Selection.Delete();
            textdoc.Selection.Insert(value);
            textdoc.Selection.SmartFormat();
        }

        static void GetSelection(out int selectStart, out int selectEnd)
        {
            var doc = VSInfo.DTE2.ActiveDocument.Object("TextDocument") as EnvDTE.TextDocument;
            selectStart = doc.Selection.ActivePoint.AbsoluteCharOffset;
            selectEnd = doc.Selection.AnchorPoint.AbsoluteCharOffset;
            if (selectStart > selectEnd)
            {
                int t = selectStart;
                selectStart = selectEnd;
                selectEnd = t;
            }
        }

        static bool GetHeaderCppCode(string headerpath, string cpppath, out string header, out EnvDTE.Document headerdoc, out string cpp, out EnvDTE.Document cppdoc)
        {
            cppdoc = null;
            headerdoc = null;
            header = null;
            cpp = null;
            foreach (EnvDTE.Document _doc in VSInfo.DTE2.Documents)
            {
                if (_doc.FullName == headerpath)
                {
                    header = GetTextFromDocument(_doc);
                    headerdoc = _doc;
                }
                if (_doc.FullName == cpppath)
                {
                    cpp = GetTextFromDocument(_doc);
                    cppdoc = _doc;
                }
            }
            if (header == null)
                header = System.IO.File.ReadAllText(headerpath);
            if (cpp == null)
                cpp = System.IO.File.ReadAllText(cpppath);
            return true;
        }

    }
}
