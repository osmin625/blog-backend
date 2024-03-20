import os
import sys
from os import path
from pathlib import Path
from filecmp import cmp
import zipfile
import shutil
import fileinput
import re
import logging

logging.basicConfig(filename="post_upload.log", encoding='utf-8', level=logging.INFO)
userName = os.getenv('username')
downloadPath = path.join('\\Users',userName,'Downloads')
contentPath = '..\\..\\frontend\\content\\posts'
imgPath = '..\\..\\frontend\\static\\imgs'
currentPath = path.curdir
sourcePath = path.join(currentPath, 'sources')


def getZipList(downloadPath):
    dwPathFiles = os.listdir(downloadPath)
    zips_ = []

    for f in dwPathFiles:
        filePath = path.join(downloadPath,f)
        fname, ext = path.splitext(f)
        if ext == '.zip' and 'Export' in fname:
            zips_.append(filePath)
    return zips_


def extractZip(path_ = downloadPath):
    if not path.isdir(sourcePath): 
        os.makedirs(sourcePath)
    for zf in getZipList(path_):
        with zipfile.ZipFile(zf, 'r') as zipRef:
            zipRef.extractall(sourcePath)


def move_md_(fname, path_, src_path = sourcePath):
    src = path.join(src_path, fname)
    dest = path.join(path_, fname)
    os.rename(src, dest)


def fileDistribute(path_):
    fname_md, fname_dir = set(), set()
    def _fileDistribute(path_):
        for file in os.listdir(path_):
            fname, ext = path.splitext(file)
            if ext == '.md':
                fname_md.add(fname)
                move_md_(file, contentPath)
            elif ext == '.png':
                move_md_(file, imgPath, path_)
            elif ext == '':
                fname_dir.add(fname)
            else:
                os.remove(path.join(path_, file))
    _fileDistribute(path_)
    

    mdImgDir = fname_dir & fname_md

    for fname_md in mdImgDir:
        _fileDistribute(path.join(path_, fname_md))

    shutil.rmtree(sourcePath)


def organizeNotionExportFileName(path_):
    for file in os.listdir(path_):
        fname, ext = path.splitext(file)
        fname = ' '.join(fname.split()[:-1])
        new_file = fname + ext
        os.rename(path.join(path_,file), path.join(path_, new_file))
    return os.listdir(path_)


def updateImageFileName(path_):
    def _updateImageFileName(path_, folder_name):
        path_ = path.join(path_, folder_name)
        for i, img in enumerate(os.listdir(path_)):
            os.rename(path.join(path_, img), path.join(path_, folder_name + str(i) + '.png'))
    
    for file in os.listdir(path_):
        if path.isdir(path.join(path_, file)):
            _updateImageFileName(path_, file)


def cleanFileNames(path_):
    pattern = re.compile(r'[^\w\d_]+')
    for file in os.listdir(path_):
        fname, ext = path.splitext(file)
        fname = re.sub(pattern, '_', fname)
        if fname.endswith('_'):
            fname = fname.rstrip('_')
        os.rename(os.path.join(path_, file), os.path.join(path_, fname + ext))


def addPostFrontMatter(path_):
    mdList = [mdFile for mdFile in os.listdir(path_) if mdFile.endswith('.md')]
    for fname in mdList:
        FrontMatterClosed = False
        with fileinput.FileInput(path.join(path_,fname),inplace=True, encoding='utf-8') as f:
            for line in f:
                if f.isfirstline():
                    title = line.lstrip('#')
                    titleParam = 'title:' + title
                    print('---')
                    line = titleParam
                if not FrontMatterClosed:
                    if line == '\n':
                        continue
                    elif f.lineno() > 2 and ':' not in line:
                        logging.info(f'{f.lineno()}th line')
                        FrontMatterClosed = True
                        print('type: post')
                        print('---')
                    elif line.startswith(('마지막 학습일:', 'summary:', '생성일:', '생성일0:', 'status:', '갱신:', '하위 항목:', '상위 항목:', '이웃 항목:')):
                        continue
                if '⁍' in line:
                    logging.warning(f'[{fname}] {f.lineno()}th line latex syntax error occured.')
                print(line, end='')


extractZip(downloadPath)
organizeNotionExportFileName(sourcePath)
cleanFileNames(sourcePath)
updateImageFileName(sourcePath)
addPostFrontMatter(sourcePath)

# fileDistribute(sourcePath)
