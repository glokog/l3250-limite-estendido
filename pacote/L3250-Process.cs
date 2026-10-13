using System;
using System.Diagnostics;

// .NET 2.0 APIs; avoid the PowerShell 2 Start-Process -PassThru adapter.
public static class L3250Process {
    public static int Run(string executable, string arguments, bool elevate) {
        ProcessStartInfo info = new ProcessStartInfo(executable, arguments);
        info.UseShellExecute = true;
        if (elevate) info.Verb = "runas";
        using (Process process = Process.Start(info)) {
            if (process == null) throw new InvalidOperationException("Processo nao retornou um identificador.");
            IntPtr handle = process.Handle;
            if (handle == IntPtr.Zero) throw new InvalidOperationException("Identificador de processo invalido.");
            process.WaitForExit();
            return process.ExitCode;
        }
    }
}
