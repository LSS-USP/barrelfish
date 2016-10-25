# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure("2") do |config|
  config.vm.box = "ubuntu/trusty64"

  config.vm.define "barrelfish_dev" do |barrelfish|

    barrelfish.vm.provider "virtualbox" do |vb|
      # Customize the amount of memory on the VM:
     vb.memory = "2048"
    end

    barrelfish.vm.provision 'shell', privileged: true, keep_color: true, path: 'vagrant/provision.sh'
  end
end
