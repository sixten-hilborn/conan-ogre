from conan.packager import ConanMultiPackager
import platform

if __name__ == "__main__":
    builder = ConanMultiPackager(args="--build missing")
    builder.add_common_builds(shared_option_name="OGRE:shared", pure_c=False)
    # Disable VS2010 because of missing DirectX stuff
    # Disable x86 Linux builds
    builder.builds = [
        [settings, options]
        for settings, options in builder.builds
        if not (settings["compiler"] == "Visual Studio" and settings["compiler.version"] == "10")
        and not (settings["os"] == "Linux" and settings["arch"] == "x86")
    ]
    builder.run()

