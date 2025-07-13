#!/bin/bash

echo " Project HAKKO Transporter 初回セットアップを開始します..."

# --- 必要なツールのインストール ---
echo "🔧 VagrantとVirtualBoxをインストール中..."
sudo apt update
sudo apt install -y vagrant virtualbox

# --- 必要なファイルのチェック ---
if [ ! -f "install_files/win11.iso" ]; then
    echo " エラー: install_files/win11.iso が見つかりません。"
    exit 1
fi
if [ ! -f "install_files/hakko_ai_setup.exe" ]; then
    echo " エラー: install_files/hakko_ai_setup.exe が見つかりません。"
    exit 1
fi

# --- VagrantでWindows仮想マシンを起動＆プロビジョニング ---
echo " VagrantでWindows仮想マシンをセットアップ中... (これには数時間かかることがあります)"
vagrant up

if [ $? -ne 0 ]; then
    echo " Vagrantのセットアップに失敗しました。"
    exit 1
fi

echo " Windows仮想マシンの準備が完了しました！"
echo " 初回セットアップがすべて完了しました！"
echo "次回からは start_hakko.sh を実行してアプリを起動してください。"
