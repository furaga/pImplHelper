using System;
using System.Diagnostics;
using System.Globalization;
using System.Runtime.InteropServices;
using System.ComponentModel.Design;
using Microsoft.Win32;
using Microsoft.VisualStudio;
using Microsoft.VisualStudio.Shell.Interop;
using Microsoft.VisualStudio.OLE.Interop;
using Microsoft.VisualStudio.Shell;

namespace Company.pImplHelper
{
    [PackageRegistration(UseManagedResourcesOnly = true)]
    [InstalledProductRegistration("#110", "#112", "1.0", IconResourceID = 400)]
    [ProvideMenuResource("Menus.ctmenu", 1)]
    [Guid(GuidList.guidpImplHelperPkgString)]
    public sealed class pImplHelperPackage : Package
    {
        public pImplHelperPackage()
        {
        }

        // メニューを追加
        protected override void Initialize()
        {
            base.Initialize();
            OleMenuCommandService mcs = GetService(typeof(IMenuCommandService)) as OleMenuCommandService;
            if (null != mcs)
            {
                foreach (var cmdid in new[] { PkgCmdIDList.cmdidPImplHelper_GenClass, PkgCmdIDList.cmdidPImplHelper_WrapMethod })
                {
                    CommandID menuCommandID = new CommandID(GuidList.guidpImplHelperCmdSet, (int)cmdid);
                    MenuCommand menuItem = new MenuCommand(MenuItemCallback, menuCommandID);
                    mcs.AddCommand(menuItem);
                }
            }
        }

        // pImplHelperの各機能を実行
        private void MenuItemCallback(object sender, EventArgs e)
        {
            if (!(sender is MenuCommand))
                return;
            switch ((uint)(sender as MenuCommand).CommandID.ID)
            {
                case PkgCmdIDList.cmdidPImplHelper_GenClass:
                    pImplHelper.GenerateClass();
                    break;
                case PkgCmdIDList.cmdidPImplHelper_WrapMethod:
                    pImplHelper.WrapMethod();
                    break;
            }
        }

    }
}