#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conans import ConanFile, tools
from conans.errors import ConanException, ConanInvalidConfiguration
import os
import shutil


class AndroidNDKConan(ConanFile):
    name = "android-ndk"
    version = "r21e"
    description = "The Android NDK is a toolset that lets you implement parts of your app in native code, " \
                  "using languages such as C and C++"
    url = "https://github.com/Tereius/conan-android-ndk"
    homepage = "https://developer.android.com/ndk/"
    license = "GNU GPL"
    exports = ["LICENSE", "android.toolchain.conan.cmake"]
    short_paths = True
    no_copy_source = True
    options = {"makeStandalone": [True, False]}
    default_options = "makeStandalone=True"
    settings = "os", "arch", "compiler", "os_build", "arch_build"

    supported_clang_version = "9"
    max_supported_api_level = 30

    def __getattr_recursive(self, obj, name, default):
        if obj is None:
            return default
        split_names = name.split('.')
        depth = len(split_names)
        if depth == 1:
            return getattr(obj, name, default)
        return self.__getattr_recursive(getattr(obj, split_names[0], default), ".".join(split_names[1:]), default)

    def isSingleProfile(self):
        settings_target = getattr(self, 'settings_target', None)
        if settings_target is None:
            return True
        return False

    def get_setting(self, name: str):
        is_build_setting = name.endswith('_build')
        depth = len(name.split('.'))
        settings_target = getattr(self, 'settings_target', None)
        if settings_target is None:
            # It is running in 'host' context
            setting_val = self.__getattr_recursive(self.settings, name, None)
            if setting_val is None:
                raise ConanInvalidConfiguration("Setting in host context with name %s is missing. Make sure to provide it in your conan host profile." % name)
            return setting_val
        else:
            # It is running in 'build' context and it is being used as a build requirement
            setting_name = name.replace('_build', '')
            if is_build_setting:
                setting_val = self.__getattr_recursive(self.settings, setting_name, None)
            else:
                setting_val = self.__getattr_recursive(settings_target, setting_name, None)
            if setting_val is None:
                raise ConanInvalidConfiguration("Setting in build context with name %s is missing. Make sure to provide it in your conan %s profile." % (setting_name, "build" if is_build_setting else "host"))
            return setting_val

    def configure(self):
        if self.get_setting("os_build") not in ["Windows", "Macos", "Linux"]:
            raise ConanException("Unsupported build os: %s. Supported are: Windows, Macos, Linux" % self.get_setting("os_build"))
        if self.get_setting("arch_build") != "x86_64":
            raise ConanException("Unsupported build arch: %s. Supported is: x86_64" % self.get_setting("arch_build"))
        if self.get_setting("arch") in ["x86_64", "armv8"] and int(str(self.get_setting("os.api_level"))) < 21:
            raise ConanException("Minumum API version for architecture %s is 21" % str(self.get_setting("arch")))
        if int(str(self.get_setting("os.api_level"))) > self.max_supported_api_level:
            raise ConanException("Maximum API version for is " + str(self.max_supported_api_level))
        if self.get_setting("compiler") == "clang" and not self.get_setting("compiler.libcxx") in ["libc++", "libstdc++"]:
            raise ConanException("Unsupported libcxx")
        if self.get_setting("compiler") == "clang" and str(
                self.get_setting("compiler.version")) != self.supported_clang_version:
            raise ConanException("Only clang version " + self.supported_clang_version + " is supported")

    def source(self):
        source_url = "https://dl.google.com/android/repository/android-ndk-{0}-{1}-{2}.zip".format(self.version,
                                                                                                   self.os_name,
                                                                                                   self.get_setting("arch_build"))
        tools.get(source_url, keep_permissions=True)

    @property
    def os_name(self):
        return {"Windows": "windows",
                "Macos": "darwin",
                "Linux": "linux"}.get(str(self.get_setting("os_build")))

    @property
    def android_short_arch(self):
        return {"armv7": "arm",
                "armv8": "arm",
                "x86": "x86",
                "x86_64": "x86"}.get(str(self.get_setting("arch")))

    @property
    def android_arch(self):
        return {"armv7": "arm",
                "armv8": "arm64",
                "x86": "x86",
                "x86_64": "x86_64"}.get(str(self.get_setting("arch")))

    @property
    def android_abi(self):
        return {"armv7": "armeabi-v7a",
                "armv8": "arm64-v8a",
                "x86": "x86",
                "x86_64": "x86_64"}.get(str(self.get_setting("arch")))

    @property
    def android_stdlib(self):
        return {"libc++": "c++_shared",
                "c++_shared": "c++_shared",
                "c++_static": "c++_static"}.get(str(self.get_setting("compiler.libcxx")))

    @property
    def abi(self):
        return 'androideabi' if self.android_arch == 'arm' else 'android'

    @property
    def triplet(self):
        arch = {'arm': 'arm',
                'arm64': 'aarch64',
                'x86': 'i686',
                'x86_64': 'x86_64'}.get(self.android_arch)
        return '%s-linux-%s' % (arch, self.abi)

    def build(self):

        ndk = "android-ndk-%s" % self.version
        if self.options.makeStandalone:
            make_standalone_toolchain = os.path.join(self.source_folder,
                                                     ndk, 'build', 'tools', 'make_standalone_toolchain.py')

            if str(self.get_setting("compiler.libcxx")) == 'libc++':
                stl = 'libc++'
            else:
                stl = 'gnustl'

            python = tools.which('python')
            command = '"%s" %s --arch %s --api %s --stl %s --install-dir %s' % (python,
                                                                                make_standalone_toolchain,
                                                                                self.android_arch,
                                                                                str(self.get_setting("os.api_level")),
                                                                                stl,
                                                                                self.package_folder)

            self.run(command)
            if self.get_setting("os_build") == 'Windows':
                # workaround Windows CMake Clang detection (Determine-Compiler-Standalone.cmake)
                if self.get_setting("compiler") == 'clang':
                    with tools.chdir(os.path.join(self.package_folder, 'bin')):
                        shutil.copy('clang90.exe', 'clang.exe')
                        shutil.copy('clang90++.exe', 'clang++.exe')
            else:
                def chmod_plus_x(filename):
                    os.chmod(filename, os.stat(filename).st_mode | 0o111)

                for root, _, files in os.walk(self.package_folder):
                    for filename in files:
                        filename = os.path.join(root, filename)
                        with open(filename, 'rb') as f:
                            sig = f.read(4)
                            if type(sig) is str:
                                sig = [ord(s) for s in sig]
                            if len(sig) > 2 and sig[0] == 0x23 and sig[1] == 0x21:
                                self.output.info('chmod on script file: "%s"' % filename)
                                chmod_plus_x(filename)
                            elif sig == [0x7F, 0x45, 0x4C, 0x46]:
                                self.output.info('chmod on ELF file: "%s"' % filename)
                                chmod_plus_x(filename)
                            elif \
                                    sig == [0xCA, 0xFE, 0xBA, 0xBE] or \
                                            sig == [0xBE, 0xBA, 0xFE, 0xCA] or \
                                            sig == [0xFE, 0xED, 0xFA, 0xCF] or \
                                            sig == [0xCF, 0xFA, 0xED, 0xFE] or \
                                            sig == [0xFE, 0xEF, 0xFA, 0xCE] or \
                                            sig == [0xCE, 0xFA, 0xED, 0xFE]:
                                self.output.info('chmod on Mach-O file: "%s"' % filename)
                                chmod_plus_x(filename)
        else:
            shutil.copytree(self.source_folder + "/" + ndk, self.package_folder)

    def package(self):
        self.copy(pattern="LICENSE", dst="license", src='.')
        if not self.options.makeStandalone:
            self.copy(pattern="android.toolchain.conan.cmake", dst="build/cmake", src='.')

    def tool_name(self, tool):
        if 'clang' in tool:
            suffix = '.cmd' if self.get_setting("os_build") == 'Windows' else ''
        else:
            suffix = '.exe' if self.get_setting("os_build") == 'Windows' else ''
        return '%s-%s%s' % (self.triplet, tool, suffix)

    def define_tool_var(self, name, value, ndk_bin):
        path = os.path.join(ndk_bin, self.tool_name(value))
        self.output.info('Creating %s environment variable: %s' % (name, path))
        return path

    def package_id(self):
        if self.isSingleProfile():
            self.info.include_build_settings()

    def package_info(self):
        ndk_root = self.package_folder
        if self.options.makeStandalone:
            ndk_bin = os.path.join(ndk_root, 'bin')

        self.output.info(
            'Creating NDK_ROOT, ANDROID_NDK_ROOT, ANDROID_NDK_HOME, CONAN_CMAKE_ANDROID_NDK environment variable: %s' % ndk_root)
        self.env_info.NDK_ROOT = ndk_root
        self.env_info.ANDROID_NDK_ROOT = ndk_root
        self.env_info.ANDROID_NDK_HOME = ndk_root
        self.env_info.CMAKE_ANDROID_NDK = ndk_root

        self.output.info('Creating CHOST environment variable: %s' % self.triplet)
        self.env_info.CHOST = self.triplet

        # self.output.info('Creating ANDROID_TOOLCHAIN_VERSION environment variable: %s' % self.toolchain_version)
        # self.env_info.ANDROID_TOOLCHAIN_VERSION = self.toolchain_version
        # self.env_info.TOOLCHAIN_VERSION = self.toolchain_version

        if self.options.makeStandalone:
            self.output.info('Appending PATH environment variable: %s' % ndk_bin)
            self.env_info.PATH.append(ndk_bin)
        else:
            toolchain = os.path.join(ndk_root, "build", "cmake", "android.toolchain.conan.cmake")
            self.output.info('Creating CONAN_CMAKE_TOOLCHAIN_FILE environment variable: %s' % toolchain)
            self.env_info.CONAN_CMAKE_TOOLCHAIN_FILE = toolchain
            self.env_info.CONAN_ANDROID_STL = self.android_stdlib
            self.env_info.CONAN_ANDROID_ABI = self.android_abi
            self.env_info.CONAN_ANDROID_TOOLCHAIN = self.get_setting("compiler")
            self.env_info.CONAN_ANDROID_PLATFORM = "android-" + str(self.get_setting("os.api_level"))

        ndk_sysroot = os.path.join(ndk_root, 'sysroot')

        self.output.info('Creating CONAN_CMAKE_FIND_ROOT_PATH environment variable: %s' % ndk_sysroot)
        self.env_info.CONAN_CMAKE_FIND_ROOT_PATH = ndk_sysroot

        self.output.info('Creating SYSROOT environment variable: %s' % ndk_sysroot)
        self.env_info.SYSROOT = ndk_sysroot

        self.output.info('Creating self.cpp_info.sysroot: %s' % ndk_sysroot)
        self.cpp_info.sysroot = ndk_sysroot

        if self.options.makeStandalone:
            self.env_info.CC = self.define_tool_var('CC', 'clang', ndk_bin)
            self.env_info.CXX = self.define_tool_var('CXX', 'clang++', ndk_bin)
            self.env_info.AS = self.define_tool_var('AS', 'clang', ndk_bin)
            self.env_info.LD = self.define_tool_var('LD', 'ld', ndk_bin)
            self.env_info.AR = self.define_tool_var('AR', 'ar', ndk_bin)
            self.env_info.RANLIB = self.define_tool_var('RANLIB', 'ranlib', ndk_bin)
            self.env_info.STRIP = self.define_tool_var('STRIP', 'strip', ndk_bin)
            self.env_info.NM = self.define_tool_var('NM', 'nm', ndk_bin)
            self.env_info.ADDR2LINE = self.define_tool_var('ADDR2LINE', 'addr2line', ndk_bin)
            self.env_info.OBJCOPY = self.define_tool_var('OBJCOPY', 'objcopy', ndk_bin)
            self.env_info.OBJDUMP = self.define_tool_var('OBJDUMP', 'objdump', ndk_bin)
            self.env_info.READELF = self.define_tool_var('READELF', 'readelf', ndk_bin)
            self.env_info.ELFEDIT = self.define_tool_var('ELFEDIT', 'elfedit', ndk_bin)
        else:
            self.output.info('Creating self.cpp_info.builddirs: %s' % os.path.join(ndk_root, 'build'))
            self.cpp_info.builddirs = [os.path.join(ndk_root, 'build')]
