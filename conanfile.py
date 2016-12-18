from conans import ConanFile
import os
import fnmatch
import glob
from conans.tools import get, patch, replace_in_file
from conans import CMake
from multiprocessing import cpu_count


def apply_patches(source, dest):
    for root, dirnames, filenames in os.walk(source):
        for filename in fnmatch.filter(filenames, '*.patch'):
            patch_file = os.path.join(root, filename)
            dest_path = os.path.join(dest, os.path.relpath(root, source))
            patch(base_path=dest_path, patch_file=patch_file)


def rename(pattern, name):
    for extracted in glob.glob(pattern):
        os.rename(extracted, name)


class OgreConan(ConanFile):
    name = "OGRE"
    version = "1.9.0"
    description = "Open Source 3D Graphics Engine"
    folder = 'ogre-v1.9'
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "use_boost": [True, False],
    }
    default_options = "shared=True", "use_boost=True", "freetype:shared=False"
    exports = ["CMakeLists.txt", 'patches*']
    requires = (
        #"freeimage/3.17.0@sixten-hilborn/testing",
        "freetype/2.6.3@sixten-hilborn/testing",
        "SDL2/2.0.5@lasote/stable",
        "OIS/1.3@sixten-hilborn/testing",
        "RapidJSON/1.0.2@SamuelMarks/stable",
        "zlib/1.2.8@lasote/stable",
        "Cg/3.1@sixten-hilborn/testing",

        "libpng/1.6.23@lasote/stable", "bzip2/1.0.6@lasote/stable"  # From freetype
    )
    url = "http://github.com/sixten-hilborn/conan-ogre"
    license = "https://opensource.org/licenses/mit-license.php"

    def configure(self):
        if self.settings.compiler == "Visual Studio" and self.settings.build_type == "Debug":
            if not self.settings.compiler.runtime.value.endswith("d"):
                self.settings.compiler.runtime.value += "d"

    def requirements(self):
        if self.options.use_boost:
            self.requires("Boost/1.60.0@lasote/stable")

    def source(self):
        get("https://bitbucket.org/sinbad/ogre/get/v1-9.zip")
        rename('sinbad-ogre*', self.folder)
        apply_patches('patches', self.folder)
        replace_in_file(
            '{0}/Components/Overlay/CMakeLists.txt'.format(self.folder),
            'target_link_libraries(OgreOverlay OgreMain ${FREETYPE_LIBRARIES})',
            'target_link_libraries(OgreOverlay OgreMain ${FREETYPE_LIBRARIES} ${CONAN_LIBS_BZIP2} ${CONAN_LIBS_LIBPNG} ${CONAN_LIBS_ZLIB})')

    def build(self):
        self.makedir('_build')
        cmake = CMake(self.settings)
        cd_build = 'cd _build'
        options = '-DOGRE_BUILD_SAMPLES=0 -DOGRE_BUILD_TESTS=0 -DOGRE_BUILD_TOOLS=0 -DOGRE_INSTALL_PDB=0 -DOGRE_USE_BOOST={0}'.format(
            1 if self.options.use_boost else 0)
        build_options = '-- -j{0}'.format(cpu_count()) if self.settings.compiler == 'gcc' else ''
        self.run_and_print('%s && cmake .. %s %s' % (cd_build, cmake.command_line, options))
        self.run_and_print("%s && cmake --build . --target install %s %s" % (cd_build, cmake.build_config, build_options))

    def makedir(self, path):
        if self.settings.os == "Windows":
            self.run("IF not exist {0} mkdir {0}".format(path))
        else:
            self.run("mkdir {0}".format(path))

    def package(self):
        sdk_dir = os.path.join('_build', self.folder, 'sdk')
        include_dir = os.path.join(sdk_dir, 'include', 'OGRE')
        lib_dir = os.path.join(sdk_dir, 'lib')
        bin_dir = os.path.join(sdk_dir, 'bin')
        self.copy(pattern="*.h", dst="include/OGRE", src=include_dir)
        self.copy("*.lib", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.a", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.so", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.dll", dst="bin", src=bin_dir, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = [
            'OgreMain',
            'OgreOverlay',
            'OgrePaging',
            'OgreProperty',
            'OgreRTShaderSystem',
            'OgreTerrain'
        ]

        if self.settings.os == "Windows":
            if self.settings.build_type == "Debug" and self.settings.compiler == "Visual Studio":
                self.cpp_info.libs = [lib+'_d' for lib in self.cpp_info.libs]

    def run_and_print(self, command):
        self.output.warn(command)
        self.run(command)
