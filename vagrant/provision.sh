#!/bin/bash

set -x

# Required packages for compile barrelfish
packages=$(echo `cat /vagrant/vagrant/packages_install.txt`)
sudo apt-get update
sudo apt-get install -y $packages

# Prepare cabal
if [[ ! -f ~/.cabal/config ]]; then
  local message="Cabal is not installed"
  command -v cabal >/dev/null 2>&1 || { echo >&2 $message; exit 1; }
  cabal init -n -m
  cp ~/.cabal/config ~/.config/config_bkp
  sed -e '/remote-repo:/s/^/--/' -i ~/.cabal/config
  sed '/remote-repo/a remote-repo: hackage.fpcomplete.com:http://hackage.fpcomplete.com/' -i ~/.cabal/config
fi

cabal update
cabal install bytestring-trie

# Prepare to compile
mkdir -p /vagrant/build
cd /vagrant/build

../hake/hake.sh -s .. -a x86_64

sudo make X86_64_Basic
