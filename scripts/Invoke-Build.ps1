param(
    [Parameter(Mandatory=$true)][string]$BuildJdk,
    [Parameter(Mandatory=$true)][string]$CompileJdk,
    [Parameter(Mandatory=$true)][string]$GameJdk,
    [string[]]$Tasks = @('build'),
    [string]$CacheDirectory = '.work/gradle-home'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
foreach ($jdk in @($BuildJdk, $CompileJdk, $GameJdk)) {
    if (!(Test-Path -LiteralPath (Join-Path $jdk 'bin/javac.exe'))) { throw "Missing JDK compiler: $jdk" }
}
if ((Get-Content (Join-Path $BuildJdk 'release') -Raw) -notmatch 'JAVA_VERSION="17\.') { throw 'BuildJdk must be JDK 17' }
if ((Get-Content (Join-Path $CompileJdk 'release') -Raw) -notmatch 'JAVA_VERSION="1\.8\.') { throw 'CompileJdk must be JDK 8' }
if ((Get-Content (Join-Path $GameJdk 'release') -Raw) -notmatch 'JAVA_VERSION="1\.7\.') { throw 'GameJdk must be JDK 7' }
$previousJavaHome = $env:JAVA_HOME
Push-Location $root
try {
    $env:JAVA_HOME = (Resolve-Path -LiteralPath $BuildJdk).Path
    $toolchains = @($BuildJdk, $CompileJdk, $GameJdk | ForEach-Object { (Resolve-Path -LiteralPath $_).Path }) -join ','
    $java7Path = (Resolve-Path -LiteralPath $GameJdk).Path
    & .\gradlew.bat --no-daemon --gradle-user-home $CacheDirectory "-Porg.gradle.java.installations.paths=$toolchains" "-Pjava7Home=$java7Path" @Tasks
    if ($LASTEXITCODE -ne 0) { throw "Gradle failed: $LASTEXITCODE" }
} finally {
    $env:JAVA_HOME = $previousJavaHome
    Pop-Location
}
