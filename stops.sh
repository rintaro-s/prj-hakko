#!/bin/bash

echo "🛑  AI Transporter を停止します..."

# 実行中のDockerコンテナを探して停止
CONTAINER_ID=$(docker ps -q --filter ancestor=-receiver)
if [ -n "$CONTAINER_ID" ]; then
    echo "受信クライアントのコンテナを停止します..."
    docker stop $CONTAINER_ID
fi

# Vagrant仮想マシンを停止
echo "Windows仮想マシンをシャットダウンします..."
vagrant halt

echo "✅ 停止処理が完了しました。"
