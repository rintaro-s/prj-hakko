# PowerShellの実行ポリシーを変更してスクリプトを実行できるようにする
Set-ExecutionPolicy Bypass -Scope Process -Force;

# --- Chocolatey (Windowsのパッケージマネージャー) のインストール ---
Write-Host "Installing Chocolatey..."
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# --- Pythonのインストール ---
Write-Host "Installing Python..."
choco install python -y

# Pythonのパスを環境変数に設定（再起動なしで有効にするため）
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$env:Path += ";C:\Python311\Scripts\"
[System.Environment]::SetEnvironmentVariable("Path", $env:Path, "Machine")

# --- 必要なPythonライブラリのインストール ---
Write-Host "Installing Python libraries..."
pip install opencv-python-headless numpy Pillow pywin32 psutil pynput

# --- HAKKO AIのインストール ---
Write-Host "Installing HAKKO AI..."
# サイレントインストールを試みる（/S や /SILENT などはソフトによる）
Start-Process -FilePath "C:\vagrant\install_files\hakkoai.exe" -ArgumentList "/S" -Wait

# --- 送信側アプリをスタートアップに登録 ---
Write-Host "Setting up sender app to auto-start..."
$startupPath = [System.Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startupPath "capture.lnk"
$targetPath = "C:\vagrant\sender_app\capture.py"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $targetPath
$shortcut.Save()

Write-Host "Setup finished! Please restart the VM if needed."
