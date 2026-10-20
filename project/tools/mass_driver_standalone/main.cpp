#include <windows.h>
#include <shlobj.h>
#include <shobjidl.h>
#include <shellapi.h>
#include <commctrl.h>
#include <bcrypt.h>
#include <atomic>
#include <algorithm>
#include <filesystem>
#include <fstream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>
#include <set>
#include <cwctype>
#include "archive.h"
#include "private_config.h"

namespace fs = std::filesystem;
static const wchar_t* kTitle = L"Mass Driver";
static const wchar_t* kPlayName = L"Play Mass Driver.exe";
static const wchar_t* kRuntime = L"runtime/duckstation-qt-x64-ReleaseLTCG.exe";
static const wchar_t* kCue = L"game/Xenogears_Mass_Driver.cue";
#ifdef PUBLIC_PLAYER
static const wchar_t* kInstallDirectory = L"Xenogears Mass Driver";
#else
static const wchar_t* kInstallDirectory = L"Xenogears Mass Driver Private";
#endif
static HWND gWindow=nullptr,gInstall=nullptr,gPlay=nullptr,gOpenFolder=nullptr,gShortcut=nullptr,gCancelButton=nullptr,gStatus=nullptr,gProgress=nullptr,gLocation=nullptr;
static std::atomic<bool> gCancel(false),gWorking(false);
static fs::path gSelf,gRoot;
static mdarchive::Info gArchive;
static bool gHasArchive=false;
static constexpr UINT WM_PROGRESS=WM_APP+1,WM_FINISHED=WM_APP+2;

static std::string Utf8(const std::wstring& value) {
    int size=WideCharToMultiByte(CP_UTF8,0,value.data(),static_cast<int>(value.size()),nullptr,0,nullptr,nullptr);
    std::string text(size,'\0'); WideCharToMultiByte(CP_UTF8,0,value.data(),static_cast<int>(value.size()),text.data(),size,nullptr,nullptr); return text;
}
static std::wstring Wide(const std::string& text) {
    int size=MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),nullptr,0);
    if(size<=0 && !text.empty()) throw std::runtime_error("Invalid UTF8");
    std::wstring value(size,L'\0'); MultiByteToWideChar(CP_UTF8,MB_ERR_INVALID_CHARS,text.data(),static_cast<int>(text.size()),value.data(),size); return value;
}
static std::string HashText(const std::string& data) {
    BCRYPT_ALG_HANDLE algorithm=nullptr; BCRYPT_HASH_HANDLE hash=nullptr; unsigned char bytes[32]{};
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0) throw std::runtime_error("SHA256");
    auto status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(status>=0) status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char*>(data.data())),static_cast<ULONG>(data.size()),0);
    if(status>=0) status=BCryptFinishHash(hash,bytes,32,0);
    if(hash) BCryptDestroyHash(hash); BCryptCloseAlgorithmProvider(algorithm,0);
    if(status<0) throw std::runtime_error("SHA256");
    std::string result; for(auto byte:bytes) {result+="0123456789abcdef"[byte>>4];result+="0123456789abcdef"[byte&15];} return result;
}
static bool Hex(const std::string& text) {return text.size()==64 && text.find_first_not_of("0123456789abcdef")==std::string::npos;}
static bool Plain(const fs::path& path,bool directory) {
    DWORD attributes=GetFileAttributesW(path.c_str()); return attributes!=INVALID_FILE_ATTRIBUTES && !(attributes&FILE_ATTRIBUTE_REPARSE_POINT) &&
        static_cast<bool>(attributes&FILE_ATTRIBUTE_DIRECTORY)==directory;
}
static bool SafeTree(const fs::path& path) {
    fs::path current;
    for(const auto& part:path) {current/=part; if(fs::exists(current) && !Plain(current,true)) return false;} return true;
}
static fs::path NormalizeRoot(const fs::path& requested) {
    auto absolute=fs::absolute(requested).lexically_normal();
    for(const auto& part:absolute.relative_path()){
        auto name=part.wstring();
        if(name.empty()||name.back()==L'.'||name.back()==L' '||name.find_first_of(L"<>:\"|?*")!=std::wstring::npos)throw std::runtime_error("Invalid installation path");
        auto stem=part.stem().wstring();for(auto& ch:stem)ch=static_cast<wchar_t>(towupper(ch));
        if(stem==L"CON"||stem==L"PRN"||stem==L"AUX"||stem==L"NUL"||
           (stem.size()==4&&(stem.rfind(L"COM",0)==0||stem.rfind(L"LPT",0)==0)&&stem[3]>=L'1'&&stem[3]<=L'9'))throw std::runtime_error("Reserved installation path");
    }
    if(!SafeTree(absolute))throw std::runtime_error("Linked installation path");
    auto ancestor=absolute;std::vector<fs::path> missing;
    while(!fs::exists(ancestor)){missing.push_back(ancestor.filename());auto parent=ancestor.parent_path();if(parent==ancestor)throw std::runtime_error("Missing path root");ancestor=parent;}
    auto directory=CreateFileW(ancestor.c_str(),FILE_READ_ATTRIBUTES,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,nullptr,OPEN_EXISTING,FILE_FLAG_BACKUP_SEMANTICS,nullptr);
    if(directory==INVALID_HANDLE_VALUE)throw std::runtime_error("Cannot normalize path");
    std::vector<wchar_t> normalized(32768);auto size=GetFinalPathNameByHandleW(directory,normalized.data(),static_cast<DWORD>(normalized.size()),FILE_NAME_NORMALIZED|VOLUME_NAME_DOS);CloseHandle(directory);
    if(!size||size>=normalized.size())throw std::runtime_error("Cannot normalize path");
    std::wstring text(normalized.data(),size);if(text.rfind(L"\\\\?\\UNC\\",0)==0)text=L"\\\\"+text.substr(8);else if(text.rfind(L"\\\\?\\",0)==0)text=text.substr(4);
    fs::path result(text);for(auto item=missing.rbegin();item!=missing.rend();++item)result/=*item;return result;
}
static std::string ReadText(const fs::path& path,size_t cap=2*1024*1024) {
    if(!Plain(path,false) || fs::file_size(path)>cap) throw std::runtime_error("Invalid text file");
    std::ifstream source(path,std::ios::binary); return std::string(std::istreambuf_iterator<char>(source),{});
}
static std::wstring Guid() {GUID id{};wchar_t value[40]{};if(FAILED(CoCreateGuid(&id))||!StringFromGUID2(id,value,40))throw std::runtime_error("GUID");return value;}
static void WriteAtomic(const fs::path& path,const std::string& data,bool preserve=false) {
    if(fs::exists(path)) {if(!Plain(path,false))throw std::runtime_error("Linked output");if(preserve||ReadText(path,std::max<size_t>(data.size()+1,2*1024*1024))==data)return;}
    if(!SafeTree(path.parent_path()))throw std::runtime_error("Linked output directory");
    fs::create_directories(path.parent_path()); auto temp=path.parent_path()/(L".write-"+Guid());
    HANDLE output=INVALID_HANDLE_VALUE;bool owned=false;
    try {output=CreateFileW(temp.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(output==INVALID_HANDLE_VALUE)throw std::runtime_error("Write failed");owned=true;
        size_t offset=0;while(offset<data.size()){DWORD written=0;auto amount=static_cast<DWORD>(std::min<size_t>(data.size()-offset,1ULL<<20));if(!WriteFile(output,data.data()+offset,amount,&written,nullptr)||written==0)throw std::runtime_error("Write failed");offset+=written;}
        if(!FlushFileBuffers(output))throw std::runtime_error("Flush failed");CloseHandle(output);output=INVALID_HANDLE_VALUE;
        if(!MoveFileExW(temp.c_str(),path.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH))throw std::runtime_error("Commit failed");
    }catch(...){if(output!=INVALID_HANDLE_VALUE)CloseHandle(output);if(owned){std::error_code ignored;fs::remove(temp,ignored);}throw;}
}
static std::string LogicalManifest(const mdarchive::Info& info) {
    auto files=info.files;std::sort(files.begin(),files.end(),[](const auto&a,const auto&b){return a.path<b.path;});
    std::string text="XGMDCONTENT1\n";for(const auto&file:files) text+=std::to_string(file.size)+"\t"+file.sha256+"\t"+Utf8(file.path)+"\n";return text;
}
static bool CheckLogical(const mdarchive::Info& info,std::wstring& error) {
    if(HashText(LogicalManifest(info))!=PRIVATE_CONTENT_SHA256){
#ifdef PUBLIC_PLAYER
        error=L"This installer or content manifest does not match this Mass Driver build.";
#else
        error=L"This installer or content manifest does not match this private build.";
#endif
        return false;}return true;
}
static fs::path VersionPath(const fs::path& root,const std::string& identity){return root/L"v"/Wide(identity.substr(0,16));}
static bool LoadInstalled(const fs::path& root,fs::path& version,mdarchive::Info& info,std::wstring& error,bool verify=true) {
    try {
        if(!SafeTree(root)||!Plain(root,true))throw std::runtime_error("Invalid installation folder");
        auto identity=ReadText(root/L"installation.txt",66);if(identity.size()==65&&identity.back()=='\n')identity.pop_back();
        if(!Hex(identity))throw std::runtime_error("Invalid installation identity");
        version=VersionPath(root,identity);if(!SafeTree(version)||!Plain(version,true))throw std::runtime_error("Invalid version folder");
        auto text=ReadText(version/L"content_manifest.txt");if(HashText(text)!=PRIVATE_CONTENT_SHA256)throw std::runtime_error("Changed content manifest");
        std::istringstream lines(text);std::string line;std::getline(lines,line);if(line!="XGMDCONTENT1")throw std::runtime_error("Invalid manifest");
        info={};info.identity=identity;
        while(std::getline(lines,line)) {
            auto first=line.find('\t'),second=line.find('\t',first+1);if(first==std::string::npos||second==std::string::npos)throw std::runtime_error("Invalid entry");
            mdarchive::Entry file;file.size=std::stoull(line.substr(0,first));file.sha256=line.substr(first+1,second-first-1);auto name=line.substr(second+1);
            if(!Hex(file.sha256)||name.empty()||name.find("..")!=std::string::npos||name.front()=='/'||name.find('\\')!=std::string::npos||name.find(':')!=std::string::npos)throw std::runtime_error("Unsafe entry");
            file.path=Wide(name);info.totalSize+=file.size;info.files.push_back(file);
        }
        if(!CheckLogical(info,error))return false;
        return !verify||mdarchive::Verify(version,info,error);
    } catch(...) {
#ifdef PUBLIC_PLAYER
        error=L"This installation is missing or changed. Run Mass_Driver_Setup.exe to repair the program files.";
#else
        error=L"This installation is missing or changed. Run the private installer to repair it.";
#endif
        return false;}
}
static fs::path DefaultRoot() {PWSTR local=nullptr;if(FAILED(SHGetKnownFolderPath(FOLDERID_LocalAppData,KF_FLAG_CREATE,nullptr,&local)))throw std::runtime_error("LocalAppData");fs::path root=fs::path(local)/kInstallDirectory;CoTaskMemFree(local);return root;}
static std::string Slash(const fs::path& path){return Utf8(path.generic_wstring());}
static fs::path BiosDirectory(const fs::path& root,const fs::path& version){
#ifdef PUBLIC_PLAYER
    return root/L"UserData/bios";
#else
    return version/L"bios";
#endif
}
static const char* BiosFilename(){
#ifdef PUBLIC_PLAYER
    return "user-bios.bin";
#else
    return "ps-22a.bin";
#endif
}
static void ReplaceAll(std::string& text,const std::string& from,const std::string& to){size_t pos=0;while((pos=text.find(from,pos))!=std::string::npos){text.replace(pos,from.size(),to);pos+=to.size();}}
static void SeedData(const fs::path& root,const fs::path& version) {
    auto data=root/L"UserData";if(!SafeTree(data))throw std::runtime_error("Linked user data");fs::create_directories(data);
    for(const auto* folder:{L"memcards",L"savestates",L"cache",L"cheats",L"covers",L"gameicons",L"gamesettings",L"inputprofiles",L"patches",L"screenshots",L"shaders",L"subchannels",L"textures",L"videos"}){
        auto path=data/folder;if(!SafeTree(path))throw std::runtime_error("Linked user data");fs::create_directories(path);
    }
#ifdef PUBLIC_PLAYER
    if(!SafeTree(data/L"bios"))throw std::runtime_error("Linked BIOS data");fs::create_directories(data/L"bios");
#endif
    auto defaults=ReadText(version/L"defaults/settings.ini.template");ReplaceAll(defaults,"@BIOS_DIRECTORY@",Slash(BiosDirectory(root,version)));ReplaceAll(defaults,"@DATA_DIRECTORY@",Slash(data));
    WriteAtomic(data/L"settings.ini",defaults,true);
}
static std::string SessionSettings(const fs::path& root,const fs::path& version) {
    auto canonical=root/L"UserData/settings.ini",session=version/L"runtime/settings.ini";
    auto source=canonical;
    if(fs::exists(session)&&Plain(session,false)&&fs::last_write_time(session)>fs::last_write_time(canonical)) source=session;
    auto text=ReadText(source);std::istringstream lines(text);std::string line,section,result;auto data=root/L"UserData";std::set<std::string> seen;
    static const std::vector<std::pair<std::string,std::string>> folders={{"Cache","cache"},{"Cheats","cheats"},{"Covers","covers"},{"GameIcons","gameicons"},{"GameSettings","gamesettings"},{"InputProfiles","inputprofiles"},{"Patches","patches"},{"SaveStates","savestates"},{"Screenshots","screenshots"},{"Shaders","shaders"},{"Subchannels","subchannels"},{"Textures","textures"},{"Videos","videos"}};
    while(std::getline(lines,line)) {
        if(!line.empty()&&line.back()=='\r')line.pop_back();
        if(line.size()>2&&line.front()=='['&&line.back()==']')section=line.substr(1,line.size()-2);
        auto equal=line.find('=');std::string key=equal==std::string::npos?"":line.substr(0,equal);while(!key.empty()&&key.back()==' ')key.pop_back();
        seen.insert(section+"/"+key);
        if(section=="BIOS"&&key=="SearchDirectory")line="SearchDirectory = "+Slash(BiosDirectory(root,version));
        else if(section=="BIOS"&&key=="PathNTSCU")line=std::string("PathNTSCU = ")+BiosFilename();
        else if(section=="MemoryCards"&&key=="Directory")line="Directory = "+Slash(data/L"memcards");
        else if(section=="Folders"&&!key.empty()) {
            for(const auto& item:folders)if(key==item.first)line=key+" = "+Slash(data/Wide(item.second));
        }
        result+=line+"\n";
    }
    if(!seen.count("BIOS/SearchDirectory")||!seen.count("BIOS/PathNTSCU")){result+="\n[BIOS]\n";if(!seen.count("BIOS/SearchDirectory"))result+="SearchDirectory = "+Slash(BiosDirectory(root,version))+"\n";if(!seen.count("BIOS/PathNTSCU"))result+=std::string("PathNTSCU = ")+BiosFilename()+"\n";}
    if(!seen.count("MemoryCards/Directory"))result+="\n[MemoryCards]\nDirectory = "+Slash(data/L"memcards")+"\n";
    std::string missingFolders;for(const auto& item:folders)if(!seen.count("Folders/"+item.first))missingFolders+=item.first+" = "+Slash(data/Wide(item.second))+"\n";if(!missingFolders.empty())result+="\n[Folders]\n"+missingFolders;
    if(!seen.count("Main/SetupWizardIncomplete"))result+="\n[Main]\nSetupWizardIncomplete = false\n";
    return result;
}
static void Console(const std::string& text,bool error=false){auto handle=GetStdHandle(error?STD_ERROR_HANDLE:STD_OUTPUT_HANDLE);if(handle&&handle!=INVALID_HANDLE_VALUE){DWORD written;auto line=text+"\r\n";WriteFile(handle,line.data(),static_cast<DWORD>(line.size()),&written,nullptr);}}
struct Guard {HANDLE value=nullptr;~Guard(){if(value){ReleaseMutex(value);CloseHandle(value);}}};
static bool LockInstall(const fs::path& root,Guard& lock,std::wstring& error) {
    auto spelling=root.wstring();for(auto& ch:spelling)ch=static_cast<wchar_t>(towlower(ch));
    auto name=L"Local\\MassDriverPrivate."+Wide(HashText(Utf8(spelling)));lock.value=CreateMutexW(nullptr,TRUE,name.c_str());
    if(!lock.value||GetLastError()==ERROR_ALREADY_EXISTS){error=L"Mass Driver is already installing or running from this folder.";return false;}return true;
}
#ifndef PRIVATE_PLAY_LAUNCHER
static bool StartMenuShortcut(const fs::path& root){
    HRESULT initialized=CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);bool success=false;
    PWSTR programs=nullptr;IShellLinkW* link=nullptr;
    if(SUCCEEDED(SHGetKnownFolderPath(FOLDERID_Programs,KF_FLAG_CREATE,nullptr,&programs))){
        try{
#ifdef PUBLIC_PLAYER
            auto folder=NormalizeRoot(fs::path(programs)/L"Mass Driver");
#else
            auto folder=NormalizeRoot(fs::path(programs)/L"Mass Driver Private");
#endif
            fs::create_directories(folder);
            if(SUCCEEDED(CoCreateInstance(CLSID_ShellLink,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&link)))){
                link->SetPath((root/kPlayName).c_str());link->SetWorkingDirectory(root.c_str());
#ifdef PUBLIC_PLAYER
                link->SetDescription(L"Play Mass Driver");
#else
                link->SetDescription(L"Play Mass Driver (private local installation)");
#endif
                IPersistFile* persist=nullptr;if(SUCCEEDED(link->QueryInterface(IID_PPV_ARGS(&persist)))){success=SUCCEEDED(persist->Save((folder/L"Play Mass Driver.lnk").c_str(),TRUE));persist->Release();}link->Release();
            }
        }catch(...){}CoTaskMemFree(programs);
    }if(SUCCEEDED(initialized))CoUninitialize();return success;
}
static bool CleanupStage(const fs::path& root,const fs::path& stage,bool& owned,std::wstring& error){
    if(!owned)return true;
    if(stage.parent_path()!=root||stage.filename().wstring().rfind(L".install-",0)!=0){error+=L" Temporary cleanup path could not be verified.";return false;}
    std::error_code failure;
    for(int attempt=0;attempt<3;++attempt){failure.clear();fs::remove_all(stage,failure);if(!failure&&!fs::exists(stage)){owned=false;return true;}Sleep(50);}
    error+=L" Windows could not remove the temporary folder. Close applications using it, then remove this folder: "+stage.wstring();return false;
}
static bool WriteLauncher(const fs::path& root,std::wstring& error) {
    auto module=GetModuleHandleW(nullptr);auto found=FindResourceW(module,MAKEINTRESOURCEW(201),RT_RCDATA);auto handle=found?LoadResource(module,found):nullptr;
    auto data=handle?static_cast<const char*>(LockResource(handle)):nullptr;auto size=found?SizeofResource(module,found):0;
    if(!data||size!=PRIVATE_PLAY_SIZE||HashText(std::string(data,size))!=PRIVATE_PLAY_SHA256){error=L"The included Play launcher is damaged.";return false;}
    try{WriteAtomic(root/kPlayName,std::string(data,size));return true;}catch(...){error=L"The Play launcher could not be installed.";return false;}
}
static int Install(const fs::path& root,bool cancelBefore,bool cancelDuring,std::wstring& error,bool shortcut=false) {
    Guard lock;if(!LockInstall(root,lock,error))return 8;
    fs::path stage;bool owned=false;
    try {
        if(!SafeTree(root)||root==gSelf.parent_path()){error=L"Choose a separate writable installation folder.";return 20;}
        if(!CheckLogical(gArchive,error))return 10;
        auto final=VersionPath(root,gArchive.identity);
        // This upstream Qt build fails to initialize at some long installation paths.
        // Keep its version root compact and below the empirically failing range.
        if(final.wstring().size()>120){error=L"This location is too long for the included game runtime. Choose a shorter installation location.";return 20;}
        fs::create_directories(root/L"v");if(!SafeTree(root/L"v"))throw std::runtime_error("Linked install");
        bool ready=fs::exists(final)&&mdarchive::Verify(final,gArchive,error);
        if(!ready) {
            ULARGE_INTEGER free{};if(!GetDiskFreeSpaceExW(root.c_str(),&free,nullptr,nullptr)||free.QuadPart<gArchive.totalSize+64ULL*1024*1024){error=L"There is not enough free space to install Mass Driver.";return 31;}
            stage=root/(L".install-"+Guid());if(!fs::create_directory(stage))throw std::runtime_error("Cannot stage");owned=true;
            if(cancelBefore)gCancel.store(true);
            auto progress=[&](uint64_t done,uint64_t total){if(cancelDuring&&done>0)gCancel.store(true);if(gWindow)PostMessageW(gWindow,WM_PROGRESS,total?static_cast<WPARAM>(done*1000/total):0,0);};
            if(!mdarchive::Extract(gSelf,stage,gArchive,&gCancel,progress,error)){
                CleanupStage(root,stage,owned,error);return gCancel.load()?61:10;
            }
            if(gCancel.load()){error=L"Installation cancelled. Select Install to try again.";CleanupStage(root,stage,owned,error);return 61;}
            WriteAtomic(stage/L"content_manifest.txt",LogicalManifest(gArchive));
            if(fs::exists(final)){
                if(!Plain(final,true))throw std::runtime_error("Linked existing install");
                auto preserved=final.parent_path()/(final.filename().wstring()+L".preserved-"+Guid());fs::rename(final,preserved);
            }
            fs::rename(stage,final);owned=false;
        } else WriteAtomic(final/L"content_manifest.txt",LogicalManifest(gArchive));
        SeedData(root,final);
        if(!WriteLauncher(root,error))return 20;
        WriteAtomic(root/L"installation.txt",gArchive.identity+"\n");
        if(shortcut&&!StartMenuShortcut(root))error=L"Mass Driver is installed. The Start menu shortcut could not be created; use Open folder, then Play Mass Driver.exe.";
        return 0;
    }catch(...){error=L"Windows could not finish the installation. Your saved games were preserved.";CleanupStage(root,stage,owned,error);return 20;}
}
#endif
static std::wstring Quote(const std::wstring& value){std::wstring result=L"\"";size_t slashes=0;for(auto ch:value){if(ch==L'\\'){++slashes;continue;}if(ch==L'\"'){result.append(slashes*2+1,L'\\');result+=ch;slashes=0;continue;}result.append(slashes,L'\\');slashes=0;result+=ch;}result.append(slashes*2,L'\\');return result+L"\"";}
#ifdef PUBLIC_PLAYER
#include "public_player.h"
#endif
static int Play(const fs::path& root,bool dryRun,std::wstring& error) {
    Guard lock;if(!LockInstall(root,lock,error))return 8;
    fs::path version;mdarchive::Info info;if(!LoadInstalled(root,version,info,error))return 20;
    try{
#ifdef PUBLIC_PLAYER
        auto setup=PublicSetup(root,version,{},{},!dryRun,false,false,error);if(setup)return setup;
        auto prerequisite=PublicPrerequisites(root,!dryRun,error);if(prerequisite)return prerequisite;
#endif
        SeedData(root,version);auto settings=SessionSettings(root,version);WriteAtomic(version/L"runtime/settings.ini",settings);
#ifdef PUBLIC_PLAYER
        auto runtime=version/kRuntime,cue=PublicGame(root)/L"Xenogears_Mass_Driver.cue";
#else
        auto runtime=version/kRuntime,cue=version/kCue;
#endif
        std::wstring command=Quote(runtime.wstring())+L" -batch -nogui -fullscreen -fastboot -- "+Quote(cue.wstring());
        if(dryRun){Console("LAUNCH_EXE="+Slash(runtime));Console("LAUNCH_COMMAND="+Utf8(command));Console("GAME_CUE="+Slash(cue));Console("USER_DATA="+Slash(root/L"UserData"));Console("RUNTIME_LAUNCHED=false");return 0;}
        std::vector<wchar_t> writable(command.begin(),command.end());writable.push_back(0);
        STARTUPINFOW startup{sizeof(startup)};PROCESS_INFORMATION process{};
        if(!CreateProcessW(runtime.c_str(),writable.data(),nullptr,nullptr,FALSE,0,nullptr,runtime.parent_path().c_str(),&startup,&process)){error=L"The included game runtime could not start.";return 40;}
        CloseHandle(process.hThread);WaitForSingleObject(process.hProcess,INFINITE);DWORD exitCode=0;GetExitCodeProcess(process.hProcess,&exitCode);CloseHandle(process.hProcess);
        if(Plain(version/L"runtime/settings.ini",false))WriteAtomic(root/L"UserData/settings.ini",ReadText(version/L"runtime/settings.ini"));
        if(exitCode!=0){std::wostringstream code;code<<std::hex<<std::uppercase<<exitCode;error=L"The game runtime exited unexpectedly (Windows code 0x"+code.str()+L"). Your memory cards remain in the UserData folder.";return 40;}return 0;
    }catch(...){error=L"The game could not prepare its private settings. Saved games were preserved.";return 20;}
}
static void ChooseLocation(HWND owner) {
    IFileDialog* dialog=nullptr;HRESULT initialized=CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);
    if(SUCCEEDED(CoCreateInstance(CLSID_FileOpenDialog,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&dialog)))){
        DWORD options=0;dialog->GetOptions(&options);dialog->SetOptions(options|FOS_PICKFOLDERS|FOS_FORCEFILESYSTEM|FOS_PATHMUSTEXIST|FOS_DONTADDTORECENT);dialog->SetTitle(L"Choose where to install Mass Driver");
        if(SUCCEEDED(dialog->Show(owner))){IShellItem* item=nullptr;PWSTR selected=nullptr;if(SUCCEEDED(dialog->GetResult(&item))){if(SUCCEEDED(item->GetDisplayName(SIGDN_FILESYSPATH,&selected))){try{gRoot=NormalizeRoot(fs::path(selected)/kInstallDirectory);SetWindowTextW(gLocation,gRoot.c_str());fs::path version;mdarchive::Info info;std::wstring ignored;bool ready=LoadInstalled(gRoot,version,info,ignored,false);EnableWindow(gPlay,ready);EnableWindow(gOpenFolder,ready);SetWindowTextW(gStatus,ready?L"Mass Driver is installed here. Select Play.":L"Location selected. Select Install.");}catch(...){MessageBoxW(owner,L"Choose an ordinary writable folder without links or reserved names.",kTitle,MB_OK|MB_ICONERROR);}CoTaskMemFree(selected);}item->Release();}}dialog->Release();
    }if(SUCCEEDED(initialized))CoUninitialize();
}
static LRESULT CALLBACK WindowProc(HWND window,UINT message,WPARAM word,LPARAM value){
    switch(message){
    case WM_CREATE:{gWindow=window;auto font=GetStockObject(DEFAULT_GUI_FONT);auto child=[&](const wchar_t* cls,const wchar_t* text,DWORD style,int x,int y,int w,int h,int id){auto control=CreateWindowW(cls,text,WS_CHILD|WS_VISIBLE|style,x,y,w,h,window,reinterpret_cast<HMENU>(static_cast<INT_PTR>(id)),GetModuleHandleW(nullptr),nullptr);SendMessageW(control,WM_SETFONT,reinterpret_cast<WPARAM>(font),TRUE);return control;};
        child(L"STATIC",L"Mass Driver",SS_LEFT,24,20,600,30,0);
#ifdef PUBLIC_PLAYER
        child(L"STATIC",L"Install, then Play. First run asks for your own USA Disc 2 BIN and PlayStation BIOS.",SS_LEFT,24,58,645,40,0);
#else
        child(L"STATIC",L"Install once, then select Play. Your saved games stay in your private UserData folder.",SS_LEFT,24,58,600,40,0);
#endif
        gLocation=child(L"STATIC",gRoot.c_str(),SS_PATHELLIPSIS,24,108,510,36,0);child(L"BUTTON",L"Change location...",WS_TABSTOP,540,106,130,30,100);
        gInstall=child(L"BUTTON",L"Install",WS_TABSTOP|BS_DEFPUSHBUTTON,24,160,170,40,101);gCancelButton=child(L"BUTTON",L"Cancel",WS_TABSTOP,210,160,130,40,102);EnableWindow(gCancelButton,FALSE);
        gPlay=child(L"BUTTON",L"Play",WS_TABSTOP,356,160,170,40,103);fs::path version;mdarchive::Info info;std::wstring ignored;EnableWindow(gPlay,LoadInstalled(gRoot,version,info,ignored,false));
        gOpenFolder=child(L"BUTTON",L"Open folder",WS_TABSTOP,542,160,130,40,104);EnableWindow(gOpenFolder,IsWindowEnabled(gPlay));
        gProgress=child(PROGRESS_CLASSW,L"",0,24,220,645,24,0);SendMessageW(gProgress,PBM_SETRANGE32,0,1000);
#ifdef PUBLIC_PLAYER
        gStatus=child(L"STATIC",L"No game image or BIOS is included. Play guides you through first-time setup.",SS_LEFT,24,264,645,56,0);
        child(L"BUTTON",L"Help / BIOS",WS_TABSTOP,540,324,130,28,106);
        gShortcut=child(L"BUTTON",L"Add a Start menu shortcut",BS_AUTOCHECKBOX|WS_TABSTOP,24,326,490,24,105);
#else
        gStatus=child(L"STATIC",L"Ready to install. No original disc or emulator setup is needed for this private package.",SS_LEFT,24,264,645,56,0);
        gShortcut=child(L"BUTTON",L"Add a Start menu shortcut",BS_AUTOCHECKBOX|WS_TABSTOP,24,326,600,24,105);
#endif
        SendMessageW(gShortcut,BM_SETCHECK,BST_CHECKED,0);return 0;}
    case WM_COMMAND:
#ifdef PUBLIC_PLAYER
        if(LOWORD(word)==106&&!gWorking.load()){
            MessageBoxW(window,L"First-time setup needs two files you supply:\n\n1. An untouched USA Xenogears Disc 2 BIN dumped from your own disc. Patched images, Disc 1 and other regions are unsupported.\n\n2. A 512 KB NTSC-U PlayStation BIOS dumped from your own console (such as SCPH-1001, 5501, 7001 or 101). If you do not have a dump, cancel and dump your console's firmware; do not download someone else's BIOS.\n\nInstall, then select Play. Explorer asks for the files. Originals remain unchanged. The included README_PLAYER.md has full directions and official documentation links.\n\nIf needed, Play offers Microsoft's official signed x64 runtime installer. No game, BIOS or Microsoft DLL is included in this download.",kTitle,MB_OK|MB_ICONINFORMATION);return 0;
        }
#endif
        if(LOWORD(word)==100&&!gWorking.load()){ChooseLocation(window);return 0;}
        if(LOWORD(word)==104&&!gWorking.load()){ShellExecuteW(window,L"open",gRoot.c_str(),nullptr,nullptr,SW_SHOWNORMAL);return 0;}
        if(LOWORD(word)==102){gCancel.store(true);EnableWindow(gCancelButton,FALSE);SetWindowTextW(gStatus,L"Cancelling safely...");return 0;}
        if(LOWORD(word)==103&&!gWorking.load()){
            gWorking.store(true);EnableWindow(gInstall,FALSE);EnableWindow(gPlay,FALSE);EnableWindow(gOpenFolder,FALSE);EnableWindow(gShortcut,FALSE);EnableWindow(GetDlgItem(window,100),FALSE);SetWindowTextW(gStatus,L"Starting Mass Driver...");
            std::thread([]{std::wstring error;int code=Play(gRoot,false,error);PostMessageW(gWindow,WM_FINISHED,code,reinterpret_cast<LPARAM>(new std::wstring(error)));}).detach();return 0;
        }
#ifndef PRIVATE_PLAY_LAUNCHER
        if(LOWORD(word)==101&&!gWorking.load()){
            bool shortcut=SendMessageW(gShortcut,BM_GETCHECK,0,0)==BST_CHECKED;
            gCancel.store(false);gWorking.store(true);EnableWindow(gInstall,FALSE);EnableWindow(gPlay,FALSE);EnableWindow(gOpenFolder,FALSE);EnableWindow(gShortcut,FALSE);EnableWindow(gCancelButton,TRUE);EnableWindow(GetDlgItem(window,100),FALSE);SetWindowTextW(gStatus,L"Installing Mass Driver...");
            std::thread([shortcut]{std::wstring error;int code=Install(gRoot,false,false,error,shortcut);PostMessageW(gWindow,WM_FINISHED,code,reinterpret_cast<LPARAM>(new std::wstring(error)));}).detach();return 0;
        }
#endif
        break;
    case WM_PROGRESS:SendMessageW(gProgress,PBM_SETPOS,word,0);return 0;
    case WM_FINISHED:{auto error=reinterpret_cast<std::wstring*>(value);gWorking.store(false);EnableWindow(gInstall,TRUE);EnableWindow(gShortcut,TRUE);EnableWindow(GetDlgItem(window,100),TRUE);EnableWindow(gCancelButton,FALSE);fs::path version;mdarchive::Info info;std::wstring ignored;EnableWindow(gPlay,LoadInstalled(gRoot,version,info,ignored,false));EnableWindow(gOpenFolder,IsWindowEnabled(gPlay));SetWindowTextW(gStatus,word==0&&error->empty()?L"Mass Driver is ready. Select Play, or use Play Mass Driver from the Start menu later.":error->c_str());if(word!=0&&word!=61)MessageBoxW(window,error->c_str(),kTitle,MB_OK|MB_ICONERROR);delete error;return 0;}
    case WM_CLOSE:if(gWorking.load()){MessageBoxW(window,L"Close the game or select Cancel and wait for installation to stop first.",kTitle,MB_OK);return 0;}DestroyWindow(window);return 0;
    case WM_DESTROY:PostQuitMessage(0);return 0;
    }return DefWindowProcW(window,message,word,value);
}
int WINAPI wWinMain(HINSTANCE instance,HINSTANCE,PWSTR,int show){
    try{
        wchar_t self[32768]{};auto count=GetModuleFileNameW(nullptr,self,32768);if(!count||count>=32768)return 60;gSelf=fs::path(self);gRoot=NormalizeRoot(DefaultRoot());
        int argc=0;auto argv=CommandLineToArgvW(GetCommandLineW(),&argc);bool headless=argv&&argc>1&&std::wstring(argv[1])==L"--headless";std::wstring action,error;bool before=false,during=false;bool rootSeen=false;
#ifdef PUBLIC_PLAYER
        fs::path source,bios,prerequisiteFile;
#endif
        if(headless){for(int i=2;i<argc;++i){std::wstring argument=argv[i];
            if(argument==L"--root"&&i+1<argc&&!rootSeen){gRoot=NormalizeRoot(argv[++i]);rootSeen=true;}
            else if(argument==L"--cancel-before"&&!before)before=true;
            else if(argument==L"--cancel-during"&&!during)during=true;
            else if(action.empty()&&(argument==L"--inspect"||argument==L"--install"||argument==L"--check-installed"||argument==L"--launch-check"))action=argument;
#ifdef PUBLIC_PLAYER
            else if(action.empty()&&(argument==L"--setup"||argument==L"--check-prerequisites"||argument==L"--verify-prerequisite"||argument==L"--download-prerequisite"))action=argument;
            else if(argument==L"--source"&&i+1<argc&&source.empty())source=fs::absolute(argv[++i]);
            else if(argument==L"--bios"&&i+1<argc&&bios.empty())bios=fs::absolute(argv[++i]);
            else if(argument==L"--file"&&i+1<argc&&prerequisiteFile.empty())prerequisiteFile=fs::absolute(argv[++i]);
#endif
            else{LocalFree(argv);return 2;}
        }}
#ifdef PRIVATE_PLAY_LAUNCHER
        if(!rootSeen)gRoot=NormalizeRoot(gSelf.parent_path());
#else
        gHasArchive=mdarchive::Inspect(gSelf,gArchive,error)&&CheckLogical(gArchive,error);
        if(!gHasArchive){if(headless)Console("ERROR="+Utf8(error),true);else MessageBoxW(nullptr,error.c_str(),kTitle,MB_OK|MB_ICONERROR);if(argv)LocalFree(argv);return 10;}
#endif
        if(argv)LocalFree(argv);
        if(headless){int code=2;
            if(action==L"--launch-check")code=Play(gRoot,true,error);
            else if(action==L"--check-installed"){fs::path version;mdarchive::Info info;code=LoadInstalled(gRoot,version,info,error)?0:20;if(code==0)Console("INSTALLED_OK="+Slash(version));}
#ifdef PUBLIC_PLAYER
            else if(action==L"--setup"){
                Guard lock;fs::path version;mdarchive::Info info;
                if(!LockInstall(gRoot,lock,error))code=8;
                else if(!LoadInstalled(gRoot,version,info,error))code=20;
                else{SeedData(gRoot,version);code=PublicSetup(gRoot,version,source,bios,false,before,during,error);}
            }
            else if(action==L"--check-prerequisites"){code=PublicPrerequisites(gRoot,false,error);if(code==0)Console("MICROSOFT_VC_RUNTIME_READY=true");}
            else if(action==L"--verify-prerequisite"&&!prerequisiteFile.empty()){code=PublicVerifyMicrosoft(prerequisiteFile,error)?0:46;if(code==0)Console("MICROSOFT_SIGNATURE_VALID=true");}
            else if(action==L"--download-prerequisite"&&!prerequisiteFile.empty()){code=PublicDownloadMicrosoft(prerequisiteFile,error)?0:46;if(code==0)Console("MICROSOFT_SIGNED_DOWNLOAD="+Slash(prerequisiteFile));}
#endif
#ifndef PRIVATE_PLAY_LAUNCHER
            else if(action==L"--inspect"){Console("ARCHIVE_OK="+gArchive.identity);Console("CONTENT_BYTES="+std::to_string(gArchive.totalSize));Console("CONTENT_FILES="+std::to_string(gArchive.files.size()));code=0;}
            else if(action==L"--install"){code=Install(gRoot,before,during,error);if(code==0)Console("INSTALL_SUCCESS="+Slash(gRoot));}
#endif
            if(code!=0)Console("ERROR="+std::to_string(code)+":"+Utf8(error),true);return code;
        }
#ifdef PRIVATE_PLAY_LAUNCHER
        int code=Play(gRoot,false,error);
#ifdef PUBLIC_PLAYER
        if(code&&code!=61)MessageBoxW(nullptr,error.c_str(),kTitle,MB_OK|MB_ICONERROR);
#else
        if(code)MessageBoxW(nullptr,error.c_str(),kTitle,MB_OK|MB_ICONERROR);
#endif
        return code;
#else
        INITCOMMONCONTROLSEX controls{sizeof(controls),ICC_PROGRESS_CLASS};InitCommonControlsEx(&controls);
        WNDCLASSW cls{};cls.lpfnWndProc=WindowProc;cls.hInstance=instance;cls.hCursor=LoadCursorW(nullptr,IDC_ARROW);cls.hIcon=LoadIconW(nullptr,IDI_APPLICATION);cls.hbrBackground=reinterpret_cast<HBRUSH>(COLOR_WINDOW+1);cls.lpszClassName=L"MassDriverPrivateInstaller";if(!RegisterClassW(&cls))return 60;
        auto window=CreateWindowW(cls.lpszClassName,kTitle,WS_OVERLAPPED|WS_CAPTION|WS_SYSMENU|WS_MINIMIZEBOX,CW_USEDEFAULT,CW_USEDEFAULT,716,420,nullptr,nullptr,instance,nullptr);if(!window)return 60;
        ShowWindow(window,show);UpdateWindow(window);MSG message{};while(GetMessageW(&message,nullptr,0,0)>0){if(!IsDialogMessageW(window,&message)){TranslateMessage(&message);DispatchMessageW(&message);}}return static_cast<int>(message.wParam);
#endif
    }catch(...){return 60;}
}
