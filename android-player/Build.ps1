param()
$ErrorActionPreference = 'Stop'
$configFile = Join-Path $PSScriptRoot 'toolchain.json'
if (-not (Test-Path -LiteralPath $configFile)) { throw 'Copy toolchain.example.json to toolchain.json and set your local tool paths. See README.md.' }
$config = Get-Content -LiteralPath $configFile -Raw | ConvertFrom-Json
$androidRoot = $config.source_alias
if (-not $androidRoot) { $androidRoot = $PSScriptRoot }
$build = Join-Path $androidRoot 'build'
$releases = Join-Path $androidRoot 'releases'
New-Item -ItemType Directory -Path $build,$releases,(Join-Path $build 'generated'),(Join-Path $build 'classes'),(Join-Path $build 'dex') -Force | Out-Null
$env:JAVA_HOME = $config.java_home
$javaBin = Join-Path $config.java_home 'bin'
$env:PATH = "$javaBin;$env:PATH"
$tools = $config.build_tools
function Run-Checked([string]$program,[object[]]$arguments) {
    & $program @arguments
    if ($LASTEXITCODE -ne 0) { throw "$program failed with exit code $LASTEXITCODE" }
}
Run-Checked (Join-Path $tools 'aapt2.exe') @('compile','--dir',(Join-Path $androidRoot 'app/src/main/res'),'-o',(Join-Path $build 'resources.zip'))
Run-Checked (Join-Path $tools 'aapt2.exe') @('link','-o',(Join-Path $build 'resources.apk'),'-I',$config.platform_jar,'--manifest',(Join-Path $androidRoot 'app/src/main/AndroidManifest.xml'),'--java',(Join-Path $build 'generated'),'-A',(Join-Path $androidRoot 'app/src/main/assets'),'-0','wav','--min-sdk-version','26','--target-sdk-version','35',(Join-Path $build 'resources.zip'))
$sources = @(Get-ChildItem -LiteralPath (Join-Path $androidRoot 'app/src/main/java'),(Join-Path $build 'generated') -Recurse -Filter '*.java' | ForEach-Object { '"' + $_.FullName.Replace('\','/') + '"' })
[IO.File]::WriteAllLines((Join-Path $build 'sources.txt'),$sources,[Text.UTF8Encoding]::new($false))
$bootClasspath = $config.platform_jar + ';' + (Join-Path $tools 'core-lambda-stubs.jar')
Run-Checked (Join-Path $javaBin 'javac.exe') @('-encoding','UTF-8','-source','8','-target','8','-Xlint:-options','-bootclasspath',$bootClasspath,'-d',(Join-Path $build 'classes'),('@'+(Join-Path $build 'sources.txt')))
Run-Checked (Join-Path $javaBin 'jar.exe') @('--create','--file',(Join-Path $build 'classes.jar'),'-C',(Join-Path $build 'classes'),'.')
Run-Checked (Join-Path $javaBin 'java.exe') @('-cp',(Join-Path $tools 'lib\d8.jar'),'com.android.tools.r8.D8','--lib',$config.platform_jar,'--min-api','26','--output',(Join-Path $build 'dex'),(Join-Path $build 'classes.jar'))
$pythonExe = if ($config.python_exe) { $config.python_exe } else { 'python' }
Run-Checked $pythonExe @((Join-Path $androidRoot 'tools/merge_apk.py'),(Join-Path $build 'resources.apk'),(Join-Path $build 'dex/classes.dex'),(Join-Path $build 'unsigned.apk'))
Run-Checked (Join-Path $tools 'zipalign.exe') @('-p','-f','4',(Join-Path $build 'unsigned.apk'),(Join-Path $build 'aligned.apk'))
$keystore = if ($config.keystore) { $config.keystore } else { Join-Path $env:USERPROFILE '.android/ee475-development.jks' }
$keyFolder=Split-Path -Parent $keystore
New-Item -ItemType Directory -Path $keyFolder -Force | Out-Null
if (-not (Test-Path -LiteralPath $keystore)) {
    Run-Checked (Join-Path $javaBin 'keytool.exe') @('-genkeypair','-keystore',$keystore,'-alias','ee475-beacon','-keyalg','RSA','-keysize','2048','-validity','10000','-storepass','android','-keypass','android','-dname','CN=EE475 Development, OU=Project, O=EE475, C=US')
}
$apk=Join-Path $releases 'BeaconLoop-1.1.apk'
Run-Checked (Join-Path $tools 'apksigner.bat') @('sign','--ks',$keystore,'--ks-key-alias','ee475-beacon','--ks-pass','pass:android','--key-pass','pass:android','--out',$apk,(Join-Path $build 'aligned.apk'))
Run-Checked (Join-Path $tools 'apksigner.bat') @('verify','--verbose',$apk)
Run-Checked (Join-Path $tools 'zipalign.exe') @('-c','4',$apk)
Write-Output "APK ready: $apk"
