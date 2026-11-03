/* Starts the bundled native Qt application; no shell, browser or network service. */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR arguments, int show) {
    static wchar_t root[32768], python[32768], script[32768], command[32768];
    DWORD size=GetModuleFileNameW(NULL,root,32768);
    if (!size || size>=32000) return 1;
    wchar_t *last=wcsrchr(root,L'\\');
    if (!last) return 1;
    *last=0;
    if (wcslen(root)>14000 || wcslen(arguments)>2000) return 1;
    wcscpy(python,root);wcscat(python,L"\\runtime\\windows\\pythonw.exe");
    wcscpy(script,root);wcscat(script,L"\\covenant_graphics_studio.py");
    if (GetFileAttributesW(python)==INVALID_FILE_ATTRIBUTES || GetFileAttributesW(script)==INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(NULL,L"Extraia todo o ZIP e mantenha runtime, assets e os arquivos do aplicativo juntos deste executavel.",L"Covenant Graphics Studio",MB_OK|MB_ICONERROR);
        return 1;
    }
    wcscpy(command,L"\"");wcscat(command,python);wcscat(command,L"\" -E -s \"");
    wcscat(command,script);wcscat(command,L"\" ");wcscat(command,arguments);
    STARTUPINFOW startup={0};PROCESS_INFORMATION process={0};startup.cb=sizeof(startup);
    if (!CreateProcessW(python,command,NULL,NULL,FALSE,CREATE_NO_WINDOW,NULL,root,&startup,&process)) {
        MessageBoxW(NULL,L"Nao foi possivel iniciar a janela. Confira se o pacote foi extraido por completo.",L"Covenant Graphics Studio",MB_OK|MB_ICONERROR);
        return 1;
    }
    CloseHandle(process.hThread);CloseHandle(process.hProcess);return 0;
}
