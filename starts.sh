#!/bin/bash

echo "  AI Transporter を起動します..."

# --- Windows仮想マシンをバックグラウンドで起動 ---
echo " Windowsをバックグラウンドで起動中..."
# --no-provision をつけることで、初回セットアップの処理をスキップする
vagrant up --no-provision

if [ $? -ne 0 ]; then
    echo "Windowsの起動に失敗しました。"
    exit 1
fi

# --- Dockerで受信側アプリを起動 ---
echo " 受信クライアントを起動中..."

# Xサーバーへのアクセスを許可
xhost +local:docker

# Dockerコンテナを起動
docker run --rm -it \
    --net=host \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix \
    -receiver

if [ $? -ne 0 ]; then
    echo " 受信クライアントの起動に失敗しました。"
    # エラーが発生した場合もVMを停止する
    echo "VMをシャットダウンします..."
    vagrant halt
    exit 1
fi

echo " アプリが終了しました。Windowsをシャットダウンします..."
vagrant halt

echo "すべてのプロセスが完了しました！"
