#define MyAppName "Rental Management"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "rental-mgmt"
#define MyAppURL "https://rental-mgmt.local"
#define PythonVersion "3.12.0"
#define PythonURL "https://www.python.org/ftp/python/{#PythonVersion}/python-{#PythonVersion}-amd64.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={localappdata}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#SourcePath}\..\dist
OutputBaseFilename=rental-mgmt-setup-{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=none
DisableWelcomePage=no
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\app\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\frontend\dist\*"; DestDir: "{app}\frontend\dist"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\alembic\*"; DestDir: "{app}\alembic"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\alembic.ini"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\desktop.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\pyproject.toml"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\.env.example"; DestDir: "{app}"; Flags: ignoreversion
Source: "run.bat"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\data\db"
Name: "{app}\data\backups"
Name: "{app}\data\invoices"

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\run.bat"; WorkingDir: "{app}"; AppUserModelID: "RentalMgmt"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\run.bat"; WorkingDir: "{app}"; Tasks: desktopicon; AppUserModelID: "RentalMgmt"

[Run]
Filename: "{cmd}"; Parameters: "/C pip install ."; WorkingDir: "{app}"; Flags: runhidden waituntilterminated; StatusMsg: "Installing Python dependencies..."
Filename: "{app}\run.bat"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C pip uninstall -y rental-mgmt"; Flags: runhidden waituntilterminated; RunOnceId: "UninstallPip"

[Code]
var
  DownloadPage: TDownloadWizardPage;
  PythonDownloaded: Boolean;

function IsPythonInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := False;
  if Exec(ExpandConstant('{cmd}'), '/C python --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    Result := ResultCode = 0;
  if not Result then
    if Exec(ExpandConstant('{cmd}'), '/C python3 --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) then
      Result := ResultCode = 0;
end;

function PreparePythonInstall(PreviousPageId: Integer): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  if IsPythonInstalled() then
    Exit;

  if MsgBox('Python {#PythonVersion} no esta instalado.' #13#13
            'El instalador puede descargarlo e instalarlo automaticamente.' #13#13
            'Desea continuar?', mbConfirmation, MB_YESNO) = IDNO then
  begin
    Result := False;
    Exit;
  end;

  DownloadPage := CreateDownloadPage(SetupMessage(msgWizardPreparing), SetupMessage(msgPreparingDesc), nil);
  DownloadPage.Clear;
  DownloadPage.Add('Python {#PythonVersion} ({#PythonURL})', '{#PythonURL}', '');

  DownloadPage.Show;
  try
    DownloadPage.Download;
    PythonDownloaded := True;
  finally
    DownloadPage.Hide;
  end;

  if not FileExists(ExpandConstant('{tmp}{\}') + 'python-{#PythonVersion}-amd64.exe') then
  begin
    MsgBox('Error al descargar Python. Verifica tu conexion a internet.', mbError, MB_OK);
    Result := False;
    Exit;
  end;

  WizardForm.StatusLabel.Caption := 'Instalando Python {#PythonVersion}...';
  WizardForm.ProgressGauge.Style := npbstMarquee;
  if Exec(ExpandConstant('{tmp}{\}python-{#PythonVersion}-amd64.exe'),
          '/quiet PrependPath=1 Include_test=0',
          '', SW_SHOW, ewWaitUntilTerminated, ResultCode) then
  begin
    if ResultCode <> 0 then
    begin
      MsgBox('Error al instalar Python (codigo: ' + IntToStr(ResultCode) + ').' #13#13
             'Instala Python manualmente desde python.org y vuelve a ejecutar este instalador.',
             mbError, MB_OK);
      Result := False;
      Exit;
    end;
    Log('Python installed successfully');
  end
  else
  begin
    MsgBox('Error al ejecutar el instalador de Python.', mbError, MB_OK);
    Result := False;
  end;
  WizardForm.ProgressGauge.Style := npbstNormal;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpSelectDir then
    Result := PreparePythonInstall(CurPageID);
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and PythonDownloaded then
    DeleteFile(ExpandConstant('{tmp}{\}python-{#PythonVersion}-amd64.exe'));
end;
