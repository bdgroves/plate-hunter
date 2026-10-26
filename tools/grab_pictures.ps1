<#
Plate Hunter: download plate pictures that GitHub's servers can't get.

Some agency sites (Illinois's, for one) refuse GitHub's runners, so those plates still show a drawn
stand-in. This reads the game's plate lists straight from GitHub, downloads every picture that is
still waiting ("img_url"), and saves it under Downloads\plate-pictures\<STATE>\<plate id>.<ext>.
Then upload the state folder(s) to https://github.com/bdgroves/plate-hunter/upload/main/incoming
and the fetch-pictures workflow does the rest (see incoming/README.md).

Run it without saving anything (add -State IL to do just one state):
    & ([scriptblock]::Create((irm https://raw.githubusercontent.com/bdgroves/plate-hunter/main/tools/grab_pictures.ps1)))
Plain Windows PowerShell 5.1 or later; nothing to install. It only downloads; it changes nothing online.
#>
param([string[]]$State = @())

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$raw = 'https://raw.githubusercontent.com/bdgroves/plate-hunter/main'
$out = Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads\plate-pictures'
$ua  = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) plate-hunter'

$collections = Invoke-RestMethod "$raw/data/collections.json"
$got = 0; $failed = 0
foreach ($c in $collections) {
    if ($State.Count -and ($State -notcontains $c.code)) { continue }
    $doc = Invoke-RestMethod "$raw/$($c.file)"
    $waiting = @($doc.plates | Where-Object { $_.img_url })
    if (-not $waiting.Count) { continue }
    $dir = Join-Path $out $c.code
    New-Item -ItemType Directory -Force -Path $dir | Out-Null
    Write-Host "$($c.code): $($waiting.Count) picture(s) waiting"
    foreach ($p in $waiting) {
        $ext = [IO.Path]::GetExtension(([Uri]$p.img_url).AbsolutePath)
        if ($ext -notmatch '^\.(gif|png|jpe?g|webp)$') { $ext = '.img' }
        $dest = Join-Path $dir ($p.id + $ext)
        try {
            Invoke-WebRequest -Uri $p.img_url -OutFile $dest -UserAgent $ua -UseBasicParsing -TimeoutSec 30
            $got++
        } catch {
            $failed++
            Write-Host "  couldn't get $($p.name): $($_.Exception.Message)" -ForegroundColor Yellow
            Remove-Item $dest -ErrorAction SilentlyContinue
        }
    }
}
Write-Host ""
Write-Host "$got picture(s) saved to $out" -ForegroundColor Green
if ($failed) { Write-Host "$failed couldn't be downloaded from here either." -ForegroundColor Yellow }
if ($got) {
    Write-Host "Next: drag the state folder(s) into https://github.com/bdgroves/plate-hunter/upload/main/incoming"
    Start-Process explorer.exe $out
}
