# -*- mode: ruby -*-
# vi: set ft=ruby :

# --- 起動引数をチェックして、GUIを表示するかどうかを自動で判断する ---
# `vagrant up` (初回) の時は true になり、
# `vagrant up --no-provision` (2回目以降) の時は false になる
show_gui = !ARGV.include?('--no-provision')

Vagrant.configure("2") do |config|
  # --- 基本設定 ---
  config.vm.box = "generic/windows11"
  config.vm.communicator = "winrm"

  # --- 仮想マシンのスペック ---
  config.vm.provider "virtualbox" do |vb|
    # ★上の判断結果を使って、GUIの表示・非表示を自動で切り替える！
    vb.gui = show_gui
    vb.memory = "4096"
    vb.cpus = "2"
    vb.auto_install_guest_additions = true
  end

  # --- ネットワーク設定 ---
  # 環境に合わせて変更して (例: enp3s0)
  config.vm.network "public_network", bridge: "enp1s0"

  # --- ファイルの同期 ---
  config.vm.synced_folder "sender_app", "C:/vagrant/sender_app"
  config.vm.synced_folder "install_files", "C:/vagrant/install_files"

  # --- プロビジョニング (自動設定) ---
  config.vm.provision "powershell", path: "setup_windows.ps1"

  # --- WinRMの設定 ---
  config.winrm.username = "vagrant"
  config.winrm.password = "vagrant"
  config.winrm.transport = :plaintext
  config.winrm.execution_time_limit = "PT2H"
end
