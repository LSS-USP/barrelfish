##########################################################################
# Copyright (c) 2009-2016 ETH Zurich.
# All rights reserved.
#
# This file is distributed under the terms in the attached LICENSE file.
# If you do not find this file, copies can be found by writing to:
# ETH Zurich D-INFK, Universitaetstr. 6, CH-8092 Zurich. Attn: Systems Group.
##########################################################################

import os, signal, tempfile, subprocess, shutil
import debug, machines
from machines import Machine, ARMMachineBase

QEMU_SCRIPT_PATH = 'tools/qemu-wrapper.sh' # relative to source tree
GRUB_IMAGE_PATH = 'tools/grub-qemu.img' # relative to source tree
QEMU_CMD_X64 = 'qemu-system-x86_64'
QEMU_CMD_X32 = 'qemu-system-i386'
QEMU_CMD_ARM = 'qemu-system-arm'
QEMU_ARGS_GENERIC = '-nographic -no-reboot'.split()
QEMU_ARGS_X64 = '-net nic,model=ne2k_pci -net user -m 3084'.split()
QEMU_ARGS_X32 = '-net nic,model=ne2k_pci -net user -m 512'.split()

class QEMUMachineBase(Machine):
    def __init__(self, options):
        super(QEMUMachineBase, self).__init__(options)
        self.child = None
        self.tftp_dir = None
        self.options = options

    def setup(self):
        pass

    def get_coreids(self):
        return range(0, self.get_ncores())

    def get_tickrate(self):
        return None

    def get_buildall_target(self):
        return self.get_bootarch().upper() + "_Full"

    def get_boot_timeout(self):
        # shorter time limit for running a qemu test
        # FIXME: ideally this should somehow be expressed in CPU time / cycles
        return 60

    def get_machine_name(self):
        return self.name

    def get_serial_binary(self):
        return "serial_pc16550d"

    def force_write(self, consolectrl):
        pass

    def get_tftp_dir(self):
        if self.tftp_dir is None:
            debug.verbose('creating temporary directory for QEMU TFTP files')
            self.tftp_dir = tempfile.mkdtemp(prefix='harness_qemu_')
            debug.verbose('QEMU TFTP directory is %s' % self.tftp_dir)
        return self.tftp_dir

    def _write_menu_lst(self, data, path):
        debug.verbose('writing %s' % path)
        debug.debug(data)
        f = open(path, 'w')
        f.write(data)
        f.close()

    def set_bootmodules(self, modules):
        path = os.path.join(self.get_tftp_dir(), 'menu.lst')
        self._write_menu_lst(modules.get_menu_data('/'), path)

    def lock(self):
        pass

    def unlock(self):
        pass

    def _get_cmdline(self):
        raise NotImplementedError

    def _kill_child(self):
        # terminate child if running
        if self.child:
            os.kill(self.child.pid, signal.SIGTERM)
            self.child.wait()
            self.child = None
        self.masterfd = None

    def reboot(self):
        self._kill_child()
        cmd = self._get_cmdline()
        debug.verbose('starting "%s"' % ' '.join(cmd))
        import pty
        (self.masterfd, slavefd) = pty.openpty()
        self.child = subprocess.Popen(cmd, close_fds=True,
                                      stdout=slavefd,
                                      stdin=slavefd)
        os.close(slavefd)
        # open in binary mode w/o buffering
        self.qemu_out = os.fdopen(self.masterfd, 'rb', 0)

    def shutdown(self):
        self._kill_child()
        # try to cleanup tftp tree if needed
        if self.tftp_dir and os.path.isdir(self.tftp_dir):
            shutil.rmtree(self.tftp_dir, ignore_errors=True)
        self.tftp_dir = None

    def get_output(self):
        return self.qemu_out

class QEMUMachineX64(QEMUMachineBase):
    def _get_cmdline(self):
        qemu_wrapper = os.path.join(self.options.sourcedir, QEMU_SCRIPT_PATH)
        menu_lst = os.path.join(self.get_tftp_dir(), 'menu.lst')
        return [ qemu_wrapper, "--menu", menu_lst, "--arch", "x86_64",
                "--smp", "%s" % self.get_ncores() ]

    def set_bootmodules(self, modules):
        path = os.path.join(self.get_tftp_dir(), 'menu.lst')
        self._write_menu_lst(modules.get_menu_data('/', self.get_tftp_dir()), path)

    def get_bootarch(self):
        return "x86_64"

class QEMUMachineX32(QEMUMachineBase):
    def _get_cmdline(self):
        grub_image = os.path.join(self.options.sourcedir, GRUB_IMAGE_PATH)
        s = '-smp %d -fda %s -tftp %s' % (self.get_ncores(), grub_image,
                                          self.get_tftp_dir())
        return [QEMU_CMD_X32] + QEMU_ARGS_GENERIC + QEMU_ARGS_X32 + s.split()

    def get_bootarch(self):
        return "x86_32"

# create 1, 2 and 4 core x86_64 qemu machines
for n in [1, 2, 4]:
    class TmpMachine(QEMUMachineX64):
        name = 'qemu%d' % n
        cores= n

        def get_ncores(self):
            return self.cores

        # 60 seconds per core
        def get_boot_timeout(self):
            return self.cores * 60

        # 120 seconds per core
        def get_test_timeout(self):
            return self.cores * 120

    machines.add_machine(TmpMachine)

@machines.add_machine
class QEMUMachineX32Uniproc(QEMUMachineX32):
    '''Uniprocessor x86_32 QEMU'''
    name = 'qemu1-32'

    def get_ncores(self):
        return 1

@machines.add_machine
class QEMUMachineX32Multiproc(QEMUMachineX32):
    '''Multiprocessor x86_32 QEMU (4 CPUs)'''
    name = 'qemu4-32'

    def get_ncores(self):
        return 4

@machines.add_machine
class QEMUMachineARMv7Uniproc(QEMUMachineBase, ARMMachineBase):
    '''Uniprocessor ARMv7 QEMU'''
    name = 'qemu_armv7'

    imagename = "armv7_a15ve_1_image"

    def __init__(self, options):
        super(QEMUMachineARMv7Uniproc, self).__init__(options)
        self._set_kernel_image()

    def get_ncores(self):
        return 1

    def get_bootarch(self):
        return "armv7"

    def get_platform(self):
        return 'a15ve'

    def _write_menu_lst(self, data, path):
        ARMMachineBase._write_menu_lst(self, data, path)

    def set_bootmodules(self, modules):
        # write menu.lst
        debug.verbose("Writing menu.lst in build directory.")
        menulst_fullpath = os.path.join(self.options.builds[0].build_dir,
                "platforms", "arm", "menu.lst.armv7_a15ve_1")
        self._write_menu_lst(modules.get_menu_data('/'), menulst_fullpath)

        # produce ROM image
        debug.verbose("Building QEMU image.")
        debug.checkcmd(["make", self.imagename],
                cwd=self.options.builds[0].build_dir)

    def _get_cmdline(self):
        qemu_wrapper = os.path.join(self.options.sourcedir, QEMU_SCRIPT_PATH)

        return ([qemu_wrapper, '--arch', 'a15ve', '--image', self.kernel_img])

@machines.add_machine
class QEMUMachineZynq7(QEMUMachineBase, ARMMachineBase):
    '''Zynq7000 as modelled by QEMU'''
    name = 'qemu_armv7_zynq7'

    imagename = "armv7_zynq7_image"

    def __init__(self, options):
        super(QEMUMachineZynq7, self).__init__(options)
        self._set_kernel_image()
        # XXX: change this once we have proper zynq7 configurations
        self.menulst_template = "menu.lst.armv7_zynq7"

    def get_ncores(self):
        return 1

    def get_bootarch(self):
        return "armv7"

    def get_platform(self):
        return 'zynq7'

    def _write_menu_lst(self, data, path):
        ARMMachineBase._write_menu_lst(self, data, path)

    def set_bootmodules(self, modules):
        # write menu.lst
        debug.verbose("Writing menu.lst in build directory.")
        menulst_fullpath = os.path.join(self.options.builds[0].build_dir,
                "platforms", "arm", "menu.lst.armv7_zynq7")
        self._write_menu_lst(modules.get_menu_data('/'), menulst_fullpath)

        # produce ROM image
        debug.verbose("Building QEMU image.")
        debug.checkcmd(["make", self.imagename],
                cwd=self.options.builds[0].build_dir)

    def _get_cmdline(self):
        qemu_wrapper = os.path.join(self.options.sourcedir, QEMU_SCRIPT_PATH)

        return ([qemu_wrapper, '--arch', 'zynq7', '--image', self.kernel_img])
