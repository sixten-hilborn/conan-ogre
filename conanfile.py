from conans import ConanFile
import os
import glob
from conans.tools import get
from conans import CMake
from multiprocessing import cpu_count

def rename(pattern, name):
    for extracted in glob.glob(pattern):
        os.rename(extracted, name)


class OgreConan(ConanFile):
    name = "OGRE"
    version = "1.9.0"
    folder = 'ogre-v1.9'
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {"shared": [True, False]}
    default_options = "shared=False"
    exports = ["CMakeLists.txt"]
    requires = (
        #"freeimage/3.17.0@sixten-hilborn/testing",
        "freetype/2.6.3@sixten-hilborn/testing",
        "SDL2/2.0.5@lasote/stable",
        "OIS/1.3@sixten-hilborn/testing",
        "RapidJSON/1.0.2@SamuelMarks/stable",
        "zlib/1.2.8@lasote/stable"
    )
    url="http://github.com/sixten-hilborn/conan-ogre"
    license="https://opensource.org/licenses/mit-license.php"

    def source(self):
        get("https://bitbucket.org/sinbad/ogre/get/v1-9.zip")
        rename('sinbad-ogre*', self.folder)

    def build(self):
        self.makedir('_build')
        cmake = CMake(self.settings)
        cd_build = 'cd _build'
        options = '-DOGRE_BUILD_SAMPLES=0 -DOGRE_BUILD_TESTS=0 -DOGRE_BUILD_TOOLS=0'
        build_options = '-- -j{0}'.format(cpu_count()) if self.settings.compiler == 'gcc' else ''
        self.run_and_print('%s && cmake .. %s %s' % (cd_build, cmake.command_line, options))
        self.run_and_print("%s && cmake --build . %s %s" % (cd_build, cmake.build_config, build_options))

    def makedir(self, path):
        if self.settings.os == "Windows":
            self.run("IF not exist {0} mkdir {0}".format(path))
        else:
            self.run("mkdir {0}".format(path))

    def package(self):
        lib_dir = "_build/{0}/lib".format(self.folder)
        bin_dir = "_build/{0}/bin".format(self.folder)
        self.copy(pattern="*.h", dst="include/OGRE", src="_build/{0}//include".format(self.folder))
        self.copy(pattern="*.h", dst="include/OGRE", src="{0}/OgreMain/include".format(self.folder))
        #for subsystem in ['RenderSystems',
        #self.copy(pattern="*.h", dst="include/OGRE", src="{0}/OgreMain/include".format(self.folder), keep_path=False)
        self.copy("*.lib", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.a", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.so", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.dll", dst="bin", src=bin_dir, keep_path=False)

    def package_info(self):
        self.cpp_info.libs = [
            'OgreMain',
            #  'OgreOverlay',  -- Not used at the moment
            'OgrePaging',
            'OgreProperty',
            'OgreRTShaderSystem',
            'OgreTerrain'
        ]

        if self.settings.os == "Windows":
            if self.settings.build_type == "Debug" and self.settings.compiler == "Visual Studio":
                self.cpp_info.libs = [lib+'_d' for likb in self.cpp_info.libs]

    def run_and_print(self, command):
        self.output.warn(command)
        self.run(command)
