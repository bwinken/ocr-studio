; OCR Studio Installer - Inno Setup Script
; Installs without admin rights to %LOCALAPPDATA%

[Setup]
AppName=OCR Studio
AppVersion=1.0.0
AppPublisher=OCR Studio
DefaultDirName={localappdata}\OCRStudio
DefaultGroupName=OCR Studio
PrivilegesRequired=lowest
OutputDir=.\output
OutputBaseFilename=OCRStudio-Setup-1.0.0
Compression=lzma2
SolidCompression=yes
WizardStyle=modern

[Files]
Source: ".\dist\OCRStudio\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\OCR Studio"; Filename: "{app}\OCRStudio.exe"
Name: "{userdesktop}\OCR Studio"; Filename: "{app}\OCRStudio.exe"; Tasks: desktopicon
Name: "{userstartup}\OCR Studio"; Filename: "{app}\OCRStudio.exe"; Tasks: startup

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"
Name: "startup"; Description: "Start OCR Studio when Windows starts"; Flags: unchecked

[Run]
Filename: "{app}\OCRStudio.exe"; Description: "Launch OCR Studio"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{localappdata}\OCRStudio"
