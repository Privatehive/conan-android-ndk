from conan.packager import ConanMultiPackager


if __name__ == "__main__":
    builder = ConanMultiPackager()
    builder.add(settings={"os": "Android", "os.api_level": 21, "arch": "armv7", "compiler": "gcc", "compiler.version": "4.9", "compiler.libcxx": "libstdc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 23, "arch": "armv7", "compiler": "gcc", "compiler.version": "4.9", "compiler.libcxx": "libstdc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 24, "arch": "armv7", "compiler": "gcc", "compiler.version": "4.9", "compiler.libcxx": "libstdc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 26, "arch": "armv7", "compiler": "gcc", "compiler.version": "4.9", "compiler.libcxx": "libstdc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 27, "arch": "armv7", "compiler": "gcc", "compiler.version": "4.9", "compiler.libcxx": "libstdc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 21, "arch": "armv7", "compiler": "clang", "compiler.version": "5.0", "compiler.libcxx": "libc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 23, "arch": "armv7", "compiler": "clang", "compiler.version": "5.0", "compiler.libcxx": "libc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 24, "arch": "armv7", "compiler": "clang", "compiler.version": "5.0", "compiler.libcxx": "libc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 26, "arch": "armv7", "compiler": "clang", "compiler.version": "5.0", "compiler.libcxx": "libc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.add(settings={"os": "Android", "os.api_level": 27, "arch": "armv7", "compiler": "clang", "compiler.version": "5.0", "compiler.libcxx": "libc++"}, options={"makeStandalone": "False"}, env_vars={}, build_requires={})
    builder.run()
