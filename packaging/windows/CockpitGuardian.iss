#define MyAppName "Cockpit Guardian"
#ifndef MyAppVersion
#define MyAppVersion "0.1.0"
#endif
#define MyAppPublisher "Realistic Sim Cockpit"
#define MyAppExeName "CockpitGuardian.exe"
#define MyAppURL "https://github.com/realisticsimcockpit/cockpit-guardian"
#ifndef SourceDir
#define SourceDir "..\\..\\build\\windows\\CockpitGuardian"
#endif
#ifndef OutputDir
#define OutputDir "..\\..\\dist"
#endif

[Setup]
AppId={{21E1BB5A-3995-49C3-A6DC-353945D14494}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Cockpit Guardian
DefaultGroupName=Cockpit Guardian
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=CockpitGuardianSetup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}
LicenseFile={#SourceDir}\LICENSE
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoVersion={#MyAppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked
Name: "startup"; Description: "Start Cockpit Guardian with Windows"; GroupDescription: "Startup:"; Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Cockpit Guardian"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Cockpit Guardian"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\Cockpit Guardian"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Cockpit Guardian"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
