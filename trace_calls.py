#!/usr/bin/python3
import frida
import sys
import json

def on_message(message,data):
	if(message['type']=='send'):
		print(message['payload'])		
	
		
def on_detached():
	sys.exit(0)	
	

pid = frida.spawn(['ba321ad38f1d52cc0a8b94807fda8ff7.exe'])
session = frida.attach(pid)

script = session.create_script("""

var funcStart=new NativePointer('0x01204B4');
var funcEnd=new NativePointer('0x0123DA4');

function varToStr(ptr) {
  var type=ptr.add(0x0c).readU32();
  if(type==1)	
     return ptr.readU32().toString();
  if(type==2)	
     return ptr.readU64().toString();
  if(type==3)	
     return ptr.readDouble().toString();
  if(type==4)	
     return '"'+ptr.add(8).readPointer().readPointer().readUtf16String()+'"';
  if(type==7)	
     return ptr.readPointer().toString();
  if(type==12)	
     return ptr.add(0).readPointer().add(8).readPointer().toString()+' len='+ptr.add(0).readPointer().add(12).readU32().toString();

  return '??unknown type '+type+'??';
}

function logCall(args,p1)
{
  try
  {
	var ptr;
	var pcount;
        var logStr='';

	var addr=new NativePointer(p1);
	for(ptr=funcStart;ptr<funcEnd;ptr=ptr.add(36))
	{
		var fp2=ptr.add(12).readPointer();	
		if(fp2.equals(addr))
		{
			pcount=new NativePointer(args[0]).add(8).readU32();		
			logStr+=ptr.readPointer().readUtf16String()+'(';

  			var i;
			var first=true;
  			for(i=0;i<pcount*4;i+=4)
			{
				if(first===true)
					first=0;
				else
					logStr+=',';

				logStr+=varToStr(new NativePointer(args[0]).add(4).readPointer().add(i).readPointer());
				
			}
			logStr+=')';
			console.log(logStr);    		
		}
	}
  }
  catch(error)
  {
    console.log(error);
  }
}


function writeBinFile(name,addr,len)
{
	var h=new File(name, 'wb');
	h.write(addr.readByteArray(len));
}

function handleDLLCALLADDRESS(args,p1)
{
  try
  {
	logCall(args,p1);
	var pcount=new NativePointer(args[0]).add(8).readU32();

	if(pcount==8 && varToStr(new NativePointer(args[0]).add(4).readPointer().add(12).readPointer()).includes('MSBuild.exe'))
	{
   		var codeAddr=new NativePointer(args[0]).add(4).readPointer().add(4).readPointer().readPointer();
		writeBinFile('code.bin',codeAddr.add(-190),1474);
   		var dataAddr=new NativePointer(args[0]).add(4).readPointer().add(28).readPointer().readPointer();
		writeBinFile('data.bin',dataAddr,1138694);
		console.log('wrote files');
	}
  }
  catch(error)
  {
    console.log(error);
  }
}


// Dump function names for IDA Pro
Interceptor.attach(ptr('0x007FAC6'), 
     function(args) {
		var ptr;
		var msg='';
		for(ptr=funcStart;ptr<funcEnd;ptr=ptr.add(36))
		{		
			var fname=ptr.readPointer().readUtf16String();
			msg+='MakeName('+ptr.add(12).readPointer().toString()+',"'+fname+'_func");';

			if(fname.includes('STRING') ||fname.includes('BITXOR') ||fname.includes('CHRW') ||fname.includes('ASC'))
			{
				console.log('Skipping: '+fname);  
				continue;
			}
			if(fname=="DLLCALLADDRESS")
			{
			  Interceptor.attach(ptr.add(12).readPointer(), {
    				onEnter: function(args) {
					handleDLLCALLADDRESS(args,this.context.pc);	 				
    				}
			  });
			}
			else
			{
			Interceptor.attach(ptr.add(12).readPointer(), {
    				onEnter: function(args) {
					logCall(args,this.context.pc);	 				
    				}
			});
			}
		}
		send(msg);    
});


var load = Module.findExportByName('kernel32', 'VirtualAlloc')

Interceptor.attach(load, {
    onEnter: function (args) {
        console.log('VirtualAlloc(' + new NativePointer(args[0]).toString()+','+args[1].toString()+','+args[2].toString()+','+args[3].toString()+')');
    },
    onLeave: function (retval) {
	console.log('VirtualAlloc returns:'+retval.toString());
    }
});

""")

script.on('message', on_message)
session.on('detached', on_detached)
script.load()
frida.resume(pid)

