using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data;
using System.Drawing;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows.Forms;

namespace Company.pImplHelper
{
    public partial class GeneratePImplClassForm : Form
    {
        bool isOK = false;
        public string ClassName { get; private set; }
        public string HeaderPath{ get; private set; }
        public string CppPath { get; private set; }
        public string defaultDir = "";
        public GeneratePImplClassForm(string defaultDir)
        {
            InitializeComponent();
            this.defaultDir = defaultDir;
        }

        private void textBox1_TextChanged(object sender, EventArgs e)
        {
            ClassName = "";
            foreach (char c in classNameTextbox.Text)
                if (!char.IsWhiteSpace(c))
                    ClassName += c;

            if (VSInfo.DTE2 != null)
            {
                HeaderPath = System.IO.Path.Combine(defaultDir, ClassName + ".h");
                headerTextbox.Text = HeaderPath;
                CppPath = System.IO.Path.Combine(defaultDir, ClassName + ".cpp");
                cppTextbox.Text = CppPath;
            }
        }

        private void OKButton_Click(object sender, EventArgs e)
        {
            isOK = true;
            this.Close();
        }

        private void CancelButton_Click(object sender, EventArgs e)
        {
            ClassName = HeaderPath = CppPath = "";
            this.Close();
        }

        private void GeneratePImplClassForm_FormClosed(object sender, FormClosedEventArgs e)
        {
            if (!isOK)
                ClassName = HeaderPath = CppPath = "";
        }

        private void GeneratePImplClassForm_Load(object sender, EventArgs e)
        {
            textBox1_TextChanged(null, null);
            if (VSInfo.DTE2 != null)
            {
                string dir = System.IO.Path.GetDirectoryName(VSInfo.DTE2.ActiveDocument.FullName);
                HeaderPath = System.IO.Path.Combine(dir, ClassName + ".h");
                headerTextbox.Text = HeaderPath;
                CppPath = System.IO.Path.Combine(dir, ClassName + ".cpp");
                cppTextbox.Text = CppPath;
            }
        }
    }
}
