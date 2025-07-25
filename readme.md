# Project Transporter

## これは何？

Windowsでしか動かない「」みたいなアプリを、コマンド一発でUbuntu上に表示させるためのツールです。  

---

## 特徴

- **全自動セットアップ**  
  `win11.iso` とアプリの `.exe`を所定の場所に置いたら、あとはスクリプトを実行するだけです。

---

## 必要なもの

このプロジェクトを動かすには、あらかじめUbuntuに以下のソフトウェアをインストールしておく必要があります。

- Vagrant
- VirtualBox
- Docker

`install.sh` を実行すれば、VagrantとVirtualBoxは自動でインストールを試みます。

---

## 使い方

### ファイルの準備

`install_files/` フォルダに、`green_background.png`(←(0, 255, 0)の緑で) と`win11.iso` と `_ai_setup.exe` （←英語、日本、中国版でインストーラーの名前が違うのでこの名前に統一してください）を入れてください。

---

### 初回インストール

ターミナルでこのプロジェクトのフォルダに移動して、以下のコマンドを実行します。  
Windowsのインストールから始まるので、完了までにはかなり時間がかかります。インストール画面が表示されたら、手動でOSとアプリのセットアップを進めてください。

```bash
chmod +x install.sh
./install.sh
```

---

### 2回目以降の起動

初回セットアップが終わった後、アプリを起動したいときは、いつでもこのコマンドを実行します。

```bash
chmod +x .sh
./start_.sh
```

これで、裏でWindowsが起動し、Ubuntuのデスクトップにアプリの画面が表示されます。

---

## 各スクリプトの役割

- **install.sh**  
  必要なツールをインストールし、Vagrantを使ってWindows仮想環境の初回セットアップを行います。最初に一度だけ実行するスクリプトです。

- **start_.sh**  
  セットアップ済みのWindows仮想環境をバックグラウンドで起動し、Ubuntu側で表示用クライアントを立ち上げます。普段使い用のスクリプトです。

- **stop_.sh**  
  起動しているアプリと仮想環境を、安全に両方ともシャットダウンします。

---

## 注意点

- `Vagrantfile` の中のネットワーク設定 (`config.vm.network`) は、自分の環境に合わせて変更する必要があります。
- Windowsアプリのインストーラーによっては、`setup_windows.ps1` の中のサイレントインストール用のコマンドを調整する必要があります。
- 使用しているデスクトップ環境がWaylandの場合は、キャラクタの移動及びレンダリングが乱れる/できない可能性があります。
