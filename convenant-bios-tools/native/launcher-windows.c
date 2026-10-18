/* Native Windows entry point. Starts the bundled Python/Qt desktop application. */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <wchar.h>

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR arguments, int show) {
    static wchar_t root[32768], python[32768], script[32768], command[32768];
    DWORD size = GetModuleFileNameW(NULL, root, 32768);
    if (!size || size >= 32000) return 1;
    wchar_t *last = wcsrchr(root, L'\\');
    if (!last) return 1;
    *last = 0;
    if (wcslen(root) > 14000 || wcslen(arguments) > 2000) return 1;
    wcscpy(python, root); wcscat(python, L"\\runtime\\windows\\pythonw.exe");
    wcscpy(script, root); wcscat(script, L"\\convenant_bios_tools.py");
    if (GetFileAttributesW(python) == INVALID_FILE_ATTRIBUTES ||
        GetFileAttributesW(script) == INVALID_FILE_ATTRIBUTES) {
        MessageBoxW(NULL, L"Extraia TODO o ZIP antes de abrir. Mantenha runtime, tools e os arquivos do aplicativo junto deste executavel.",
                    L"Convenant BIOS Tools", MB_OK | MB_ICONERROR);
        return 1;
    }
    wcscpy(command, L"\""); wcscat(command, python);
    wcscat(command, L"\" -E -s \""); wcscat(command, script); wcscat(command, L"\" "); wcscat(command, arguments);
    STARTUPINFOW startup = {0}; PROCESS_INFORMATION process = {0};
    startup.cb = sizeof(startup);
    if (!CreateProcessW(python, command, NULL, NULL, FALSE, CREATE_NO_WINDOW,
                        NULL, root, &startup, &process)) {
        MessageBoxW(NULL, L"Nao foi possivel iniciar o aplicativo. Confira se a pasta foi extraida e se o Windows permitiu a execucao.",
                    L"Convenant BIOS Tools", MB_OK | MB_ICONERROR);
        return 1;
    }
    CloseHandle(process.hThread); CloseHandle(process.hProcess);
    return 0;
}
