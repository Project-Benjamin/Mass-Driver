#pragma once
// Included only by PUBLIC_PLAYER, after the installer's common checked file and
// process helpers. Private builds do not compile this code or need networking.
#include <winhttp.h>
#include <wintrust.h>
#include <softpub.h>
#include <wincrypt.h>

static fs::path PublicGame(const fs::path& root) {return root/L"Game"/Wide(std::string(PUBLIC_GAME_SHA256).substr(0,16));}
static fs::path PublicBios(const fs::path& root) {return root/L"UserData/bios/user-bios.bin";}
static bool PublicHashMatches(const fs::path& path,uint64_t expectedSize,const char* expectedHash) {
    std::string hash;uint64_t size=0;std::wstring ignored;
    return Plain(path,false)&&mdarchive::HashFile(path,hash,size,ignored)&&size==expectedSize&&hash==expectedHash;
}
static bool PublicGameReady(const fs::path& root) {
    auto game=PublicGame(root);
    return SafeTree(game)&&PublicHashMatches(game/L"Xenogears_Mass_Driver.bin",PUBLIC_GAME_SIZE,PUBLIC_GAME_SHA256)&&
        PublicHashMatches(game/L"Xenogears_Mass_Driver.cue",PUBLIC_CUE_SIZE,PUBLIC_CUE_SHA256);
}
static std::string PublicMD5(const std::string& data) {
    BCRYPT_ALG_HANDLE algorithm=nullptr;BCRYPT_HASH_HANDLE hash=nullptr;unsigned char bytes[16]{};
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_MD5_ALGORITHM,nullptr,0)<0)throw std::runtime_error("BIOS identity");
    auto status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(status>=0)status=BCryptHashData(hash,reinterpret_cast<PUCHAR>(const_cast<char*>(data.data())),static_cast<ULONG>(data.size()),0);
    if(status>=0)status=BCryptFinishHash(hash,bytes,sizeof(bytes),0);
    if(hash)BCryptDestroyHash(hash);BCryptCloseAlgorithmProvider(algorithm,0);
    if(status<0)throw std::runtime_error("BIOS identity");
    std::string result;for(auto b:bytes){result+="0123456789abcdef"[b>>4];result+="0123456789abcdef"[b&15];}return result;
}
static bool PublicReadBios(const fs::path& path,std::string& data,std::wstring& error) {
    try {
        if(!Plain(path,false)||fs::file_size(path)!=524288)throw std::runtime_error("BIOS size");
        data=ReadText(path,524288);auto md5=PublicMD5(data);
        for(const auto* allowed:PUBLIC_BIOS_MD5S)if(md5==allowed)return true;
    }catch(...){}
    error=L"Choose a supported 512 KB USA (NTSC-U) PlayStation BIOS dumped from your own console. This file is not recognized. If you do not have a dump, cancel and read Help / BIOS.";return false;
}
static bool PublicBiosReady(const fs::path& root) {std::string data;std::wstring ignored;return SafeTree(PublicBios(root).parent_path())&&PublicReadBios(PublicBios(root),data,ignored);}
static bool PublicPickFile(const wchar_t* title,const wchar_t* filter,fs::path& path) {
    bool selected=false;HRESULT initialized=CoInitializeEx(nullptr,COINIT_APARTMENTTHREADED);IFileOpenDialog* dialog=nullptr;
    if(SUCCEEDED(CoCreateInstance(CLSID_FileOpenDialog,nullptr,CLSCTX_INPROC_SERVER,IID_PPV_ARGS(&dialog)))){
        DWORD options=0;dialog->GetOptions(&options);dialog->SetOptions(options|FOS_FORCEFILESYSTEM|FOS_FILEMUSTEXIST|FOS_PATHMUSTEXIST|FOS_DONTADDTORECENT);
        COMDLG_FILTERSPEC types[]={{L"BIN files",filter},{L"All files",L"*.*"}};dialog->SetFileTypes(2,types);dialog->SetTitle(title);
        if(SUCCEEDED(dialog->Show(gWindow))){IShellItem* item=nullptr;PWSTR name=nullptr;
            if(SUCCEEDED(dialog->GetResult(&item))){if(SUCCEEDED(item->GetDisplayName(SIGDN_FILESYSPATH,&name))){path=name;CoTaskMemFree(name);selected=true;}item->Release();}}
        dialog->Release();
    }if(SUCCEEDED(initialized))CoUninitialize();return selected;
}
static int PublicRunPatcher(const fs::path& version,const fs::path& source,const fs::path& game,const fs::path& log,bool cancel,std::wstring& error) {
    auto exe=version/L"patcher/Xenogears_Mass_Driver.exe";
    std::wstring command=Quote(exe.wstring())+L" --headless --source "+Quote(source.wstring())+L" --output "+Quote(game.wstring());
    if(cancel)command+=L" --cancel-before-decode";
    if(!SafeTree(log.parent_path())){error=L"The game log location is linked to another folder.";return 20;}
    SECURITY_ATTRIBUTES security{sizeof(security),nullptr,TRUE};
    HANDLE output=CreateFileW(log.c_str(),GENERIC_WRITE,FILE_SHARE_READ,&security,CREATE_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    HANDLE input=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&security,OPEN_EXISTING,0,nullptr);
    if(output==INVALID_HANDLE_VALUE||input==INVALID_HANDLE_VALUE){if(output!=INVALID_HANDLE_VALUE)CloseHandle(output);if(input!=INVALID_HANDLE_VALUE)CloseHandle(input);error=L"The game build log could not be created.";return 20;}
    STARTUPINFOW startup{sizeof(startup)};startup.dwFlags=STARTF_USESTDHANDLES|STARTF_USESHOWWINDOW;startup.wShowWindow=SW_HIDE;
    startup.hStdOutput=output;startup.hStdError=output;startup.hStdInput=input;PROCESS_INFORMATION process{};
    std::vector<wchar_t> writable(command.begin(),command.end());writable.push_back(0);
    BOOL created=CreateProcessW(exe.c_str(),writable.data(),nullptr,nullptr,TRUE,CREATE_NO_WINDOW,nullptr,exe.parent_path().c_str(),&startup,&process);
    CloseHandle(input);CloseHandle(output);
    if(!created){error=L"The included game builder could not start. Run the installer again to repair the program.";return 20;}
    CloseHandle(process.hThread);WaitForSingleObject(process.hProcess,INFINITE);DWORD code=0;GetExitCodeProcess(process.hProcess,&code);CloseHandle(process.hProcess);
    if(code==0)return 0;
    error=code==61?L"Setup cancelled. Your source files and saved games were preserved. Select Play to try again.":
        L"Mass Driver could not build the game from this file. Choose an untouched USA Disc 2 BIN; patched images, Disc 1 and other regions are unsupported. Your source file and saved games were preserved.";
    return static_cast<int>(code);
}
static int PublicSetup(const fs::path& root,const fs::path& version,fs::path source,fs::path bios,bool interactive,bool cancelBefore,bool cancelDecode,std::wstring& error) {
    try {
        bool readyGame=PublicGameReady(root),readyBios=PublicBiosReady(root);std::string biosData;
        // Collect and validate both inputs before copying or generating anything.
        if(!readyGame&&source.empty()){
            if(!interactive){error=L"First-time setup needs your untouched USA Xenogears Disc 2 BIN. Use Play, or --setup --source <BIN> --bios <BIOS>.";return 41;}
            MessageBoxW(gWindow,L"Select the untouched USA Xenogears Disc 2 BIN dumped from your own disc. Mass Driver builds a separate game copy; the original stays unchanged. You will also need a BIOS dump from your own PlayStation.",kTitle,MB_OK|MB_ICONINFORMATION);
            if(!PublicPickFile(L"Select your untouched USA Xenogears Disc 2 BIN",L"*.bin",source)){error=L"Setup cancelled. Select Play when your disc and BIOS are ready.";return 61;}
        }
        if(!source.empty()&&!PublicHashMatches(source,PUBLIC_SOURCE_SIZE,PUBLIC_SOURCE_SHA256)){error=L"This is not the supported untouched USA Xenogears Disc 2 BIN. Patched images, Disc 1 and other regions cannot be used. Your files were not changed.";return 42;}
        if(!readyBios&&bios.empty()){
            if(!interactive){error=L"First-time setup needs a supported BIOS dumped from your own USA PlayStation. Use Play and choose the BIOS, or read Help / BIOS.";return 43;}
            MessageBoxW(gWindow,L"Select a 512 KB NTSC-U PlayStation BIOS dumped from your own console. If you do not have one, cancel and read Help / BIOS. A BIOS is not included and should not be downloaded from someone else.",kTitle,MB_OK|MB_ICONINFORMATION);
            if(!PublicPickFile(L"Select the BIOS dumped from your USA PlayStation",L"*.bin",bios)){error=L"Setup cancelled. Select Play when your BIOS dump is ready.";return 61;}
        }
        if(!bios.empty()&&!PublicReadBios(bios,biosData,error))return 44;
        if(cancelBefore){error=L"Setup cancelled before any input was copied or game was built.";return 61;}
        if(!readyGame){
            auto game=PublicGame(root);if(!SafeTree(game.parent_path()))throw std::runtime_error("Linked game root");fs::create_directories(game.parent_path());
            // Preserve a damaged prior generated copy rather than overwriting it.
            if(fs::exists(game)){if(!Plain(game,true))throw std::runtime_error("Linked game");fs::rename(game,game.parent_path()/(game.filename().wstring()+L".preserved-"+Guid()));}
            auto code=PublicRunPatcher(version,source,game,root/L"UserData/game-build.log",cancelDecode,error);if(code)return code;
            if(!PublicGameReady(root)){error=L"The generated game failed its final identity check. Your original disc and saved games were preserved.";return 45;}
        }
        if(!biosData.empty()){
            auto target=PublicBios(root);
            if(!SafeTree(target.parent_path()))throw std::runtime_error("Linked BIOS folder");fs::create_directories(target.parent_path());
            if(fs::exists(target)&&(!Plain(target,false)||ReadText(target,524288)!=biosData)){
                if(!Plain(target,false))throw std::runtime_error("Linked BIOS");fs::rename(target,target.parent_path()/(L"user-bios.bin.preserved-"+Guid()));
            }
            WriteAtomic(target,biosData);
        }
        if(!PublicGameReady(root)||!PublicBiosReady(root)){error=L"First-time setup is incomplete. Select Play to finish it.";return 45;}
        Console("GAME_READY="+Slash(PublicGame(root)));Console("BIOS_READY="+Slash(PublicBios(root)));return 0;
    }catch(...){error=L"Windows could not finish first-time setup. Your original files and saved games were preserved. Select Play to retry.";return 20;}
}
static std::vector<std::wstring> PublicMissingVC() {
    wchar_t system[32768]{};auto count=GetSystemDirectoryW(system,32768);std::vector<std::wstring> missing;
    for(const auto* name:PUBLIC_REQUIRED_VC_DLLS){
        auto path=fs::path(system)/name;auto module=count&&count<32768?LoadLibraryExW(path.c_str(),nullptr,LOAD_LIBRARY_SEARCH_SYSTEM32):nullptr;
        if(module)FreeLibrary(module);else missing.emplace_back(name);
    }return missing;
}
static bool PublicVerifyMicrosoft(const fs::path& file,std::wstring& error) {
    if(!Plain(file,false)){error=L"The Microsoft runtime installer is missing or linked.";return false;}
    WINTRUST_FILE_INFO input{sizeof(input)};input.pcwszFilePath=file.c_str();GUID action=WINTRUST_ACTION_GENERIC_VERIFY_V2;
    WINTRUST_DATA trust{sizeof(trust)};trust.dwUIChoice=WTD_UI_NONE;trust.fdwRevocationChecks=WTD_REVOKE_WHOLECHAIN;
    trust.dwUnionChoice=WTD_CHOICE_FILE;trust.pFile=&input;trust.dwStateAction=WTD_STATEACTION_VERIFY;trust.dwProvFlags=WTD_REVOCATION_CHECK_CHAIN_EXCLUDE_ROOT;
    auto status=WinVerifyTrust(nullptr,&action,&trust);bool valid=false;
    if(status==ERROR_SUCCESS){
        auto provider=WTHelperProvDataFromStateData(trust.hWVTStateData);auto signer=provider?WTHelperGetProvSignerFromChain(provider,0,FALSE,0):nullptr;
        if(signer&&signer->csCertChain){wchar_t organization[256]{};
            auto size=CertGetNameStringW(signer->pasCertChain[0].pCert,CERT_NAME_ATTR_TYPE,0,const_cast<char*>(szOID_ORGANIZATION_NAME),organization,256);
            valid=size>1&&std::wstring(organization)==L"Microsoft Corporation";
        }
    }
    trust.dwStateAction=WTD_STATEACTION_CLOSE;WinVerifyTrust(nullptr,&action,&trust);
    if(!valid)error=L"The runtime download does not have a valid Microsoft Corporation signature. It will not be opened. Retry Play or obtain the runtime from Microsoft's official website.";
    return valid;
}
struct PublicInternet {HINTERNET value=nullptr;~PublicInternet(){if(value)WinHttpCloseHandle(value);}};
static bool PublicDownloadMicrosoft(const fs::path& target,std::wstring& error) {
    HANDLE file=INVALID_HANDLE_VALUE;bool owned=false;
    try {
        if(fs::exists(target)||!SafeTree(target.parent_path()))throw std::runtime_error("Download target");
        fs::create_directories(target.parent_path());
        PublicInternet session{WinHttpOpen(L"MassDriver/1.7.6",WINHTTP_ACCESS_TYPE_AUTOMATIC_PROXY,WINHTTP_NO_PROXY_NAME,WINHTTP_NO_PROXY_BYPASS,0)};
        if(!session.value)throw std::runtime_error("Network session");WinHttpSetTimeouts(session.value,30000,30000,30000,30000);
        PublicInternet connection{WinHttpConnect(session.value,L"aka.ms",INTERNET_DEFAULT_HTTPS_PORT,0)};
        PublicInternet request{connection.value?WinHttpOpenRequest(connection.value,L"GET",L"/vs/17/release/vc_redist.x64.exe",nullptr,WINHTTP_NO_REFERER,WINHTTP_DEFAULT_ACCEPT_TYPES,WINHTTP_FLAG_SECURE):nullptr};
        if(!request.value)throw std::runtime_error("Network request");DWORD policy=WINHTTP_OPTION_REDIRECT_POLICY_DISALLOW_HTTPS_TO_HTTP;
        if(!WinHttpSetOption(request.value,WINHTTP_OPTION_REDIRECT_POLICY,&policy,sizeof(policy))||
           !WinHttpSendRequest(request.value,WINHTTP_NO_ADDITIONAL_HEADERS,0,WINHTTP_NO_REQUEST_DATA,0,0,0)||!WinHttpReceiveResponse(request.value,nullptr))throw std::runtime_error("HTTPS download");
        DWORD status=0,statusSize=sizeof(status);if(!WinHttpQueryHeaders(request.value,WINHTTP_QUERY_STATUS_CODE|WINHTTP_QUERY_FLAG_NUMBER,WINHTTP_HEADER_NAME_BY_INDEX,&status,&statusSize,WINHTTP_NO_HEADER_INDEX)||status!=200)throw std::runtime_error("Download status");
        DWORD urlSize=0;WinHttpQueryOption(request.value,WINHTTP_OPTION_URL,nullptr,&urlSize);std::vector<wchar_t> url(urlSize/sizeof(wchar_t)+1);
        if(!WinHttpQueryOption(request.value,WINHTTP_OPTION_URL,url.data(),&urlSize))throw std::runtime_error("Download URL");
        URL_COMPONENTS parts{sizeof(parts)};parts.dwHostNameLength=static_cast<DWORD>(-1);
        if(!WinHttpCrackUrl(url.data(),0,0,&parts)||parts.nScheme!=INTERNET_SCHEME_HTTPS)throw std::runtime_error("Download scheme");
        std::wstring host(parts.lpszHostName,parts.dwHostNameLength);for(auto& c:host)c=static_cast<wchar_t>(towlower(c));
        if(host!=L"aka.ms"&&host!=L"microsoft.com"&&(host.size()<14||host.substr(host.size()-14)!=L".microsoft.com"))throw std::runtime_error("Download host");
        file=CreateFileW(target.c_str(),GENERIC_WRITE,0,nullptr,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,nullptr);if(file==INVALID_HANDLE_VALUE)throw std::runtime_error("Download file");owned=true;
        uint64_t total=0;char buffer[65536];DWORD received=0;
        while(true){if(gCancel.load())throw std::runtime_error("Cancelled download");if(!WinHttpReadData(request.value,buffer,sizeof(buffer),&received))throw std::runtime_error("Download read");if(!received)break;
            total+=received;if(total>64ULL*1024*1024)throw std::runtime_error("Download too large");DWORD written=0;if(!WriteFile(file,buffer,received,&written,nullptr)||written!=received)throw std::runtime_error("Download write");}
        if(!FlushFileBuffers(file))throw std::runtime_error("Download flush");CloseHandle(file);file=INVALID_HANDLE_VALUE;
        if(total<1024*1024||!PublicVerifyMicrosoft(target,error))throw std::runtime_error("Download signature");return true;
    }catch(...){if(file!=INVALID_HANDLE_VALUE)CloseHandle(file);if(owned){std::error_code ignored;fs::remove(target,ignored);}if(error.empty())error=L"The Microsoft runtime could not be downloaded securely. Check your internet connection and retry Play. Your game and saved data were preserved.";return false;}
}
static int PublicPrerequisites(const fs::path& root,bool interactive,std::wstring& error) {
    auto missing=PublicMissingVC();if(missing.empty())return 0;
    Console("MICROSOFT_VC_RUNTIME_REQUIRED=true");
    if(!interactive){error=L"The included emulator needs Microsoft's Visual C++ x64 runtime. Select Play to download the official signed installer, or use https://aka.ms/vs/17/release/vc_redist.x64.exe .";return 46;}
    if(MessageBoxW(gWindow,L"The emulator needs Microsoft's Visual C++ x64 runtime. Download the official installer directly from Microsoft now?\n\nIts Microsoft signature will be checked. Microsoft's normal setup/license window will open and may request Windows administrator approval. No silent install is used. Choose No to cancel and retry Play later.",kTitle,MB_YESNO|MB_DEFBUTTON2|MB_ICONINFORMATION)!=IDYES){error=L"Runtime setup cancelled. Select Play when you are ready.";return 61;}
    auto download=root/L"UserData"/(L".microsoft-vc-"+Guid()+L".exe");
    if(!PublicDownloadMicrosoft(download,error))return 46;
    SHELLEXECUTEINFOW launch{sizeof(launch)};launch.fMask=SEE_MASK_NOCLOSEPROCESS|SEE_MASK_FLAG_NO_UI;launch.hwnd=gWindow;launch.lpVerb=L"open";launch.lpFile=download.c_str();launch.lpParameters=L"/install /norestart";launch.nShow=SW_SHOWNORMAL;
    DWORD code=0;bool started=ShellExecuteExW(&launch)&&launch.hProcess;
    if(started){WaitForSingleObject(launch.hProcess,INFINITE);GetExitCodeProcess(launch.hProcess,&code);CloseHandle(launch.hProcess);}
    else code=GetLastError();std::error_code ignored;fs::remove(download,ignored);
    if(code==1602||code==ERROR_CANCELLED){error=L"Microsoft runtime setup was cancelled. Your game and saved data were preserved. Select Play to retry.";return 61;}
    if(!started||(code!=0&&code!=3010)){error=L"Microsoft runtime setup did not finish. Your game and saved data were preserved. Select Play to retry.";return 46;}
    if(!PublicMissingVC().empty()){error=code==3010?L"Microsoft setup needs a Windows restart. Restart, then select Play.":L"The required Microsoft runtime is still unavailable. Retry Play after completing Microsoft's x64 runtime setup.";return 46;}
    return 0;
}
