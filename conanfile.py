#!/usr/bin/env python
# -*- coding: utf-8 -*-

from conan import ConanFile
from conan.tools.system.package_manager import Apt, PacMan
from conan.tools.cmake import CMake, CMakeToolchain
from conan.tools.files import patch, load, download, replace_in_file, copy, get
from conan.tools.build import cross_building, build_jobs
from conan.tools.env import VirtualBuildEnv
from conan.tools.scm import Git
import json, os
import shutil
import configparser
import tempfile
import requests

required_conan_version = ">=2.0"

class AndroidNDKConan(ConanFile):

    supported_clang_version = "14"
    max_supported_api_level = 33

    jsonInfo = json.load(open("info.json", 'r'))
    # ---Package reference---
    name = jsonInfo["projectName"]
    version = jsonInfo["version"]
    user = jsonInfo["domain"]
    channel = "stable"
    # ---Metadata---
    description = jsonInfo["projectDescription"]
    license = jsonInfo["license"]
    author = jsonInfo["vendor"]
    topics = jsonInfo["topics"]
    homepage = jsonInfo["homepage"]
    url = jsonInfo["repository"]
    # ---Requirements---
    requires = []
    tool_requires = []
    # ---Sources---
    exports = ["info.json"]
    exports_sources = []
    # ---Binary model---
    settings = "os", "arch"
    options = {}
    default_options = {}
    # ---Build---
    generators = []
    # ---Folders---
    no_copy_source = True

    @property
    def os_name(self):
        return {"Windows": "windows",
                "Macos": "darwin",
                "Linux": "linux"}.get(str(self.settings.os))

    @property
    def android_short_arch(self):
        return {"armv7": "arm",
                "armv8": "arm",
                "x86": "x86",
                "x86_64": "x86"}.get(str(self.settings_target.arch))

    @property
    def android_arch(self):
        return {"armv7": "arm",
                "armv8": "arm64",
                "x86": "x86",
                "x86_64": "x86_64"}.get(str(self.settings_target.arch))

    @property
    def android_abi(self):
        return {"armv7": "armeabi-v7a",
                "armv8": "arm64-v8a",
                "x86": "x86",
                "x86_64": "x86_64"}.get(str(self.settings_target.arch))

    @property
    def android_stdlib(self):
        return {"libc++": "c++_shared",
                "c++_shared": "c++_shared",
                "c++_static": "c++_static"}.get(str(self.settings_target.compiler.libcxx))

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

    def validate(self):
        if self.settings.arch != "x86_64":
            raise ConanInvalidConfiguration("Unsupported Architecture. This package currently only supports x86_64.")
        if self.settings.os not in ["Windows", "Macos", "Linux"]:
            raise ConanInvalidConfiguration("Unsupported os. This package currently only support Linux/Macos/Windows")

    def system_requirements(self):
        Apt(self).install(["unzip"])
        PacMan(self).install(["unzip"])

    def build(self):
        key = self.settings.os
        if self.settings.os == "Linux":
            # conan unzip ignores symlinks
            download(self, self.conan_data["sources"][self.version][str(key)]["url"], "android-ndk-%s.zip" % self.version)
            self.run("unzip -qq -d %s android-ndk-%s.zip" % (self.source_folder, self.version))
        else:
            get(self, **self.conan_data["sources"][self.version][str(key)], destination=self.source_folder)

    def package(self):
        copy(self, pattern="*", dst=self.package_folder, src=os.path.join(self.source_folder, "android-ndk-%s" % self.version))

    def tool_name(self, tool):
        suffix = ''
        if not 'clang' in tool:
            suffix = '.exe' if self.settings.os == 'Windows' else ''
        proposedName = '%s-%s%s' % (self.triplet, tool, suffix)
        if 'arm' in proposedName and 'clang' in tool:
            proposedName = proposedName.replace('arm', 'armv7a')
        if 'clang' in tool:
            proposedName = proposedName.replace(self.abi, self.abi + str(self.settings_target.os.api_level))
        return proposedName

    def define_tool_var(self, name, value, ndk_bin):
        path = os.path.join(ndk_bin, self.tool_name(value))
        self.output.info('Creating %s environment variable: %s' % (name, path))
        return path

    def package_info(self):
        ndk_root = self.package_folder
        ndk_bin = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', '%s-%s' % (self.os_name, self.settings.arch), 'bin')
        ndk_sysroot = os.path.join(ndk_root, 'toolchains', 'llvm', 'prebuilt', '%s-%s' % (self.os_name, self.settings.arch), 'sysroot')

        self.output.info(
            'Creating NDK_ROOT, ANDROID_NDK_ROOT environment variable: %s' % ndk_root)
        self.buildenv_info.define_path("NDK_ROOT", ndk_root)
        self.buildenv_info.define_path("ANDROID_NDK_ROOT", ndk_root)

        self.output.info('Creating CHOST environment variable: %s' % self.triplet)
        self.buildenv_info.define("CHOST", self.triplet)

        # self.output.info('Creating ANDROID_TOOLCHAIN_VERSION environment variable: %s' % self.toolchain_version)
        # self.env_info.ANDROID_TOOLCHAIN_VERSION = self.toolchain_version
        # self.env_info.TOOLCHAIN_VERSION = self.toolchain_version

        self.output.info('Prepending to PATH environment variable: %s' % ndk_bin)
        self.buildenv_info.prepend_path("PATH", ndk_bin)

        self.conf_info.define("tools.android:ndk_path", ndk_root)
        self.conf_info.define("tools.android:cmake_legacy_toolchain", False)

        #self.env_info.CONAN_ANDROID_STL = self.android_stdlib
        #self.env_info.CONAN_ANDROID_ABI = self.android_abi
        #self.env_info.CONAN_ANDROID_TOOLCHAIN = str(self.get_setting("compiler"))
        #self.env_info.CONAN_ANDROID_PLATFORM = "android-" + str(self.get_setting("os.api_level"))

        #self.output.info('Creating CONAN_CMAKE_FIND_ROOT_PATH environment variable: %s' % ndk_sysroot)
        #self.env_info.CONAN_CMAKE_FIND_ROOT_PATH = ndk_sysroot

        self.output.info('Creating SYSROOT environment variable: %s' % ndk_sysroot)
        self.buildenv_info.define_path("SYSROOT", ndk_sysroot)

        #self.output.info('Creating self.cpp_info.sysroot: %s' % ndk_sysroot)
        #self.cpp_info.sysroot = ndk_sysroot

        self.buildenv_info.define_path("CXX", self.define_tool_var('CXX', 'clang++', ndk_bin))
        self.buildenv_info.define_path("CC", self.define_tool_var('CC', 'clang', ndk_bin))
        self.buildenv_info.define_path("AS", self.define_tool_var('AS', 'clang', ndk_bin))
        self.buildenv_info.define_path("LD", self.define_tool_var('LD', 'clang', ndk_bin))
        self.buildenv_info.define_path("AR", os.path.join(ndk_bin, "llvm-ar"))
        self.buildenv_info.define_path("RANLIB", os.path.join(ndk_bin, "llvm-ranlib"))
        self.buildenv_info.define_path("STRIP", os.path.join(ndk_bin, "llvm-strip"))
        self.buildenv_info.define_path("NM", os.path.join(ndk_bin, "llvm-nm"))
        #self.buildenv_info.define_path("ADDR2LINE", os.path.join(ndk_bin, "llvm-addr2line"))
        self.buildenv_info.define_path("OBJCOPY", os.path.join(ndk_bin, "llvm-objcopy"))
        self.buildenv_info.define_path("OBJDUMP", os.path.join(ndk_bin, "llvm-objdump"))
        self.buildenv_info.define_path("READELF", os.path.join(ndk_bin, "llvm-readelf"))
        #self.buildenv_info.define_path("ELFEDIT", os.path.join(ndk_bin, "llvm-elfedit"))
        
        self.output.info('Creating self.cpp_info.builddirs: %s' % os.path.join(ndk_root, 'build'))
        self.cpp_info.includedirs = []
        self.cpp_info.libdirs = []
        self.cpp_info.bindirs = []
        self.cpp_info.builddirs = [os.path.join(ndk_root, 'build')]
