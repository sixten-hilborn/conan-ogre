from conans import ConanFile, CMake, tools
import os
import fnmatch
import glob


def apply_patches(source, dest):
    for root, _dirnames, filenames in os.walk(source):
        for filename in fnmatch.filter(filenames, '*.patch'):
            patch_file = os.path.join(root, filename)
            dest_path = os.path.join(dest, os.path.relpath(root, source))
            tools.patch(base_path=dest_path, patch_file=patch_file)


def rename(pattern, name):
    for extracted in glob.glob(pattern):
        os.rename(extracted, name)


class OgreConan(ConanFile):
    name = "ogre"
    version = "1.10.12"
    description = "Open Source 3D Graphics Engine"
    folder = 'ogre-v' + version
    install_path = os.path.join('_build', folder, 'sdk')
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "with_boost": [True, False],
        "with_cg": [True, False],
        "node_storage_legacy": [True, False],
    }
    default_options = (
        "shared=True",
        "with_boost=False",
        "with_cg=True",
        "freetype:shared=False",
        "node_storage_legacy=True",
    )
    exports_sources = ['patches*']
    requires = (
        "freeimage/3.18.0@sixten-hilborn/stable",
        "freetype/2.9.0@bincrafters/stable",
        "libpng/1.6.37",  # override freetype's libpng
        "zlib/1.2.11"
    )
    url = "http://github.com/sixten-hilborn/conan-ogre"
    license = "https://opensource.org/licenses/mit-license.php"

    short_paths = True

    def configure(self):
        if 'x86' not in str(self.settings.arch):
            self.options.with_cg = False

    def requirements(self):
        if self.options.with_boost:
            if self.settings.compiler != "Visual Studio":
                self.options["boost"].fPIC = True
            self.requires("boost/1.67.0@conan/stable")
        if self.options.with_cg:
            self.requires("Cg/3.1@sixten-hilborn/stable")

    def system_requirements(self):
        if self.settings.os == 'Linux':
            installer = tools.SystemPackageTool()
            if self.settings.arch == 'x86':
                installer.install("libxmu-dev:i386")
                installer.install("libxaw7-dev:i386")
                installer.install("libxt-dev:i386")
                installer.install("libxrandr-dev:i386")
            elif self.settings.arch == 'x86_64':
                installer.install("libxmu-dev:amd64")
                installer.install("libxaw7-dev:amd64")
                installer.install("libxt-dev:amd64")
                installer.install("libxrandr-dev:amd64")

    def source(self):
        tools.get("https://github.com/OGRECave/ogre/archive/v{0}.zip".format(self.version), sha256='43ddecf937191aae46acfb6bf73ef107b7366b0336bf0cfe49dea4b1bfc24ed9')
        rename('ogre-*', self.folder)

    def build(self):
        apply_patches('patches', self.folder)
        tools.replace_in_file(
            '{0}/OgreMain/CMakeLists.txt'.format(self.folder),
            'target_link_libraries(OgreMain ${LIBRARIES})',
            'target_link_libraries(OgreMain ${LIBRARIES} ${CONAN_LIBS_ZLIB})')
        tools.replace_in_file(
            '{0}/Components/Overlay/CMakeLists.txt'.format(self.folder),
            'target_link_libraries(OgreOverlay OgreMain ${FREETYPE_LIBRARIES})',
            'target_link_libraries(OgreOverlay OgreMain ${CONAN_LIBS_FREETYPE} ${CONAN_LIBS_BZIP2} ${CONAN_LIBS_LIBPNG} ${CONAN_LIBS_ZLIB})')

        cmake = CMake(self)
        cmake.definitions['CMAKE_INSTALL_PREFIX'] = os.path.join(os.getcwd(), self.install_path)
        cmake.definitions['CMAKE_POSITION_INDEPENDENT_CODE'] = True
        cmake.definitions['OGRE_STATIC'] = not self.options.shared
        cmake.definitions['OGRE_COPY_DEPENDENCIES'] = False
        # cmake.definitions['OGRE_UNITY_BUILD'] = True  # Speed up build
        cmake.definitions['OGRE_BUILD_DEPENDENCIES'] = False  # Dependencies should be handled via Conan instead :)
        cmake.definitions['OGRE_BUILD_SAMPLES'] = False
        cmake.definitions['OGRE_BUILD_TESTS'] = False
        cmake.definitions['OGRE_BUILD_TOOLS'] = False
        cmake.definitions['OGRE_INSTALL_PDB'] = False
        cmake.definitions['OGRE_USE_STD11'] = True
        cmake.definitions['OGRE_USE_BOOST'] = self.options.with_boost
        cmake.definitions['OGRE_NODE_STORAGE_LEGACY'] = self.options.node_storage_legacy
        if self.settings.compiler == 'Visual Studio':
            cmake.definitions['OGRE_CONFIG_STATIC_LINK_CRT'] = str(self.settings.compiler.runtime).startswith('MT')
        cmake.configure(build_folder='_build', source_folder=self.folder)
        cmake.build(target='install')

    def package(self):
        sdk_dir = self.install_path
        include_dir = os.path.join(sdk_dir, 'include', 'OGRE')
        lib_dir = os.path.join(sdk_dir, 'lib')
        bin_dir = os.path.join(sdk_dir, 'bin')
        self.copy(pattern="*.h", dst="include/OGRE", src=include_dir)
        self.copy("*.lib", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.a", dst="lib", src=lib_dir, keep_path=False)
        self.copy("*.so*", dst="lib", src=lib_dir, keep_path=False, links=True)
        self.copy("*.dylib", dst="lib", src=lib_dir, keep_path=False)
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
        if not self.options.shared and self.settings.os == 'Windows':
            self.cpp_info.libs = [lib+'Static' for lib in self.cpp_info.libs]
        #is_apple = (self.settings.os == 'Macos' or self.settings.os == 'iOS')
        if self.settings.build_type == "Debug" and self.settings.os == 'Windows': #not is_apple:
            self.cpp_info.libs = [lib+'_d' for lib in self.cpp_info.libs]

        if self.settings.os == 'Linux':
            self.cpp_info.libs.append('rt')
