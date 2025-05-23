#!/usr/bin/env python3
#
# SPDX-FileCopyrightText: Adithya R
# SPDX-License-Identifier: MIT
#

import subprocess
import sys
import xml.etree.ElementTree as ET

import requests

if len(sys.argv) != 2:
    print('Usage:\n\t./merge-tag.py <tag>')
    sys.exit(1)

tag = sys.argv[1]

modules = {
    'nxp/opensource/driver': 'https://git.codelinaro.org/clo/la/platform/vendor/nxp/opensource/driver',
    'qcom/opensource/audio-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/audio-kernel-ar',
    'qcom/opensource/bt-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom-opensource/bt-kernel',
    'qcom/opensource/camera-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/camera-kernel',
    'qcom/opensource/dataipa': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/dataipa',
    'qcom/opensource/datarmnet': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/datarmnet',
    'qcom/opensource/datarmnet-ext': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/datarmnet-ext',
    'qcom/opensource/display-drivers': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/display-drivers',
    'qcom/opensource/dsp-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/dsp-kernel',
    'qcom/opensource/eva-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/eva-kernel',
    'qcom/opensource/graphics-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/graphics-kernel',
    'qcom/opensource/mm-drivers': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/mm-drivers',
    'qcom/opensource/mm-sys-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/mm-sys-kernel',
    'qcom/opensource/mmrm-driver': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/mmrm-driver',
    'qcom/opensource/securemsm-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/securemsm-kernel',
    'qcom/opensource/spu-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom/opensource/spu-kernel',
    'qcom/opensource/synx-kernel': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/synx-kernel',
    'qcom/opensource/video-driver': 'https://git.codelinaro.org/clo/la/platform/vendor/opensource/video-driver',
    'qcom/opensource/wlan/fw-api': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom-opensource/wlan/fw-api',
    'qcom/opensource/wlan/platform': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom-opensource/wlan/platform',
    'qcom/opensource/wlan/qca-wifi-host-cmn': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom-opensource/wlan/qca-wifi-host-cmn',
    'qcom/opensource/wlan/qcacld-3.0': 'https://git.codelinaro.org/clo/la/platform/vendor/qcom-opensource/wlan/qcacld-3.0',
}

# These are in a separate manifest
separated_techpacks = {
    'qcom/opensource/audio-kernel': 'audio',
    'qcom/opensource/camera-kernel': 'camera',
    'qcom/opensource/display-drivers': 'display',
    'qcom/opensource/eva-kernel': 'cv',
    'qcom/opensource/graphics-kernel': 'graphics',
    'qcom/opensource/mm-drivers': 'display',
    'qcom/opensource/mmrm-driver': 'video',
    'qcom/opensource/video-driver': 'video',
}


# Input revision from user - fallback
# for that facepalm moment when they forget to release a manifest xml
def get_revision_from_user():
    i = input('Enter custom tag or revision to proceed, or s to skip: ')
    return None if i.casefold() == 's' else i


# Parses the module revision from a vendor manifest
def get_revision_from_manifest(tag, path, techpack=None):
    if techpack is None:
        root = manifest_root
    else:
        response = requests.get(
            f'https://git.codelinaro.org/clo/la/techpack/{techpack}/manifest/-/raw/release/{tag}.xml'
        )
        if response.status_code != 200:
            print('Failed to load', techpack, 'manifest!')
            return get_revision_from_user()
        root = ET.fromstring(response.content)

    for project in root.findall('project'):
        repo_path = project.get('path')
        if repo_path is not None and repo_path.endswith(path):
            return project.get('revision')

    if techpack is None:
        print('Failed to obtain revision from vendor manifest!')
    else:
        print('Failed to obtain revision from', techpack, 'techpack manifest!')

    return get_revision_from_user()


# Obtains the tag for the given techpack manifest from vendor manifest
def get_techpack_tag(techpack):
    refs = manifest_root.find('refs')
    if refs is not None:
        for image in refs:
            project = image.get('project')
            if project == 'techpack/' + techpack + '/manifest':
                return image.get('tag')

    print('Failed to obtain', techpack, 'techpack tag from manifest!')


# Returns (actual_revision, display_revision)
def get_revision(path):
    if path in separated_techpacks.keys():
        techpack = separated_techpacks.get(path)
        tp_tag = get_techpack_tag(techpack)
        if tp_tag is not None:
            print('Techpack tag:', tp_tag)
            return (get_revision_from_manifest(tp_tag, path, techpack), tp_tag)
    else:
        return (get_revision_from_manifest(tag, path), tag)


# HERE IT BEGINS
response = requests.get(
    f'https://git.codelinaro.org/clo/la/la/vendor/manifest/-/raw/release/{tag}.xml'
)
if response.status_code != 200:
    print('Tag does not exist!')
    sys.exit(1)

# print(response.content)
manifest_root = ET.fromstring(response.content)

for path, url in modules.items():
    print('\nMerging', path)

    revs = get_revision(path)
    if revs is None:
        print('Failed to obtain revision, bailing!')
        continue

    rev, display_rev = revs
    if rev is None:
        print('No revision obtained, skipping!')
        continue

    print('URL:', url)
    print('Revision:', rev)

    commit_msg = f"{path.replace('/', ': ')}: Merge tag '{display_rev}'"
    if display_rev != tag:
        commit_msg += f"\n\nFrom vendor tag: '{tag}'"

    try:
        subprocess.run(['git', 'fetch', url, rev], check=True)
        subprocess.run(
            [
                'git',
                'merge',
                'FETCH_HEAD',
                '-Xsubtree=' + path,
                '-m',
                commit_msg,
                '--log=100',
            ],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print('Failed to merge!')
        break

    print('Succesfully merged!')
