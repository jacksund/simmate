# Blender Setup

At present, the most direct method to utilize Blender with Simmate involves a manual installation of Blender, which Simmate can then access via the command line. This process may necessitate additional steps for users who only wish to visualize structures without directly using Blender. In the future, we may explore the possibility of employing a Blender developer to facilitate the use of Blender as a bpy module, even if it's a minimal build specifically for Simmate.

# Previous Notes on Building bpy from Source

## Building a Custom Blender bpy Module (on Ubuntu 18.04)
Follow the instructions from https://wiki.blender.org/wiki/Building_Blender
1. Install all necessary dependencies to build the final package:
```
sudo apt install git;
sudo apt install build-essential;
snap install cmake --classic;
mkdir ~/blender-git;
cd ~/blender-git;
git clone https://git.blender.org/blender.git;
cd blender;
git submodule update --init --recursive;
git submodule foreach git checkout master;
git submodule foreach git pull --rebase origin master;
cd ~/blender-git/blender/build_files/build_environment;
./install_deps.sh;
```
2. In the bpy_module.cmake file, set the portable setting to 'ON':
```
nano /home/jacksund/blender-git/blender/build_files/cmake/config/bpy_module.cmake;
```
Modify this line:
```
set(WITH_INSTALL_PORTABLE    ON CACHE BOOL "" FORCE)
```
3. With the settings and dependencies prepared, build Blender as a Python module. The result will be in /blender-git/build_linux_bpy/bin/
```
cd ~/blender-git/blender;
make bpy;
```
4. Transfer the created module into the Anaconda environment and delete all build files.
```
cp -r /home/jacksund/blender-git/build_linux_bpy/bin/* /home/jacksund/anaconda3/envs/jacks_env/lib/python3.7/site-packages/;
sudo rm -r /home/jacksund/blender-git;
```
5. You can now 'import bpy' in your Python environment! 

## Building a Custom Blender bpy Module (on Ubuntu 19.10)
Follow the instructions from https://wiki.blender.org/wiki/Building_Blender/Linux/Ubuntu and troubleshoot with https://devtalk.blender.org/t/problem-with-running-blender-as-a-python-module/7367
1. Install all necessary dependencies to build the final package:
```
sudo apt-get update;
sudo apt-get install build-essential git subversion cmake libx11-dev libxxf86vm-dev libxcursor-dev libxi-dev libxrandr-dev libxinerama-dev;
mkdir ~/blender-git;
cd ~/blender-git;
git clone http://git.blender.org/blender.git;
cd ~/blender-git/blender;
make update;
cd ~/blender-git
./blender/build_files/build_environment/install_deps.sh --with-all
```
2. In the bpy_module.cmake file, set the portable setting to 'ON':
```
nano /home/jacksund/blender-git/blender/build_files/cmake/config/bpy_module.cmake;
```
Modify this line:
```
set(WITH_INSTALL_PORTABLE    ON CACHE BOOL "" FORCE)
```
Add these lines: 
```
set(WITH_MEM_JEMALLOC OFF CACHE BOOL "" FORCE)
set(WITH_MOD_OCEANSIM        OFF CACHE BOOL "" FORCE)

set(FFMPEG_LIBRARIES avformat;avcodec;avutil;avdevice;swscale;swresample;lzma;rt;theora;theoradec;theoraenc;vorbis;vorbisenc;vorbisfile;ogg;xvidcore;vpx;opus;mp3lame;x264;openjp2 CACHE STRING "" FORCE)

set(PYTHON_VERSION 3.7 CACHE STRING "" FORCE)
set(LLVM_VERSION 6.0 CACHE STRING "" FORCE)

set(OPENCOLORIO_ROOT_DIR /opt/lib/ocio CACHE STRING "" FORCE)
set(OPENIMAGEIO_ROOT_DIR /opt/lib/oiio CACHE STRING "" FORCE)
set(OSL_ROOT_DIR /opt/lib/osl CACHE STRING "" FORCE)
set(OPENSUBDIV_ROOT_DIR /opt/lib/osd CACHE STRING "" FORCE)
set(OPENCOLLADA_ROOT_DIR /opt/lib/opencollada CACHE STRING "" FORCE)
set(EMBREE_ROOT_DIR /opt/lib/embree CACHE STRING "" FORCE)
set(OPENIMAGEDENOISE_ROOT_DIR /opt/lib/oidn CACHE STRING "" FORCE)
set(ALEMBIC_ROOT_DIR /opt/lib/alembic CACHE STRING "" FORCE)
```
3. With the settings and dependencies prepared, build Blender as a Python module. The result will be in /blender-git/build_linux_bpy/bin/
```
cd ~/blender-git/blender;
make bpy;
```
4. Transfer the created module into the Anaconda environment and delete all build files.
```
cp -r /home/jacksund/blender-git/build_linux_bpy/bin/* /home/jacksund/anaconda3/envs/jacks_env/lib/python3.7/site-packages/;
sudo rm -r /home/jacksund/blender-git;
```
5. You can now 'import bpy' in your Python environment!