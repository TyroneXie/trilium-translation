from settings import PATCH_FOLDER, LANG, TRANS_RELEASE_FOLDER, USE_PROXY, PROXIES
import os
import re
import shutil
import requests
from zipfile import ZipFile
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# disable warning if use proxy
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

COMPRESS_TOOL = '7z'

COMPRESS_LEVEL = 9

REPO_NAME = 'zadam/trilium'
# TRANS_RELEASE_FOLDER = TRANS_RELEASE_FOLDER
# PATCH_FOLDER = PATCH_FOLDER


# 是否从GitHub下载文件
# whethere download files from GitHub
DO_DOWNLOAD = True
# DO_DOWNLOAD = False

# 是否删除临时文件
# whethere delete template files
DO_DELETE = True
# DO_DELETE = False


def requests_get(url):
    ret = None
    try:
        ret = requests.get(url, proxies=PROXIES, verify=not USE_PROXY)
    except Exception as e:
        print('If github is not avaliable, you can set USE_PROXY to True and set PROXIES.')
        print('Exception', e)
    return ret


def get_latest_version():
    """get latest version info"""
    print('get latest version info')
    url = f'https://api.github.com/repos/{REPO_NAME}/releases/latest'
    print(url)
    res = requests_get(url)
    version_info = {}

    # zipball_url 就是源码
    # version_info['zipball_url'] = res.json()['zipball_url']
    version_info['name'] = res.json()['name']

    patterns = {
        'linux': r'trilium-linux-x64-[0-9\.]+.tar.xz',
        'linux-server': r'trilium-linux-x64-server-[0-9\.]+.tar.xz',
        'windows': r'trilium-windows-x64-[0-9\.]+.zip',
        'mac': r'trilium-mac-x64-[0-9\.]+.zip',
    }

    releases = {}

    for x in res.json()['assets']:
        for package_type in patterns:
            if re.match(patterns[package_type], x['name']):
                releases[package_type] = {
                    'name': x['name'],
                    'url': x['browser_download_url']
                }
    version_info['releases'] = releases
    return version_info


def download_latest(url, file_name=None):
    """download latest release"""
    print('download latest tarball')
    if not file_name:
        file_name = url.split('/')[-1]

    print('downloading ...')
    if DO_DOWNLOAD:
        with requests.get(url, proxies=PROXIES, verify=False, stream=True) as r:
            r.raise_for_status()
            with open(file_name, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
    print(f'download complete, file saved as {file_name}')
    return file_name


def download_releases(releases):
    for package_type in releases:
        release = releases[package_type]
        download_latest(release['url'], TRANS_RELEASE_FOLDER + release['name'])


def decompress_package(file_name):
    print(f'decompress {file_name}')
    if file_name.endswith('tar.xz'):
        try:
            os.system(f'xz -d {file_name}')
        except:
            pass
        try:
            os.system(f'tar -xf {file_name[:-3]}')
            if DO_DELETE:
                os.system(f'rm -f {file_name[:-3]}')
        except:
            pass
    elif file_name.endswith('.zip'):
        try:
            os.system(f'unzip -o {file_name}')

            if DO_DELETE:
                os.system(f'rm -f {file_name}')
        except:
            pass


def patch_linux(file_name):

    if not file_name.endswith('.tar.xz'):
        print('linux客户端文件名有问题')
        print('linux client wrong file name')
        exit()

    file_path = TRANS_RELEASE_FOLDER + file_name
    print('file_path', file_path)
    decompress_package(file_path)

    asar_folder = TRANS_RELEASE_FOLDER + 'trilium-linux-x64/resources'
    asar_path = asar_folder + '/app.asar'
    print(asar_path)

    # asar解包
    # asar unpack
    os.chdir(asar_folder)
    os.system('asar extract app.asar ./app/')

    # 打补丁
    # apply patch
    os.system(f'cp -rf {PATCH_FOLDER}* "{asar_folder}/app/"')

    # asar封包
    # asar pack
    os.system('asar pack app/ app.asar')

    # 删除解包文件
    # remove unpacked files
    os.system(f'rm -rf {asar_folder}/app/')

    # 打zip包
    # make zip
    new_name = f'trilium-{LANG}-linux-x64.zip'
    print('new_name', new_name)
    os.system(f'rm -f {new_name}')
    patched_root_folder = 'trilium-linux-x64'
    os.chdir(TRANS_RELEASE_FOLDER)

    if COMPRESS_TOOL == '7z':
        cmd = f'7z a {new_name} -r {patched_root_folder}'
    else:
        cmd = f'zip -{COMPRESS_LEVEL} -r {new_name} {patched_root_folder}'

    print(cmd)
    os.system(cmd)

    if DO_DELETE:
        os.system('rm -rf trilium-linux-x64')

    return new_name


def patch_linux_server(file_name):

    if not file_name.endswith('.tar.xz'):
        print('linux sever 文件名有问题')
        print('linux server wrong file name')
        exit()

    file_path = TRANS_RELEASE_FOLDER + file_name
    print('file_path', file_path)
    decompress_package(file_path)

    # 打补丁
    # apply patch
    cmd = f'cp -rf {PATCH_FOLDER}* {TRANS_RELEASE_FOLDER}/trilium-linux-x64-server/'
    print('cmd', cmd)
    os.system(cmd)

    # 打zip包
    # make zip package
    new_name = 'trilium-cn-linux-x64-sever.zip'
    print('new_name', new_name)
    os.system(f'rm -f {new_name}')
    patched_root_folder = 'trilium-linux-x64-server'
    os.chdir(TRANS_RELEASE_FOLDER)
    if COMPRESS_TOOL == '7z':
        cmd = f'7z a {new_name} -r {patched_root_folder}'
    else:
        cmd = f'zip -{COMPRESS_LEVEL} -r {new_name} {patched_root_folder}'
    print(cmd)
    os.system(cmd)

    if DO_DELETE:
        os.system('rm -rf trilium-linux-x64-server')

    return new_name


def patch_windows(file_name):

    if not file_name.endswith('.zip'):
        print('windows 文件名有问题')
        exit()

    file_path = TRANS_RELEASE_FOLDER + file_name
    print('file_path', file_path)
    decompress_package(file_path)

    asar_folder = TRANS_RELEASE_FOLDER + 'trilium-windows-x64/resources'
    asar_path = asar_folder + '/app.asar'
    print(asar_path)

    # asar解包
    os.chdir(asar_folder)
    os.system('asar extract app.asar ./app/')

    # 打补丁
    # apply patch
    os.system(f'cp -rf {PATCH_FOLDER}* {asar_folder}/app/')

    # asar封包
    # asar pack
    os.system('asar pack app/ app.asar')

    # 删除解包文件
    # remove unpacked files
    os.system(f'rm -rf {asar_folder}/app/')

    # 打zip包
    # make zip package
    new_name = f'trilium-{LANG}-windows-x64.zip'
    print('new_name', new_name)
    os.system(f'rm -f {new_name}')
    patched_root_folder = 'trilium-windows-x64'
    os.chdir(TRANS_RELEASE_FOLDER)
    if COMPRESS_TOOL == '7z':
        cmd = f'7z a {new_name} -r {patched_root_folder}'
    else:
        cmd = f'zip -{COMPRESS_LEVEL} -r {new_name} {patched_root_folder}'
    print(cmd)
    os.system(cmd)

    if DO_DELETE:
        os.system('rm -rf trilium-windows-x64')

    return new_name


def patch_mac(file_name):

    if not file_name.endswith('.zip'):
        print('windows 文件名有问题')
        exit()

    file_path = TRANS_RELEASE_FOLDER + file_name
    print('file_path', file_path)
    decompress_package(file_path)

    asar_folder = TRANS_RELEASE_FOLDER + 'trilium-mac-x64/Trilium Notes.app/Contents/Resources'
    asar_path = asar_folder + '/app.asar'
    print(asar_path)

    # asar解包
    # asar unpack
    os.chdir(asar_folder)
    os.system('asar extract app.asar ./app/')

    # 打补丁
    # apply patch
    os.system(f'cp -rf {PATCH_FOLDER}* "{asar_folder}/app/"')

    # asar封包
    # asar pack
    os.system('asar pack app/ app.asar')

    # 删除解包文件
    # remove unpacked files
    cmd = f'rm -rf "{asar_folder}/app/"'
    print('cmd', cmd)
    os.system(cmd)

    # 打zip包
    # make zip package
    new_name = f'trilium-{LANG}-mac-x64.zip'
    print('new_name', new_name)
    os.system(f'rm -f {new_name}')
    patched_root_folder = 'trilium-mac-x64'
    os.chdir(TRANS_RELEASE_FOLDER)
    if COMPRESS_TOOL == '7z':
        cmd = f'7z a {new_name} -r {patched_root_folder}'
    else:
        cmd = f'zip -{COMPRESS_LEVEL} -r {new_name} {patched_root_folder}'
    print('压缩命令', cmd)
    os.system(cmd)

    if DO_DELETE:
        os.system('rm -rf trilium-mac-x64')

    return new_name


if __name__ == '__main__':

    a = input(f'Delete folder {TRANS_RELEASE_FOLDER}, contunue?(y)')
    if a not in ['y', ]:
        exit()

    os.system(f'rm -rf {TRANS_RELEASE_FOLDER}')
    os.makedirs(f'{TRANS_RELEASE_FOLDER}')
    os.chdir(TRANS_RELEASE_FOLDER)

    # 获取更新
    # get update info
    version_info = get_latest_version()
    print('version_info', version_info)

    # 下载
    # download
    releases = version_info['releases']
    download_releases(releases)

    # 打补丁
    # patch

    # linux
    patch_linux(releases['linux']['name'])

    # linux-server
    patch_linux_server(releases['linux-server']['name'])

    # windows
    patch_windows(releases['windows']['name'])

    # mac
    patch_mac(releases['mac']['name'])
