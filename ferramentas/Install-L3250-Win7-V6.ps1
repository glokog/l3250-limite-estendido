#Requires -Version 2.0
[CmdletBinding()]
param(
    [ValidateSet('Install', 'Restore', 'Verify', 'Preferences')][string]$Action = 'Install',
    [switch]$ElevatedChild
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$DriverName = 'EPSON L3250 Series'
$ScriptPath = $MyInvocation.MyCommand.Path
$PackageRoot = Split-Path -Parent $ScriptPath
$StateRoot = Join-Path $env:ProgramData 'L3250-Comprimento-Experimental-Win7'
$TranscriptStarted = $false
$Stage = 'inicio'

function Initialize-NativeSpooler {
    if ($null -eq ('L3250Spooler' -as [type])) {
        Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PackageRoot 'L3250-Spooler.cs')))
    }
}

function Get-NativeDrivers {
    Initialize-NativeSpooler
    return [L3250Spooler]::Drivers()
}

function Get-NativePrinters {
    Initialize-NativeSpooler
    return [L3250Spooler]::Printers()
}

function Get-LocalPrinters {
    try {
        return @(Get-WmiObject -Class Win32_Printer -Namespace 'root\cimv2' -EnableAllPrivileges -ErrorAction Stop)
    } catch {
        Write-Warning ('Consulta WMI das filas falhou: ' + $_.Exception.Message + '. Consultando o spooler diretamente.')
        return @(Get-NativePrinters)
    }
}

function Show-Failure($Failure) {
    Write-Host ('ERRO na etapa "' + $Stage + '": ' + $Failure.Exception.Message) -ForegroundColor Red
    Write-Host ('Identificacao: ' + $Failure.FullyQualifiedErrorId)
    Write-Host ($Failure.InvocationInfo.PositionMessage)
    $exception = $Failure.Exception
    while ($null -ne $exception) {
        Write-Host ('Excecao: ' + $exception.GetType().FullName + '; ' + $exception.Message)
        foreach ($name in @('ErrorCode', 'NativeErrorCode', 'HResult')) {
            $property = $exception.PSObject.Properties[$name]
            if ($null -ne $property) { Write-Host ($name + ': ' + $property.Value) }
        }
        $exception = $exception.InnerException
    }
}

function Test-PermissionFailure($Failure) {
    if ([string]$Failure.CategoryInfo.Category -eq 'PermissionDenied' -or [string]$Failure.CategoryInfo.Category -eq 'SecurityError') { return $true }
    $exception = $Failure.Exception
    while ($null -ne $exception) {
        if ($exception -is [UnauthorizedAccessException] -or $exception -is [Security.SecurityException]) { return $true }
        foreach ($name in @('NativeErrorCode', 'ErrorCode', 'HResult')) {
            $property = $exception.PSObject.Properties[$name]
            if ($null -ne $property -and @('5', '-2147024891', '-2147217405', 'AccessDenied') -contains ([string]$property.Value)) { return $true }
        }
        $exception = $exception.InnerException
    }
    return $false
}

function Show-ProfileLimit([string]$Path) {
    $document = New-Object Xml.XmlDocument
    $document.XmlResolver = $null
    $document.LoadXml([IO.File]::ReadAllText($Path))
    $ns = New-Object Xml.XmlNamespaceManager($document.NameTable)
    $ns.AddNamespace('e', 'http://schema.epson.net/fusion/business/v150')
    $length = $document.SelectSingleNode('/e:c/e:f/e:F[@f="11"]/e:E[@e="0"]/e:V', $ns)
    $inches = $document.SelectSingleNode('/e:c/e:f/e:F[@f="13"]/e:E[@e="0"]/e:V', $ns)
    $extent = $document.SelectSingleNode('/e:c/e:f/e:F[@f="7"]/e:E[@e="261"]', $ns)
    if ($null -eq $length -or $null -eq $inches -or $null -eq $extent) { throw ('Perfil de comprimento nao encontrado: ' + $Path) }
    $panelLength = [int]$length.GetAttribute('x') / 10.0
    $inchLength = [int]$inches.GetAttribute('x') / 100.0
    $driverLength = [int]$extent.GetAttribute('K') / 10.0
    Write-Host ('  Perfil do campo Comprimento no painel Epson: {0} mm; limite de papel: {1} mm.' -f $panelLength, $driverLength)
    Write-Host ('  Perfil equivalente em polegadas: {0} in ({1:F1} mm).' -f $inchLength, ($inchLength * 25.4))
    return ($panelLength -ge 4624 -and $driverLength -ge 4624 -and ($inchLength * 25.4) -ge 4624)
}

function Open-Preferences {
    $printers = @(Get-LocalPrinters | Where-Object { $_.DriverName -eq $DriverName })
    if ($printers.Count -eq 0) { throw 'Nenhuma fila usa EPSON L3250 Series.' }
    $index = 0
    if ($printers.Count -gt 1) {
        for ($i = 0; $i -lt $printers.Count; $i++) { Write-Host ('{0}: {1}' -f ($i + 1), $printers[$i].Name) }
        $choice = Read-Host 'Numero da impressora cujas preferencias deseja abrir'
        $number = 0
        if (-not [int]::TryParse($choice, [ref]$number) -or $number -lt 1 -or $number -gt $printers.Count) { throw 'Numero de impressora invalido.' }
        $index = $number - 1
    }
    Write-Host ('Abrindo as preferencias de ' + $printers[$index].Name)
    Write-Host 'Em Tamanho do papel, abra Definido pelo usuario e teste Comprimento = 4624 mm.'
    Start-Process -FilePath (Join-Path $env:windir 'System32\rundll32.exe') -ArgumentList @('printui.dll,PrintUIEntry', '/e', '/n', ('"{0}"' -f $printers[$index].Name)) -Wait
}

function Get-Sha256([string]$Path) {
    $stream = [IO.File]::OpenRead($Path)
    $algorithm = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = $algorithm.ComputeHash($stream)
        return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
    } finally {
        $stream.Close()
        $algorithm.Clear()
    }
}

function Read-PackageManifest {
    $path = Join-Path $PackageRoot 'manifest.xml'
    $document = New-Object Xml.XmlDocument
    $document.XmlResolver = $null
    $document.LoadXml([IO.File]::ReadAllText($path))
    $root = $document.SelectSingleNode('/l3250')
    if ($null -eq $root -or $root.GetAttribute('format') -ne '1') { throw 'Manifesto XML invalido.' }
    $files = @()
    foreach ($node in $root.SelectNodes('files/file')) {
        $files += (New-Object PSObject -Property @{
            installed_name = $node.GetAttribute('installed_name')
            original_sha256 = $node.GetAttribute('original_sha256')
            previous_sha256 = $node.GetAttribute('previous_sha256')
            patched_sha256 = $node.GetAttribute('patched_sha256')
        })
    }
    $binaries = @()
    foreach ($node in $root.SelectNodes('binaries/binary')) {
        $binaries += (New-Object PSObject -Property @{
            properties = @($node.GetAttribute('properties').Split(','))
            source_name = $node.GetAttribute('source_name')
            sha256 = $node.GetAttribute('sha256')
        })
    }
    if ($files.Count -ne 2 -or $binaries.Count -ne 3) { throw 'Manifesto incompleto.' }
    return (New-Object PSObject -Property @{
        original_installer_sha256 = $root.GetAttribute('original_installer_sha256')
        files = @($files)
        binaries = @($binaries)
    })
}

function Set-ConfigFile([string]$Source, [string]$Target, [string]$ExpectedHash) {
    if ($null -eq ('L3250FileOps' -as [type])) {
        Add-Type -TypeDefinition @'
using System.IO;
public static class L3250FileOps {
    public static void Replace(string source, string target) {
        File.Replace(source, target, null);
    }
}
'@
    }
    $temporary = Join-Path ([IO.Path]::GetDirectoryName($Target)) ('.l3250-' + ([Guid]::NewGuid()).ToString('N') + '.tmp')
    try {
        Copy-Item -LiteralPath $Source -Destination $temporary
        if ((Get-Sha256 $temporary) -ne $ExpectedHash) { throw 'A copia temporaria falhou na verificacao.' }
        [L3250FileOps]::Replace($temporary, $Target)
        if ((Get-Sha256 $Target) -ne $ExpectedHash) { throw ('Falha ao verificar ' + $Target) }
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    }
}

function Get-DriverFilePath($Driver, [string]$PropertyName) {
    # ManagementObject.Path identifies a WMI object, not a filesystem file.
    if (@('ConfigFile', 'DriverPath', 'DataFile') -notcontains $PropertyName) { return '' }
    $property = $Driver.PSObject.Properties[$PropertyName]
    if ($null -eq $property -or [string]::IsNullOrEmpty(([string]$property.Value).Trim())) { return '' }
    $path = [Environment]::ExpandEnvironmentVariables(([string]$property.Value).Trim())
    try {
        if (-not [IO.Path]::IsPathRooted($path)) {
            # WMI can return ConfigFile/DataFile as a basename. Anchor it to
            # the registered DriverPath; never guess a spooler version folder.
            if ($PropertyName -eq 'DriverPath' -or $path.IndexOfAny([char[]]'\\/:') -ge 0) { throw 'Caminho relativo inesperado.' }
            $driverPath = Get-DriverFilePath $Driver 'DriverPath'
            if ([string]::IsNullOrEmpty($driverPath)) { throw 'DriverPath absoluto ausente.' }
            $path = Join-Path ([IO.Path]::GetDirectoryName($driverPath)) $path
        }
        return [IO.Path]::GetFullPath($path)
    } catch {
        throw ('Caminho invalido em ' + $PropertyName + ': ' + $path + '; ' + $_.Exception.Message)
    }
}

function Assert-DriverVersion($Driver, $Manifest) {
    foreach ($binary in $Manifest.binaries) {
        $path = ''
        foreach ($propertyName in $binary.properties) {
            $path = Get-DriverFilePath $Driver $propertyName
            if (-not [string]::IsNullOrEmpty($path)) { break }
        }
        if ([string]::IsNullOrEmpty(([string]$path).Trim()) -or -not [IO.Path]::IsPathRooted($path) -or (Get-Sha256 $path) -ne $binary.sha256) {
            throw ('O binario ' + $binary.source_name + ' nao corresponde ao driver analisado. Instale a versao original incluida no pacote.')
        }
    }
}

function Get-LocalDriver {
    try {
        $inventory = @(Get-WmiObject -Class Win32_PrinterDriver -Namespace 'root\cimv2' -EnableAllPrivileges -ErrorAction Stop)
    } catch {
        Write-Warning ('Consulta WMI do driver falhou: ' + $_.Exception.Message + '. Consultando o spooler diretamente.')
        $inventory = @(Get-NativeDrivers)
    }
    $drivers = @($inventory | Where-Object {
        ($_.Name -eq $DriverName -or $_.Name -like ($DriverName + ',*')) -and $_.SupportedPlatform -eq 'Windows x64'
    })
    if ($drivers.Count -ne 1) {
        throw 'O driver EPSON L3250 Series para Windows x64 nao foi encontrado de forma unica. Conclua a instalacao Epson e tente novamente.'
    }
    return $drivers[0]
}

function Get-Targets($Driver, $Manifest) {
    $spoolRoot = [IO.Path]::GetFullPath((Join-Path $env:windir 'System32\spool\drivers\x64'))
    $directories = @()
    $registeredPaths = @()
    foreach ($propertyName in @('ConfigFile', 'DriverPath', 'DataFile')) {
        $path = Get-DriverFilePath $Driver $propertyName
        if (-not [string]::IsNullOrEmpty($path)) { $registeredPaths += $path }
    }
    foreach ($propertyName in @('DependentFiles')) {
        $property = $Driver.PSObject.Properties[$propertyName]
        if ($null -ne $property) { $registeredPaths += @($property.Value) }
    }
    foreach ($registeredPath in $registeredPaths) {
        if ([string]::IsNullOrEmpty(([string]$registeredPath).Trim())) { continue }
        $expanded = [Environment]::ExpandEnvironmentVariables([string]$registeredPath)
        try {
            if (-not [IO.Path]::IsPathRooted($expanded)) { continue }
            $full = [IO.Path]::GetFullPath($expanded)
        } catch {
            Write-Warning ('Caminho dependente invalido ignorado: ' + $expanded)
            continue
        }
        if ($full.StartsWith($spoolRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
            $directories += [IO.Path]::GetDirectoryName($full)
        }
    }
    $directories = @($directories | Sort-Object -Unique)
    $targets = @()
    foreach ($directory in $directories) {
        $pair = @()
        foreach ($entry in $Manifest.files) {
            $target = Join-Path $directory $entry.installed_name
            if (Test-Path -LiteralPath $target -PathType Leaf) {
                $pair += (New-Object PSObject -Property @{
                    target = $target
                    original_sha256 = $entry.original_sha256
                    previous_sha256 = $entry.previous_sha256
                    patched_sha256 = $entry.patched_sha256
                    before_sha256 = ''
                    source = Join-Path $PackageRoot ('patch\' + $entry.installed_name)
                })
            }
        }
        if ($pair.Count -eq $Manifest.files.Count) { $targets += $pair }
    }
    $dataRoot = Get-EpsonDataRoot
    foreach ($entry in $Manifest.files) {
        $target = Join-Path $dataRoot $entry.installed_name
        if (Test-Path -LiteralPath $target -PathType Leaf) {
            Assert-NoReparsePath $target
            $targets += (New-Object PSObject -Property @{
                target = $target
                original_sha256 = $entry.original_sha256
                previous_sha256 = $entry.previous_sha256
                patched_sha256 = $entry.patched_sha256
                before_sha256 = ''
                source = Join-Path $PackageRoot ('patch\' + $entry.installed_name)
            })
        } else { Write-Host ('Perfil de dados ausente: ' + $target) }
    }
    if ($targets.Count -eq 0) {
        throw 'Os dois CFX nao foram encontrados nos caminhos ativos registrados no spooler. O script nao altera o DriverStore. Consulte o log exibido pelo script.'
    }
    return $targets
}

function Get-EpsonDataRoot {
    # 0x180086834: CSIDL_COMMON_APPDATA + EPSON + DriverNameForInstall.
    $common = [Environment]::GetFolderPath([Environment+SpecialFolder]::CommonApplicationData)
    if ([string]::IsNullOrEmpty($common)) { throw 'Pasta CommonApplicationData nao encontrada.' }
    return (Join-Path (Join-Path $common 'EPSON') 'EPSON L3250 Series')
}

function Assert-NoReparsePath([string]$Path) {
    $part = [IO.Path]::GetFullPath($Path)
    while (-not [string]::IsNullOrEmpty($part)) {
        if (Test-Path -LiteralPath $part) {
            if (([IO.File]::GetAttributes($part) -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw ('Caminho redirecionado nao sera alterado: ' + $part)
            }
        }
        $part = [IO.Path]::GetDirectoryName($part)
    }
}

function Get-ProfileCache {
    # 0x1801e0bc0: CFGBFile is under ConvBinData. VIF binds this exact name.
    return (Join-Path (Join-Path (Get-EpsonDataRoot) 'ConvBinData') 'E_TCXYWE.CFB')
}

function Show-ProfileCache {
    $path = Get-ProfileCache
    Assert-NoReparsePath $path
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        Write-Host ('Cache CFB ausente: ' + $path)
        return
    }
    $data = [IO.File]::ReadAllBytes($path)
    Write-Host ('Cache CFB: ' + $path + '; SHA256: ' + (Get-Sha256 $path))
    if ($data.Length -ge 64) {
        Write-Host ('  Versao do cache: 0x{0:X8}' -f [BitConverter]::ToUInt32($data, 44))
    }
}

function Retire-ProfileCache([string]$BackupDirectory) {
    $path = Get-ProfileCache
    Assert-NoReparsePath $path
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return }
    # Called only with the spooler stopped and verified CFX available.
    $hash = Get-Sha256 $path
    $saved = Join-Path $BackupDirectory ('cache-' + [Guid]::NewGuid().ToString('N') + '.CFB')
    Copy-Item -LiteralPath $path -Destination $saved
    if ((Get-Sha256 $saved) -ne $hash -or (Get-Sha256 $path) -ne $hash) {
        throw 'Cache mudou durante o backup; cache ativo preservado.'
    }
    $cacheRecord = New-Object PSObject -Property @{ target = $path; backup = $saved; sha256 = $hash }
    Export-Clixml -InputObject $cacheRecord -Path ($saved + '.clixml') -Depth 3 -Encoding UTF8
    Remove-Item -LiteralPath $path -ErrorAction Stop
    Write-Host ('Cache antigo guardado em ' + $saved + '. O driver pode regenerar o CFB a partir do CFX.')
}

function Show-EpsonDataFolders {
    $epson = [IO.Path]::GetDirectoryName((Get-EpsonDataRoot))
    if (-not (Test-Path -LiteralPath $epson)) { Write-Host ('  Pasta ausente: ' + $epson); return }
    Write-Host ('  Conteudo de ' + $epson + ':')
    foreach ($folder in @(Get-ChildItem -LiteralPath $epson -Force -ErrorAction SilentlyContinue)) {
        Write-Host ('    ' + $folder.Name)
        if ($folder.PSIsContainer) {
            foreach ($file in @(Get-ChildItem -LiteralPath $folder.FullName -Force -ErrorAction SilentlyContinue)) { Write-Host ('      ' + $file.Name) }
        }
    }
}

function Assert-RuntimeProfiles($Targets) {
    $root = Get-EpsonDataRoot
    $runtime = @($Targets | Where-Object { $_.target -eq (Join-Path $root 'E_TCXYWE.CFX') })
    if ($runtime.Count -eq 0) {
        $inData = @($Targets | Where-Object { $_.target.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase) })
        if ($inData.Count -gt 0) {
            throw ('Perfil base E_TCXYWE.CFX ausente em ' + $root + ', mas ha outro CFX nessa pasta. Nenhum arquivo sera alterado.')
        }
        # The driver has not created working profiles yet; it can only take them from the spooler CFX.
        Show-EpsonDataFolders
        Write-Host ('Sem perfis de trabalho em ' + $root + '. Serao ajustados os CFX do driver no spooler.') -ForegroundColor Yellow
    }
    Assert-NoReparsePath (Get-ProfileCache)
}

function Assert-IdleSpooler {
    try {
        $jobs = @(Get-WmiObject -Class Win32_PrintJob -Namespace 'root\cimv2' -EnableAllPrivileges -ErrorAction Stop)
        $busy = $jobs.Count -gt 0
    } catch {
        Write-Warning ('Consulta WMI dos trabalhos falhou: ' + $_.Exception.Message + '. Consultando as filas locais diretamente.')
        $queues = @(Get-NativePrinters)
        $busy = @($queues | Where-Object { $_.Jobs -gt 0 }).Count -gt 0
    }
    if ($busy) {
        throw 'Existem trabalhos nas filas de impressao. Espere terminarem e execute novamente; nenhum trabalho sera apagado.'
    }
    if ((Get-Service -Name Spooler).Status -ne 'Running') {
        throw 'O servico Spooler precisa estar em execucao antes de aplicar ou restaurar o ajuste.'
    }
}

function Show-Capabilities {
    if ($null -eq ('L3250Capabilities' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class L3250Capabilities {
    [DllImport("winspool.drv", EntryPoint="DeviceCapabilitiesW", ExactSpelling=true, CharSet=CharSet.Unicode)]
    public static extern int DeviceCapabilities(string device, string port, ushort capability, IntPtr output, IntPtr devmode);
}
'@
    }
    $printers = @(Get-LocalPrinters | Where-Object { $_.DriverName -eq $DriverName })
    if ($printers.Count -eq 0) {
        Write-Warning 'Nenhuma fila usa o driver Epson L3250. Conecte a impressora, crie a fila e rode verificar.cmd.'
        return $false
    }
    $allExpanded = $true
    foreach ($printer in $printers) {
        $extent = [L3250Capabilities]::DeviceCapabilities($printer.Name, $printer.PortName, 5, [IntPtr]::Zero, [IntPtr]::Zero)
        if ($extent -eq -1 -or $extent -eq 0) {
            Write-Warning ('Nao foi possivel consultar DC_MAXEXTENT para ' + $printer.Name)
            $allExpanded = $false
            continue
        }
        $extentBytes = [BitConverter]::GetBytes([int]$extent)
        $width = [BitConverter]::ToUInt16($extentBytes, 0) / 10.0
        $length = [BitConverter]::ToUInt16($extentBytes, 2) / 10.0
        Write-Host ('Fila: {0}; largura maxima: {1} mm; comprimento maximo informado: {2} mm' -f $printer.Name, $width, $length)
        if ($length -lt 4624) { $allExpanded = $false }
    }
    if (-not $allExpanded) {
        Write-Warning 'O driver ainda nao confirmou 4624 mm em todas as filas. Confira os CFX e o campo Comprimento nas preferencias da mesma fila.'
    }
    return $allExpanded
}

function Test-Verification($Manifest) {
    $failed = $false
    $pending = $false
    try {
        $script:Stage = 'consulta do driver e arquivos ativos'
        $driver = Get-LocalDriver
        Write-Host ('Driver instalado: ' + $driver.Name)
        Assert-DriverVersion $driver $Manifest
        $targets = @(Get-Targets $driver $Manifest)
        Assert-RuntimeProfiles $targets
        Show-ProfileCache
        foreach ($target in $targets) {
            try {
                $script:Stage = 'leitura de ' + $target.target
                $hash = Get-Sha256 $target.target
                Write-Host ('CFX ativo: ' + $target.target + '; SHA256: ' + $hash)
                if ($hash -eq $target.original_sha256) {
                    Write-Host '  Ajuste NAO aplicado: configuracao original de 1200 mm.' -ForegroundColor Yellow
                    $pending = $true
                } elseif ($hash -eq $target.previous_sha256) {
                    Write-Host '  CFX de uma versao anterior presente. Aplique instalar.cmd da V6.' -ForegroundColor Yellow
                    $pending = $true
                } elseif ($hash -eq $target.patched_sha256) {
                    Write-Host '  Limites ampliados presentes neste CFX: mm e polegadas.'
                } else { throw 'Versao CFX nao reconhecida.' }
                if (-not (Show-ProfileLimit $target.target)) { $pending = $true }
            } catch { Show-Failure $_; $failed = $true }
        }
    } catch { Show-Failure $_; $failed = $true }
    $capabilitiesOk = $false
    try { $script:Stage = 'consulta do comprimento anunciado'; $capabilitiesOk = Show-Capabilities }
    catch { Show-Failure $_; $failed = $true }
    Write-Host 'Teste do painel: execute abrir-preferencias.cmd, abra Definido pelo usuario e tente salvar 210 x 4624 mm.'
    if ($failed) { return 1 }
    if ($pending -or -not $capabilitiesOk) { return 2 }
    Write-Host 'Perfis ativos e limite anunciado conferidos. A aceitacao no painel e a impressao precisam ser testadas no Windows.' -ForegroundColor Green
    return 0
}

function Invoke-InstallerProcess([string]$Executable, [string]$Arguments, [bool]$Elevate) {
    if ($null -eq ('L3250Process' -as [type])) {
        Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $PackageRoot 'L3250-Process.cs')))
    }
    return [L3250Process]::Run($Executable, $Arguments, $Elevate)
}

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Return from a dot-sourced block; exit only after all finally handlers finish.
$ResultCode = . {
try {
    if ([IntPtr]::Size -ne 8 -or $env:PROCESSOR_ARCHITECTURE -ne 'AMD64') {
        throw 'Este pacote exige Windows x64 Intel/AMD e PowerShell 2.0 ou superior de 64 bits. Nao e para Windows ARM64.'
    }
    if ($Action -eq 'Install' -or $Action -eq 'Restore') {
      if (-not (Test-Administrator)) {
        if ($ElevatedChild) { throw 'A janela solicitada nao obteve privilegios de administrador.' }
        $Stage = 'elevacao de administrador'
        $arguments = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $ScriptPath), '-Action', $Action, '-ElevatedChild')
        $childCode = Invoke-InstallerProcess (Join-Path $PSHOME 'powershell.exe') ($arguments -join ' ') $true
        if (@(0, 1, 2) -notcontains $childCode) { throw ('A janela elevada terminou com codigo inesperado: ' + $childCode) }
        return $childCode
      }
    }
    $Stage = 'criacao do registro'
    $logRoot = $StateRoot
    $logName = $Action.ToLowerInvariant() + '-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + $PID + '.log'
    try {
        New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
        $log = Join-Path $logRoot $logName
        Start-Transcript -Path $log -Force | Out-Null
    } catch {
        if ($Action -ne 'Verify' -and $Action -ne 'Preferences') { throw }
        $logRoot = Join-Path ([IO.Path]::GetTempPath()) 'L3250-Diagnostico'
        New-Item -ItemType Directory -Path $logRoot -Force | Out-Null
        $log = Join-Path $logRoot $logName
        Start-Transcript -Path $log -Force | Out-Null
    }
    $TranscriptStarted = $true
    Write-Host 'L3250 V6: sem borda, limite de 4624 mm, perfis em ProgramData e regeneracao do cache.'
    Write-Host 'Feche as preferencias Epson e os aplicativos de impressao antes de aplicar ou restaurar.'
    Write-Host ('Registro: ' + $log)
    Write-Host ('Windows: ' + [Environment]::OSVersion.VersionString + '; PowerShell: ' + $PSVersionTable.PSVersion)
    $Stage = 'leitura do manifesto'
    $manifest = Read-PackageManifest

    if ($Action -eq 'Preferences') {
        $Stage = 'abertura das preferencias'
        Open-Preferences
        return 0
    }
    if ($Action -eq 'Verify') {
        $result = Test-Verification $manifest
        Write-Host ('Guarde este registro se o painel continuar em 1200 mm: ' + $log)
        return $result
    }

    if ($Action -eq 'Restore') {
        $Stage = 'restauracao dos arquivos ativos'
        $recordPath = Join-Path $StateRoot 'last-backup.clixml'
        if (-not (Test-Path -LiteralPath $recordPath)) { throw 'Nao existe backup registrado deste ajuste.' }
        $record = Import-Clixml -Path $recordPath
        $driver = Get-LocalDriver
        Assert-DriverVersion $driver $manifest
        $active = @(Get-Targets $driver $manifest)
        Assert-RuntimeProfiles $active
        if ($null -eq $record.PSObject.Properties['release'] -or $record.release -ne 6) { throw 'Use instalar.cmd da V6 antes de restaurar por este pacote; o backup antigo nao inclui os perfis de ProgramData.' }
        if (@($record.files).Count -ne $active.Count) { throw 'A lista de perfis mudou desde o backup. Nenhum arquivo sera alterado.' }
        foreach ($item in $record.files) {
            $matched = @($active | Where-Object { $_.target -eq $item.target -and $_.original_sha256 -eq $item.original_sha256 -and $_.patched_sha256 -eq $item.patched_sha256 })
            if ($matched.Count -ne 1) { throw ('O caminho nao pertence mais ao driver ativo: ' + $item.target) }
            if ((Get-Sha256 $item.backup) -ne $item.original_sha256) { throw ('Backup alterado: ' + $item.backup) }
            $current = Get-Sha256 $item.target
            if ($current -ne $item.patched_sha256 -and $current -ne $matched[0].previous_sha256 -and $current -ne $item.original_sha256) {
                throw ('O arquivo mudou desde o ajuste; restaure pela reinstalacao Epson: ' + $item.target)
            }
        }
        Assert-IdleSpooler
        $restoreDirectory = Join-Path $StateRoot ('restauracoes\' + [Guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path $restoreDirectory -Force | Out-Null
        $restoreRecords = @()
        foreach ($item in $record.files) {
            $saved = Join-Path $restoreDirectory ([Guid]::NewGuid().ToString('N') + '.CFX')
            $hash = Get-Sha256 $item.target
            Copy-Item -LiteralPath $item.target -Destination $saved
            if ((Get-Sha256 $saved) -ne $hash) { throw 'Falha no backup anterior a restauracao.' }
            $restoreRecords += (New-Object PSObject -Property @{ target = $item.target; source = $saved; sha256 = $hash; original_sha256 = $item.original_sha256 })
        }
        Export-Clixml -InputObject $restoreRecords -Path (Join-Path $restoreDirectory 'antes.clixml') -Depth 4 -Encoding UTF8
        $restored = @()
        try {
            Stop-Service -Name Spooler -Force -ErrorAction Stop
            (Get-Service -Name Spooler).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
            foreach ($item in $record.files) {
                $before = @($restoreRecords | Where-Object { $_.target -eq $item.target })[0]
                if ((Get-Sha256 $item.target) -ne $before.sha256) { throw 'Perfil mudou antes da restauracao.' }
                $restored += $item.target
                Set-ConfigFile $item.backup $item.target $item.original_sha256
            }
            Retire-ProfileCache $restoreDirectory
        } catch {
            $restoreFailure = $_
            foreach ($before in $restoreRecords) {
                if ($restored -notcontains $before.target) { continue }
                try {
                    $hash = Get-Sha256 $before.target
                    if ($hash -ne $before.sha256 -and $hash -ne $before.original_sha256) { throw 'Perfil mudou durante a restauracao.' }
                    Set-ConfigFile $before.source $before.target $before.sha256
                } catch { Write-Warning ('Falha ao desfazer restauracao: ' + $_.Exception.Message) }
            }
            throw $restoreFailure
        } finally {
            Start-Service -Name Spooler -ErrorAction Stop
            (Get-Service -Name Spooler).WaitForStatus('Running', [TimeSpan]::FromSeconds(30))
        }
        Write-Host 'Configuracoes originais restauradas e verificadas.' -ForegroundColor Green
        return 0
    }

    if ($Action -eq 'Install') {
        $Stage = 'validacao do pacote e driver instalado'
        foreach ($entry in $manifest.files) {
            $source = Join-Path $PackageRoot ('patch\' + $entry.installed_name)
            if ((Get-Sha256 $source) -ne $entry.patched_sha256) { throw ('Patch alterado: ' + $source) }
        }
        $installer = Join-Path $PackageRoot 'DriverOriginal.exe'
        $ready = $false
        $driverFound = $false
        try {
            $driver = Get-LocalDriver
            $driverFound = $true
            Assert-DriverVersion $driver $manifest
            $targets = @(Get-Targets $driver $manifest)
            $ready = $true
            foreach ($target in $targets) {
                $hash = Get-Sha256 $target.target
                if ($hash -ne $target.original_sha256 -and $hash -ne $target.previous_sha256 -and $hash -ne $target.patched_sha256) { throw ('CFX nao reconhecido; nenhum arquivo sera aplicado: ' + $target.target) }
            }
        } catch {
            if ($driverFound -or (Test-PermissionFailure $_)) { throw }
            Write-Warning ('Driver ainda nao preparado: ' + $_.Exception.Message)
            $ready = $false
        }
        if (-not $ready) {
            if (-not (Test-Path -LiteralPath $installer -PathType Leaf)) {
                throw 'Nao foi possivel validar o driver instalado. Este ZIP pequeno exige a versao Epson 3.80.05.00 do pacote completo. Consulte a causa acima; nenhum CFX foi alterado.'
            }
            if ((Get-Sha256 $installer) -ne $manifest.original_installer_sha256) { throw 'O instalador original nao corresponde ao pacote analisado.' }
            Write-Host 'Abrindo o instalador original Epson. Conclua a instalacao da L3250 nas janelas que abrirem.'
            $installerCode = Invoke-InstallerProcess $installer '' $false
            if ($installerCode -eq 3010) { throw 'A Epson pediu reinicializacao. Reinicie o Windows e rode instalar.cmd novamente.' }
            if ($installerCode -ne 0) { throw ('O instalador Epson terminou com codigo ' + $installerCode + '. O patch nao foi aplicado.') }
        }
    }

    $Stage = 'validacao dos CFX ativos'
    $driver = Get-LocalDriver
    Assert-DriverVersion $driver $manifest
    $targets = @(Get-Targets $driver $manifest)
    Assert-RuntimeProfiles $targets
    Show-ProfileCache
    $pending = @()
    foreach ($target in $targets) {
        $hash = Get-Sha256 $target.target
        $target.before_sha256 = $hash
        Write-Host ('CFX: ' + $target.target + '; SHA256: ' + $hash)
        if ($hash -eq $target.patched_sha256) { Write-Host '  Limites ampliados ja presentes neste CFX.' }
        elseif ($hash -eq $target.previous_sha256) { $pending += $target; Write-Host '  Atualizando o perfil V5 reconhecido para o limite V6.' }
        elseif ($hash -eq $target.original_sha256) { $pending += $target; Write-Host '  Configuracao original de 1200 mm.' }
        else { throw ('Versao CFX nao reconhecida. Nenhum arquivo sera alterado: ' + $target.target) }
    }
    # Even matching CFX need a fresh cache, so record/retire it on each Install.
    if ($Action -eq 'Install') {
        Assert-IdleSpooler
        $backupDirectory = Join-Path $StateRoot ('backups\' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + ([Guid]::NewGuid()).ToString('N'))
        New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
        $records = @()
        for ($i = 0; $i -lt $targets.Count; $i++) {
            $target = $targets[$i]
            $backup = Join-Path $backupDirectory ($i.ToString() + '-' + [IO.Path]::GetFileName($target.target))
            $originalSource = Join-Path $PackageRoot ('originais\' + [IO.Path]::GetFileName($target.target))
            if ((Get-Sha256 $originalSource) -ne $target.original_sha256) { throw 'Original do pacote alterado; nenhum ajuste aplicado.' }
            Copy-Item -LiteralPath $originalSource -Destination $backup
            if ((Get-Sha256 $backup) -ne $target.original_sha256) { throw 'Falha ao verificar o backup. Nenhuma alteracao aplicada.' }
            $beforeBackup = Join-Path $backupDirectory ($i.ToString() + '-antes-' + [IO.Path]::GetFileName($target.target))
            Copy-Item -LiteralPath $target.target -Destination $beforeBackup
            if ((Get-Sha256 $beforeBackup) -ne $target.before_sha256) { throw 'Arquivo mudou antes da transacao. Nenhuma alteracao aplicada.' }
            $records += (New-Object PSObject -Property @{ target = $target.target; backup = $backup; original_sha256 = $target.original_sha256; patched_sha256 = $target.patched_sha256; before_backup = $beforeBackup; before_sha256 = $target.before_sha256 })
        }
        $record = (New-Object PSObject -Property @{ release = 6; driver_name = $DriverName; created = (Get-Date).ToString('o'); files = @($records) })
        $backupRecord = Join-Path $backupDirectory 'backup.clixml'
        Export-Clixml -InputObject $record -Path $backupRecord -Depth 6 -Encoding UTF8
        Copy-Item -LiteralPath $backupRecord -Destination (Join-Path $StateRoot 'last-backup.clixml') -Force
        $attempted = @()
        try {
            $Stage = 'parada do spooler'
            Stop-Service -Name Spooler -Force -ErrorAction Stop
            (Get-Service -Name Spooler).WaitForStatus('Stopped', [TimeSpan]::FromSeconds(30))
            foreach ($target in $pending) {
                $Stage = 'substituicao de ' + $target.target
                if ((Get-Sha256 $target.target) -ne $target.before_sha256) { throw ('Arquivo mudou durante a instalacao: ' + $target.target) }
                $attempted += $target.target
                Set-ConfigFile $target.source $target.target $target.patched_sha256
            }
            # Check unchanged profiles too before retiring the only selected cache.
            foreach ($target in $targets) {
                if ((Get-Sha256 $target.target) -ne $target.patched_sha256) { throw 'Perfil mudou durante a transacao.' }
            }
            Retire-ProfileCache $backupDirectory
        } catch {
            $originalFailure = $_
            foreach ($item in $records) {
                if (@($attempted | Where-Object { $_ -eq $item.target }).Count -eq 0) { continue }
                try {
                    $current = Get-Sha256 $item.target
                    if ($current -eq $item.patched_sha256 -or $current -eq $item.before_sha256) {
                        if ((Get-Sha256 $item.before_backup) -ne $item.before_sha256) { throw 'Backup anterior da transacao alterado.' }
                        Set-ConfigFile $item.before_backup $item.target $item.before_sha256
                    }
                } catch { Write-Warning ('Falha na restauracao automatica de ' + $item.target + ': ' + $_.Exception.Message) }
            }
            throw $originalFailure
        } finally {
            Start-Service -Name Spooler -ErrorAction Stop
            (Get-Service -Name Spooler).WaitForStatus('Running', [TimeSpan]::FromSeconds(30))
        }
        Write-Host ('Ajuste copiado e hashes verificados. Backup: ' + $backupDirectory)
    }
    foreach ($target in $targets) { Show-ProfileLimit $target.target | Out-Null }
    $Stage = 'consulta do comprimento anunciado'
    $capabilitiesOk = Show-Capabilities
    Show-ProfileCache
    if (-not $capabilitiesOk) { return 2 }
    Write-Host 'O driver anuncia pelo menos 4624 mm. Feche e reabra o aplicativo de impressao antes do teste.' -ForegroundColor Green
    Write-Host 'Execute abrir-preferencias.cmd. No painel Epson, abra Tamanho do papel > Definido pelo usuario e salve 210 x 4624 mm.'
    return 0
} catch {
    Show-Failure $_
    Write-Host ('Consulte os registros em ' + $StateRoot)
    Write-Host 'Se a copia for bloqueada pelo Windows, o ajuste nao foi confirmado. Este script nao muda permissoes, politicas de assinatura ou o DriverStore.'
    return 1
} finally {
    if ($TranscriptStarted) { try { Stop-Transcript | Out-Null } catch { Write-Warning 'Nao foi possivel encerrar o registro.' } }
    if ($ElevatedChild) { try { Read-Host 'Pressione ENTER para fechar esta janela' | Out-Null } catch { Write-Warning 'Nao foi possivel aguardar ENTER.' } }
}

}
if ($null -eq $ResultCode -or $ResultCode -is [array] -or @(0, 1, 2) -notcontains $ResultCode) {
    Write-Host 'ERRO: resultado da execucao ausente ou invalido.'
    $ResultCode = 1
}
Write-Host ('RESULTADO V6: ' + $ResultCode + ' (0=verificacao concluida; 1=erro; 2=limite pendente)')
exit ([int]$ResultCode)
