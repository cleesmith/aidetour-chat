; Inno Setup Script for AidetourChat

[Setup]
AppName=AidetourChat
AppVersion=1.0
DefaultDirName={autopf}\AidetourChat
DefaultGroupName=AidetourChat
UninstallDisplayIcon={app}\AidetourChat.exe
Compression=lzma
SolidCompression=yes
OutputDir=.
OutputBaseFilename=AidetourChatSetup

[Files]
Source: "dist\AidetourChat.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\AidetourChatIcon.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\AidetourChat"; Filename: "{app}\AidetourChat.exe"; IconFilename: "{app}\AidetourChatIcon.ico"
Name: "{commondesktop}\AidetourChat"; Filename: "{app}\AidetourChat.exe"; IconFilename: "{app}\AidetourChatIcon.ico"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Run]
Filename: "{app}\AidetourChat.exe"; Description: "Launch AidetourChat"; Flags: nowait postinstall skipifsilent
