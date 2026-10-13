using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;

// Windows 7 / .NET 2.0 compatible; reads only local spooler inventories.
public sealed class L3250DriverInfo {
    public string Name, SupportedPlatform, DriverPath, ConfigFile, DataFile;
    public string[] DependentFiles;
}
public sealed class L3250PrinterInfo {
    public string Name, DriverName, PortName;
    public uint Jobs;
}
public static class L3250Spooler {
    [StructLayout(LayoutKind.Sequential)]
    private struct DRIVER_INFO_3 {
        public uint Version;
        public IntPtr Name, Environment, DriverPath, DataFile, ConfigFile;
        public IntPtr HelpFile, DependentFiles, MonitorName, DefaultDataType;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct PRINTER_INFO_2 {
        public IntPtr ServerName, PrinterName, ShareName, PortName, DriverName;
        public IntPtr Comment, Location, DevMode, SepFile, PrintProcessor;
        public IntPtr Datatype, Parameters, SecurityDescriptor;
        public uint Attributes, Priority, DefaultPriority, StartTime, UntilTime;
        public uint Status, Jobs, AveragePPM;
    }
    [DllImport("winspool.drv", EntryPoint="EnumPrinterDriversW", ExactSpelling=true,
        CharSet=CharSet.Unicode, SetLastError=true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumPrinterDrivers(string server, string environment,
        uint level, IntPtr buffer, uint size, out uint needed, out uint count);
    [DllImport("winspool.drv", EntryPoint="EnumPrintersW", ExactSpelling=true,
        CharSet=CharSet.Unicode, SetLastError=true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool EnumPrinters(uint flags, string name, uint level,
        IntPtr buffer, uint size, out uint needed, out uint count);
    private static string Text(IntPtr pointer) {
        return pointer == IntPtr.Zero ? "" : Marshal.PtrToStringUni(pointer);
    }
    private static string[] MultiText(IntPtr pointer) {
        List<string> values = new List<string>();
        if (pointer != IntPtr.Zero) {
            while (Marshal.ReadInt16(pointer) != 0) {
                string value = Text(pointer);
                values.Add(value);
                pointer = new IntPtr(pointer.ToInt64() + (value.Length + 1) * 2);
            }
        }
        return values.ToArray();
    }
    private static void CheckSize(uint needed) {
        if (needed > 64 * 1024 * 1024) throw new InvalidOperationException("Spooler buffer exceeds 64 MiB.");
    }
    public static L3250DriverInfo[] Drivers() {
        uint needed, count;
        bool ok = EnumPrinterDrivers(null, "Windows x64", 3, IntPtr.Zero, 0, out needed, out count);
        int error = Marshal.GetLastWin32Error();
        if (!ok && error != 122) throw new Win32Exception(error, "EnumPrinterDriversW");
        if (needed == 0) return new L3250DriverInfo[0];
        CheckSize(needed);
        IntPtr buffer = Marshal.AllocHGlobal((int)needed);
        try {
            uint capacity = needed;
            if (!EnumPrinterDrivers(null, "Windows x64", 3, buffer, capacity, out needed, out count))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "EnumPrinterDriversW");
            int size = Marshal.SizeOf(typeof(DRIVER_INFO_3));
            if ((ulong)count * (ulong)size > capacity) throw new InvalidOperationException("Invalid driver count.");
            List<L3250DriverInfo> result = new List<L3250DriverInfo>();
            for (uint i = 0; i < count; i++) {
                IntPtr item = new IntPtr(buffer.ToInt64() + (long)i * size);
                DRIVER_INFO_3 d = (DRIVER_INFO_3)Marshal.PtrToStructure(item, typeof(DRIVER_INFO_3));
                L3250DriverInfo value = new L3250DriverInfo();
                value.Name = Text(d.Name); value.SupportedPlatform = Text(d.Environment);
                value.DriverPath = Text(d.DriverPath); value.ConfigFile = Text(d.ConfigFile);
                value.DataFile = Text(d.DataFile); value.DependentFiles = MultiText(d.DependentFiles);
                result.Add(value);
            }
            return result.ToArray();
        } finally { Marshal.FreeHGlobal(buffer); }
    }
    public static L3250PrinterInfo[] Printers() {
        uint needed, count;
        // PRINTER_ENUM_LOCAL: only queues backed by locally installed drivers.
        bool ok = EnumPrinters(2, null, 2, IntPtr.Zero, 0, out needed, out count);
        int error = Marshal.GetLastWin32Error();
        if (!ok && error != 122) throw new Win32Exception(error, "EnumPrintersW");
        if (needed == 0) return new L3250PrinterInfo[0];
        CheckSize(needed);
        IntPtr buffer = Marshal.AllocHGlobal((int)needed);
        try {
            uint capacity = needed;
            if (!EnumPrinters(2, null, 2, buffer, capacity, out needed, out count))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "EnumPrintersW");
            int size = Marshal.SizeOf(typeof(PRINTER_INFO_2));
            if ((ulong)count * (ulong)size > capacity) throw new InvalidOperationException("Invalid printer count.");
            List<L3250PrinterInfo> result = new List<L3250PrinterInfo>();
            for (uint i = 0; i < count; i++) {
                IntPtr item = new IntPtr(buffer.ToInt64() + (long)i * size);
                PRINTER_INFO_2 p = (PRINTER_INFO_2)Marshal.PtrToStructure(item, typeof(PRINTER_INFO_2));
                L3250PrinterInfo value = new L3250PrinterInfo();
                value.Name = Text(p.PrinterName); value.DriverName = Text(p.DriverName);
                value.PortName = Text(p.PortName); value.Jobs = p.Jobs;
                result.Add(value);
            }
            return result.ToArray();
        } finally { Marshal.FreeHGlobal(buffer); }
    }
}
