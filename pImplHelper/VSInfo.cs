using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Windows.Media.Imaging;
using System.ComponentModel.Composition;
using Microsoft.VisualStudio.Text.Classification;
using Microsoft.VisualStudio.Text.Editor;
using Microsoft.VisualStudio.Utilities;
using Microsoft.VisualStudio.Text.Formatting;
using EnvDTE;
using EnvDTE80;
using Microsoft.VisualStudio.Shell;

namespace Company.pImplHelper
{
    [Export(typeof(IWpfTextViewCreationListener))]
    [ContentType("C/C++")]
    [ContentType("CSharp")]
    [TextViewRole(PredefinedTextViewRoles.Document)]
    internal sealed class VSInfo : IWpfTextViewCreationListener
    {
        public static IWpfTextView WpfTextView { get { return _view; } }
        public static DTE DTE { get { return _dte; } }
        public static DTE2 DTE2 { get { return _dte2; } }
        public static Debugger Debugger { get { return _debugger; } }
        public static Debugger2 Debugger2 { get { return _debugger2; } }

        private static IWpfTextView _view;
        private static DTE _dte;
        private static DTE2 _dte2;
        private static Debugger _debugger;
        private static Debugger2 _debugger2;

        [Import]
        internal SVsServiceProvider ServiceProvider = null;

        [Export(typeof(AdornmentLayerDefinition))]
        [Name("TextAdornment1")]
        [Order(After = PredefinedAdornmentLayers.Text)]
        [TextViewRole(PredefinedTextViewRoles.Document)]
        public AdornmentLayerDefinition editorAdornmentLayer = null;

        public void TextViewCreated(IWpfTextView textView)
        {
            _view = textView;
            _dte = (DTE)ServiceProvider.GetService(typeof(DTE)) as DTE;
            _dte2 = (DTE2)ServiceProvider.GetService(typeof(DTE)) as DTE2;
            _debugger = _dte.Debugger;
            _debugger2 = _dte2.Debugger as Debugger2;
        }
    }
}