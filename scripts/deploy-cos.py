#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""部署 Regists 出海指南 到腾讯云 COS 静态网站"""

import os, sys, hashlib, json, io
from itertools import islice
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

SECRET_ID  = "AKIDJjBDECyVotjXEi5KMBwZ6ZuCrYDl6E7f"
SECRET_KEY = "hKkvsc7OSWP3ScZGjxxiDUiiT0LSKOXe"
REGION     = "ap-guangzhou"   # 广州地域，国内访问最快
BUCKET     = "goglobal-guide-1319653034"  # 唯一bucket名

try:
    from qcloud_cos import CosConfig, CosS3Client
except ImportError:
    os.system(f'{sys.executable} -m pip install cos-python-sdk-v5 -q')
    from qcloud_cos import CosConfig, CosS3Client

config = CosConfig(SecretId=SECRET_ID, SecretKey=SECRET_KEY, Region=REGION)
client = CosS3Client(config)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def list_files():
    """收集需要上传的所有文件"""
    skip_dirs = {'.workbuddy', 'scripts', '__pycache__', '.git', 'node_modules'}
    skip_exts = {'.pyc', '.pyo'}
    files = []
    for root, dirs, fnames in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in fnames:
            ext = os.path.splitext(fname)[1].lower()
            if ext in skip_exts:
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, BASE_DIR).replace('\\', '/')
            files.append((full, rel))
    return sorted(files, key=lambda x: x[1])

def upload_files(files):
    """上传文件到COS"""
    total = len(files)
    print(f"共 {total} 个文件，开始上传...\n")

    for i, (full, rel) in enumerate(files, 1):
        # 设置 Content-Type
        ext = os.path.splitext(rel)[1].lower()
        content_type = {
            '.html': 'text/html; charset=utf-8',
            '.css':  'text/css; charset=utf-8',
            '.js':   'application/javascript; charset=utf-8',
            '.json': 'application/json; charset=utf-8',
            '.svg':  'image/svg+xml',
            '.png':  'image/png',
            '.jpg':  'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.ico':  'image/x-icon',
            '.txt':  'text/plain; charset=utf-8',
            '.xml':  'application/xml; charset=utf-8',
            '.md':   'text/markdown; charset=utf-8',
            '.py':   'text/plain; charset=utf-8',
        }.get(ext, 'application/octet-stream')

        # 设置 Cache-Control
        if ext in ('.html', '.json', '.xml', '.md'):
            cache = 'no-cache'  # HTML/JSON 不缓存
        else:
            cache = 'max-age=86400'  # 静态资源缓存1天

        with open(full, 'rb') as fh:
            resp = client.put_object(
                Bucket=BUCKET,
                Body=fh,
                Key=rel,
                ContentType=content_type,
                CacheControl=cache,
            )

        status = "OK" if resp['ETag'] else "FAIL"
        print(f"  [{i:3d}/{total}] {status}  {rel}")

def enable_static_website():
    """开启静态网站功能"""
    client.put_bucket_website(
        Bucket=BUCKET,
        IndexDocument='index.html',
        ErrorDocument='index.html',
    )
    print("\n静态网站已开启")

def set_public_read():
    """设置公共读权限"""
    # 设置存储桶公开读策略
    policy = {
        "Statement": [
            {
                "Principal": {"qcs": ["qcs::cam::anyone:anyone"]},
                "Effect": "Allow",
                "Action": ["name/cos:GetObject"],
                "Resource": [f"qcs::cos:{REGION}:uid/1319653034:{BUCKET}/*"]
            }
        ],
        "Version": "2.0"
    }
    client.put_bucket_policy(Bucket=BUCKET, Policy=json.dumps(policy))
    print("已设置为公开读")

def get_endpoint():
    """获取访问链接"""
    info = client.get_bucket(Bucket=BUCKET)
    # COS 静态网站默认域名
    url = f"https://{BUCKET}.cos-website.{REGION}.myqcloud.com"
    return url

def main():
    print("=" * 60)
    print("  Regists 出海指南 - 部署到腾讯云 COS")
    print("=" * 60)

    # Step 1: 确保 Bucket 存在
    try:
        client.head_bucket(Bucket=BUCKET)
        print(f"\nBucket {BUCKET} 已存在")
    except:
        client.create_bucket(Bucket=BUCKET)
        print(f"\nBucket {BUCKET} 创建成功")

    # Step 2: 设置公开读
    set_public_read()

    # Step 3: 上传文件
    files = list_files()
    upload_files(files)

    # Step 4: 开启静态网站
    enable_static_website()

    # Step 5: 获取访问链接
    url = get_endpoint()
    print(f"\n{'='*60}")
    print(f"  ✅ 部署完成!")
    print(f"  访问链接: {url}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
