param(
    [string]$RemoteUrl = 'https://github.com/digiandi/enigma2-web.git'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-Git {
    param([Parameter(Mandatory = $true)][string[]]$GitArguments)
    $gitOutput = & git @GitArguments
    if ($LASTEXITCODE -ne 0) {
        throw "Git fehlgeschlagen (Exit-Code $LASTEXITCODE). Keine weiteren Schritte."
    }
    return $gitOutput
}

function Read-RemoteRefs {
    $refs = @{}
    $lines = @(Invoke-Git -GitArguments @(
        'ls-remote', '--refs', $RemoteUrl, 'refs/heads/*', 'refs/tags/*'
    ))
    foreach ($line in $lines) {
        $parts = $line -split '\s+', 2
        if ($parts.Count -ne 2 -or $parts[0] -notmatch '^[0-9a-f]{40}$') {
            throw 'Die Remote-Antwort konnte nicht ausgewertet werden.'
        }
        $refs[$parts[1]] = $parts[0]
    }
    return $refs
}

function Test-RefSet {
    param([hashtable]$Actual, [hashtable]$Expected)
    if ($Actual.Count -ne $Expected.Count) { return $false }
    foreach ($ref in $Expected.Keys) {
        if (-not $Actual.ContainsKey($ref) -or $Actual[$ref] -ne $Expected[$ref]) {
            return $false
        }
    }
    return $true
}

Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $branch = Invoke-Git -GitArguments @('branch', '--show-current')
    $status = @(Invoke-Git -GitArguments @('status', '--porcelain'))
    if ($branch -ne 'main' -or $status.Count -ne 0) {
        throw 'Das frisch entpackte Git-Paket muss auf main stehen und sauber sein.'
    }
    $head = Invoke-Git -GitArguments @('rev-parse', 'HEAD')
    $release = Invoke-Git -GitArguments @('rev-parse', 'refs/tags/v1.1.2^{}')
    if ($head -ne $release) {
        throw 'HEAD stimmt nicht mit dem Release v1.1.2 ueberein.'
    }

    # Stand aus der zuvor bestaetigten Ausgabe von git ls-remote.
    $oldRefs = @{
        'refs/heads/main' = 'bdcbd48d5532b64e32992e9aa74ce91c5ea0aa66'
        'refs/tags/v1.0.0' = 'a59c53a4067d2fd9c4f219d96e26f30813fda239'
        'refs/tags/v1.1.0' = 'e07be5e75f14e7b0e72555b596965b6745ed2972'
        'refs/tags/v1.1.1' = '44a0512968dd7a5e3e9b27d05bd85b3d5343208d'
    }
    $refNames = @('refs/heads/main', 'refs/tags/v1.0.0', 'refs/tags/v1.1.0',
                  'refs/tags/v1.1.1', 'refs/tags/v1.1.2')
    $newRefs = @{}
    foreach ($ref in $refNames) {
        $newRefs[$ref] = Invoke-Git -GitArguments @('rev-parse', $ref)
        if ($ref -like 'refs/tags/*') {
            $type = Invoke-Git -GitArguments @('cat-file', '-t', $ref)
            if ($type -ne 'tag') { throw "Annotierter Release-Tag fehlt: $ref" }
        }
    }

    $remoteRefs = Read-RemoteRefs
    if (Test-RefSet -Actual $remoteRefs -Expected $newRefs) {
        Write-Host 'GitHub hat bereits den bereinigten Stand 1.1.2.'
    } else {
        if (-not (Test-RefSet -Actual $remoteRefs -Expected $oldRefs)) {
            throw ('Abbruch: Andere Commits, Tags oder weitere Branches auf dem Remote. ' +
                   'Der Stand wurde nicht veraendert. Siehe GITHUB.md.')
        }
        $pushArguments = @('push', '--atomic')
        foreach ($ref in $refNames) {
            $expected = ''
            if ($oldRefs.ContainsKey($ref)) { $expected = $oldRefs[$ref] }
            $pushArguments += "--force-with-lease=${ref}:$expected"
        }
        $pushArguments += $RemoteUrl
        foreach ($ref in $refNames) { $pushArguments += "${ref}:$ref" }
        Invoke-Git -GitArguments $pushArguments
        if (-not (Test-RefSet -Actual (Read-RemoteRefs) -Expected $newRefs)) {
            throw 'Die abschliessende Remote-Pruefung ist fehlgeschlagen.'
        }
        Write-Host 'main und alle vier Release-Tags sind auf dem bereinigten Stand.'
    }

    $remotes = @(Invoke-Git -GitArguments @('remote'))
    if ($remotes -contains 'origin') {
        $originUrl = Invoke-Git -GitArguments @('remote', 'get-url', 'origin')
        if ($originUrl -ne $RemoteUrl) {
            Write-Host 'Der vorhandene origin bleibt erhalten. Fuer weitere Befehle die URL pruefen.'
        }
    } else {
        Invoke-Git -GitArguments @('remote', 'add', 'origin', $RemoteUrl)
    }
    Write-Host 'Die weiteren Schritte zu Releases und alten lokalen Kopien stehen in GITHUB.md.'
} finally {
    Pop-Location
}
