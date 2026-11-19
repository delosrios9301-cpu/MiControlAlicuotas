# Asistente de autorizacion inicial OneDrive personal (sin clave de Azure).
# Este programa NO lee ni sube pacientes ni guarda tokens en GitHub.
# La cuenta se autoriza directamente en el navegador de Microsoft.
$ErrorActionPreference='Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
Write-Host ""
Write-Host "MI CONTROL DE ALICUOTAS - CONECTAR ONEDRIVE PERSONAL" -ForegroundColor Cyan
Write-Host "Este paso solo se ejecuta una vez desde Windows. No es el capturador de Excel."
Write-Host "Se autorizara SOLO la lectura. No se enviaran datos a Firebase."
Write-Host "No uses la cuenta de Cevaxin ni otra cuenta empresarial."
Write-Host ""

$folder=Join-Path $env:LOCALAPPDATA "MiControlAlicuotas"
New-Item -ItemType Directory -Force -Path $folder | Out-Null
$cfg=Join-Path $folder "onedrive-personal-rclone.conf"
$env:RCLONE_CONFIG=$cfg
$env:RCLONE_ONEDRIVE_ACCESS_SCOPES="Files.Read Files.Read.All offline_access"

function Find-Rclone {
    $candidate=Get-Command rclone.exe -ErrorAction SilentlyContinue
    if ($candidate) { return $candidate.Source }
    $candidates=@(
      (Join-Path $env:LOCALAPPDATA 'Microsoft\WinGet\Links\rclone.exe'),
      (Join-Path $env:ProgramFiles 'Rclone\rclone.exe'),
      (Join-Path $env:ProgramFiles 'rclone\rclone.exe')
    )
    foreach($path in $candidates){ if(Test-Path $path){return $path} }
    $packages=Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
    if(Test-Path $packages){
      $found=Get-ChildItem $packages -Directory -Filter 'Rclone.Rclone*' -ErrorAction SilentlyContinue |
        ForEach-Object { Get-ChildItem $_.FullName -Filter 'rclone.exe' -Recurse -ErrorAction SilentlyContinue } |
        Select-Object -First 1
      if($found){return $found.FullName}
    }
    return $null
}

try {
    $rclone=Find-Rclone
    if(-not $rclone){
      if(-not (Get-Command winget.exe -ErrorAction SilentlyContinue)){
        throw "Windows no tiene winget. Instala rclone desde https://rclone.org/install/ y vuelve a abrir este asistente."
      }
      Write-Host "Instalando rclone desde el gestor oficial de Windows..." -ForegroundColor Yellow
      & winget.exe install --id Rclone.Rclone --exact --accept-source-agreements --accept-package-agreements
      if($LASTEXITCODE -ne 0){ throw "No se pudo instalar rclone con winget. Revisa el mensaje de Windows." }
      $rclone=Find-Rclone
      if(-not $rclone){ throw "rclone se instalo pero Windows aun no lo encuentra. Cierra y abre este asistente otra vez." }
    }
    Write-Host "rclone listo." -ForegroundColor Green
    $existing=@(& $rclone --config $cfg listremotes 2>$null)
    if($existing -contains 'mca-outlook:'){
      Write-Host "Ya existe una conexion local. No se modificara." -ForegroundColor Yellow
    } else {
      Write-Host "Se abrira Microsoft para iniciar sesion con tu Outlook personal."
      Write-Host "Si aparece Cevaxin, cancela y selecciona la cuenta Outlook."
      & $rclone --config $cfg config create mca-outlook onedrive region global access_scopes "Files.Read Files.Read.All offline_access" config_is_local true --no-output
      if($LASTEXITCODE -ne 0){ throw "No se completo la autorizacion de Microsoft." }
    }
    # Leer el JSON en memoria; nunca imprimir tokens o configuraciones.
    $raw=(& $rclone --config $cfg config dump 2>$null) -join [Environment]::NewLine
    if($LASTEXITCODE -ne 0 -or -not $raw){ throw "La configuracion de OneDrive no se guardo." }
    $doc=$raw | ConvertFrom-Json
    $entry=$doc.'mca-outlook'
    if(-not $entry -or $entry.type -ne 'onedrive'){ throw "Falta la conexion OneDrive personal." }
    if($entry.drive_type -ne 'personal'){
      throw "La cuenta vinculada no es OneDrive personal; no utilizaremos ningun directorio empresarial."
    }
    $scopes=([string]$entry.access_scopes).Trim()
    if($scopes -ne 'Files.Read Files.Read.All offline_access'){
      throw "La conexion no tiene los permisos de solo lectura esperados."
    }
    Write-Host ""
    Write-Host "ONEDRIVE PERSONAL AUTORIZADO LOCALMENTE" -ForegroundColor Green
    Write-Host "No se ha compartido ni transmitido el Excel."
    Write-Host "La configuracion privada esta guardada dentro de tu perfil Windows."
    Write-Host "No compartas el archivo .conf, capturas de sus tokens ni contrasenas."
    Write-Host "Pendiente: conectar este permiso a los secretos de GitHub y verificar Firebase."
} catch {
    Write-Host ""
    Write-Host ("No se pudo completar: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host "No se han borrado registros ni enviado Excel a Firebase."
}
