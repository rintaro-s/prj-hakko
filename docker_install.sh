#!/bin/bash

# スクリプトの実行チェック
if [ "$EUID" -ne 0 ]; then
  echo "このスクリプトはroot権限で実行する必要があります。sudoを使って実行してください。"
  exit 1
fi

echo "--- Dockerのインストールを開始します ---"

# 1. 既存のDockerバージョンのアンインストール（オプション）
echo "既存のDocker関連パッケージをアンインストールします（もしあれば）。"
apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null
echo "アンインストールが完了しました。"

# 2. 必要なパッケージのインストール
echo "必要なパッケージをインストールします..."
apt update
apt install -y ca-certificates curl gnupg
if [ $? -ne 0 ]; then
  echo "必要なパッケージのインストールに失敗しました。スクリプトを終了します。"
  exit 1
fi
echo "必要なパッケージのインストールが完了しました。"

# 3. Dockerの公式GPGキーの追加
echo "Dockerの公式GPGキーを追加します..."
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
if [ $? -ne 0 ]; then
  echo "GPGキーの追加に失敗しました。スクリプトを終了します。"
  exit 1
fi
echo "GPGキーの追加が完了しました。"

# 4. Dockerリポジトリの追加
echo "Dockerリポジトリを追加します..."
echo \
  "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
  tee /etc/apt/sources.list.d/docker.list > /dev/null
if [ $? -ne 0 ]; then
  echo "Dockerリポジトリの追加に失敗しました。スクリプトを終了します。"
  exit 1
fi
echo "Dockerリポジトリの追加が完了しました。"

# 5. Docker Engineのインストール
echo "Docker Engine、Containerd、Docker Composeをインストールします..."
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
if [ $? -ne 0 ]; then
  echo "Docker Engineのインストールに失敗しました。スクリプトを終了します。"
  exit 1
fi
echo "Docker Engineのインストールが完了しました。"

# 6. Dockerの動作確認
echo "Dockerの動作確認のために 'hello-world' イメージを実行します..."
docker run hello-world
if [ $? -ne 0 ]; then
  echo "Dockerの動作確認に失敗しました。問題がある可能性があります。"
else
  echo "Dockerは正常に動作しているようです。"
fi

# 7. sudoなしでDockerを実行するための設定（オプション）
read -p "sudoなしでDockerコマンドを実行できるようにしますか？ (y/N): " choice
case "$choice" in
  y|Y )
    echo "現在のユーザー ($SUDO_USER または $USER) を docker グループに追加します..."
    usermod -aG docker ${SUDO_USER:-$USER}
    echo "変更を有効にするには、一度ログアウトして再度ログインするか、システムを再起動してください。"
    ;;
  * )
    echo "sudoなしでDockerを実行する設定はスキップされました。"
    ;;
esac

echo "--- Dockerのインストールが完了しました！ ---"