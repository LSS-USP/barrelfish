#!/bin/bash

set -x

sudo apt-get install -y build-essential bison flex cmake gcc-multilib qemu-system-x86 qemu-system-arm ghc libghc-src-exts-dev libghc-ghc-paths-dev libghc-parsec3-dev libghc-random-dev libghc-ghc-mtl-dev libghc-src-exts-dev libghc-async-dev gcc-arm-linux-gnueabi g++-arm-linux-gnueabi libgmp3-dev cabal-install curl freebsd-glue libelf-freebsd-dev

cabal install bytestring-trie

mkdir -p /vagrant/build
cd /vagrant/build

../hake/hake.sh -s .. -a x86_64

make X86_64_Basic
