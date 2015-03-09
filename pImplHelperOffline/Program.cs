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
        // ビルド時に scripts/pimpl.py が Debug(Release)直下にコピーされる 
        static string pythonPath
        {
            get
            {
                string root = System.Environment.GetFolderPath(Environment.SpecialFolder.MyDocuments);
                string path = System.IO.Path.Combine(root, "pImplHelper", "scripts/pimpl.py");
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

        static bool BindMethod_python(string header, string cpp, int selectStart, int selectEnd, out string outheader, out string outcpp)
        {
            outheader = outcpp = "";
            try
            {
                // todo: cpythonをかわりに使う。ironpythonはlibclang.dllの関数を実行しようとするとnotimplementederrorがでる

                string rootDir = System.IO.Path.GetDirectoryName(pythonPath);
                System.IO.Directory.CreateDirectory(System.IO.Path.Combine(rootDir, "tmp"));
                System.IO.File.WriteAllText(System.IO.Path.Combine(rootDir, "tmp", "__dummy__.h"), header);
                System.IO.File.WriteAllText(System.IO.Path.Combine(rootDir, "tmp", "__dummy__.cpp"), cpp);

                System.Diagnostics.ProcessStartInfo psInfo = new System.Diagnostics.ProcessStartInfo();

                psInfo.FileName = "python.exe"; // 実行するファイル
                // psInfo.Arguments = "pimpl.py new_class";
                psInfo.Arguments = "pimpl.py wrap_method tmp/__dummy__.h tmp/__dummy__.cpp " + selectStart + " " + selectEnd;
                psInfo.CreateNoWindow = true; // コンソール・ウィンドウを開かない
                psInfo.UseShellExecute = false; // シェル機能を使用しない
                psInfo.RedirectStandardOutput = true; // 標準出力をリダイレクト
                psInfo.WorkingDirectory = rootDir;
                System.Diagnostics.Process p = System.Diagnostics.Process.Start(psInfo); // アプリの実行開始
                string output = p.StandardOutput.ReadToEnd(); // 標準出力の読み取り

                List<string> snippets = new List<string>();
                string snip = "";
                const string splitLine = "****************************************"; // "*" * 40
                foreach (var _line in output.Split('\n'))
                {
                    var line = _line.TrimEnd();
                    if (line == splitLine)
                    {
                        snippets.Add(snip);
                        snip = "";
                    }
                    else
                    {
                        snip += line + "\r\n";
                    }
                }

                if (snippets.Count >= 2)
                {
                    outheader = snippets[snippets.Count - 2];
                    outcpp = snippets[snippets.Count - 1];
                }
            }
            catch (Exception ex)
            {
                outheader = header;
                outcpp = cpp;
            }
            return true;
        }

        //-----------------------------------------------------------------------
        // メソッドのバインド
        //-----------------------------------------------------------------------

        public static bool BindMethod()
        {
            // コードを取得
            string header, cpp;
            GetHeaderCppCode("SampleClass.h", "SampleClass.cpp", out header, out cpp);

            // コード書き換え
            header = header.Replace("\r\n", "\n");
            cpp = cpp.Replace("\r\n", "\n");
            string outheader, outcpp;
            bool res = BindMethod_python(header, cpp, 0, cpp.Length, out outheader, out outcpp);
            if (res == false)
                return false;

            Console.WriteLine("=======================");
            Console.WriteLine(outheader);
            Console.WriteLine("=======================");
            Console.WriteLine(outcpp);
            Console.WriteLine("=======================");

            Console.Read();

            return true;
        }

        static bool GetHeaderCppCode(string headerpath, string cpppath, out string header, out string cpp)
        {
            header = System.IO.File.ReadAllText(headerpath);
            cpp = System.IO.File.ReadAllText(cpppath);
            return true;
        }

        static void Main(string[] args)
        {
            BindMethod();
        }
    }
}