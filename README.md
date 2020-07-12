# Notes of reversing ba321ad38f1d52cc0a8b94807fda8ff7 f1bb149c5d9dd76ea9a91eb8e10c86f45d86c4336e5a9cdcaddd4b0161c9d4de malware.

Executable is AutoIt script(https://www.autoitscript.com/autoit3/docs/). There is AutoIt decompiler Exe2Aut.exe, but the malware has quite a lot of obfuscation. So simple decompiling does not help, see ba321ad38f1d52cc0a8b94807fda8ff7.au3.

There is IsDebuggerPresent call in AutoIt. Patch it: FF 15 30 F3 2A 00 -> 66 B8 00 00 90 90
![Debug](/Images/Debug.png)

Wrote Frida script(trace_calls.py) to trace AutoIt execution, to better understand what script does. This script hooks all AutoIt commands and logs commands with call parameters. Script also dumps AutoIt command addresses and names for Ida Pro for easier debugging. Example trace in AutoItLog.txt

In the log, we see script calls VirtualAlloc:
DLLCALL("kernel32","ptr","VirtualAlloc","dword","0","dword",569611,"dword","0x3000","dword","0x40")

Later it calls allocated address and passes pointer to struct and some magic string as parameters:
DLLCALLADDRESS("dword",0x3e90000,"ptr",0x4074020,"int",284672,"str","FMPEXKQQCK","int",0)

This seems to be some kind of unpacking operation, as there are not any WinAPI calls in this code.

Later there is a new allocation:
EXECUTE("DllCall("kernel32", "ptr", "VirtualAlloc", "dword", "0", "dword", BinaryLen($DD), "dword", "0x3000", "dword", "0x40")["0"]")

And call to the allocated address + 0x0be : 
DLLCALLADDRESS("dword",0x41000be,"wstr","C:\\\\Windows\\\\Microsoft.NET\\\\Framework\\\\v2.0.50727\\\\MSBuild.exe","wstr","","ptr",0x5d11020)

This shellcode calls CreateProcessW and tries to create a suspended thread of MSBuild.exe. This file does not exist on Windows 10 setup. Installed dotnet v2.0 SP1. But this call still seems to fail. Stopped here. Sorry :-)

trace_calls.py also dumps these memories to disk see code.bin for 0x4100000. Omitting data.bin from this repo, as it is malicious. This repo also has ShellcodeRun.exe to load them to memory and run. Remove the underscore from .bin files, if you want to run them.


Here are tips to get trace from AutoIt execution:
Find function table from memory and patch funcStart and funcEnd addresses:
![CommandsMem](/Images/CommandsMem.png)

There is function that sets these values:
![Commands](/Images/Commands.png)

Set this interceptor after the sets are done. 
// Intercept function calls, dump function names for IDA Pro.
Interceptor.attach(ptr('0x007FAC6'), 

Here is some structures:
First parameter of all functions
![CallContext_t](/Images/CallContext_t.png)

Variable type. Also second parameter of functions as return value.
![Variable_t](/Images/Variable_t.png)
