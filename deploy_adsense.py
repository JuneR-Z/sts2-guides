#!/usr/bin/env python3
"""
AdSense Auto Ads 批量部署脚本
用法: python deploy_adsense.py <ca-pub-XXXXXX>

功能:
1. 扫描所有 HTML 文件
2. 智能处理三种情况:
   - 已有占位符 ca-pub-XXXXXXXXXXXXXXXX → 替换为真实 ID
   - 无 AdSense 代码 → 注入新代码
   - 已是目标 ID → 跳过
3. 自动生成 sitemap
"""
import sys
import os
import re
from datetime import datetime

# Fix Unicode output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ─── 配置 ──────────────────────────────────────────────
if len(sys.argv) < 2:
    print("用法: python deploy_adsense.py ca-pub-XXXXXXXXXXXXXXXX")
    print("示例: python deploy_adsense.py ca-pub-1234567890123456")
    sys.exit(1)

PUBLISHER_ID = sys.argv[1]
PLACEHOLDER = 'ca-pub-XXXXXXXXXXXXXXXX'

# AdSense Auto Ads 代码（放在 </head> 前）
ADSENSE_CODE = f'''<!-- Google AdSense Auto Ads -->
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={PUBLISHER_ID}" crossorigin="anonymous"></script>'''


def process_file(filepath: str) -> tuple[str, bool]:
    """
    处理单个文件，返回 (action, modified)。
    action: 'replace' | 'inject' | 'skip' | 'fail'
    """
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 1. 如果已有目标 publisher ID → 跳过
    if PUBLISHER_ID in content:
        return ('skip', False)

    # 2. 如果有 placeholder（且不是目标 ID 本身），替换为真实 ID
    if PLACEHOLDER in content and PUBLISHER_ID != PLACEHOLDER:
        new_content = content.replace(PLACEHOLDER, PUBLISHER_ID)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return ('replace', True)

    # 3. 如果没有 AdSense 代码 → 注入
    if 'pagead2.googlesyndication.com' not in content:
        new_content = re.sub(
            r'</head>',
            f'{ADSENSE_CODE}\n</head>',
            content,
            count=1,
            flags=re.IGNORECASE
        )
        if new_content == content:
            return ('fail', False)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return ('inject', True)

    # 4. 已有某版本 AdSense 但不匹配 placeholder → 跳过
    return ('skip', False)


def main():
    site_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(site_root)

    is_placeholder = (PUBLISHER_ID == PLACEHOLDER)
    print(f'🚀 AdSense 部署')
    print(f'   Publisher ID: {PUBLISHER_ID}')
    if is_placeholder:
        print(f'   ⚠ 占位符模式 — 获真实 ID 后重新运行本脚本即可替换')
    print(f'   时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    total = 0
    injected = 0
    replaced = 0
    skipped = 0
    failed = 0

    for root, dirs, files in os.walk('.'):
        # 跳过隐藏目录
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for f in files:
            if not f.endswith('.html'):
                continue
            path = os.path.join(root, f).replace('\\', '/')
            total += 1
            action, modified = process_file(path)
            if action == 'inject':
                injected += 1
                print(f'  {path}  ✅ 已注入')
            elif action == 'replace':
                replaced += 1
                print(f'  {path}  🔄 已替换')
            elif action == 'fail':
                failed += 1
                print(f'  {path}  ❌ 找不到 </head>')
            else:
                skipped += 1

    print()
    updated = injected + replaced
    print(f'📊 结果: {total} 个文件')
    print(f'   新注入: {injected}')
    print(f'   已替换: {replaced}')
    print(f'   已跳过: {skipped}')
    if failed:
        print(f'   失败: {failed}')
    print(f'   实际修改: {updated}')

    # 生成 sitemap
    if os.path.exists('generate_sitemap.py'):
        print('\n🔄 生成 sitemap...')
        os.system('python generate_sitemap.py')


if __name__ == '__main__':
    main()
