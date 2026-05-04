#!/usr/bin/env python3
"""FTP-upload every renamed-new-file and redirect-stub-old-file to BetLegendPicks live root."""
import os, json, ftplib, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
MAP_PATH = os.path.join(ROOT, 'scripts', 'date_strip_rename_map.json')

FTP_HOST = '208.109.70.186'
FTP_USER = 'master@bestmlbhandicapper.com'
FTP_PASS = 'Warriors2025!'

def main():
    with open(MAP_PATH, 'r', encoding='utf-8') as f:
        rename_map = json.load(f)

    print(f'  Rename map entries: {len(rename_map)}')
    upload_targets = []
    for old, new in rename_map.items():
        upload_targets.append(old)  # redirect stub at old name
        upload_targets.append(new)  # real renamed file at new name
    print(f'  Total file uploads queued: {len(upload_targets)}')

    print('  Connecting to FTP...')
    ftp = ftplib.FTP(FTP_HOST, timeout=60)
    ftp.login(FTP_USER, FTP_PASS)
    ftp.cwd('/')
    print('  Connected, cwd=/')

    uploaded = 0
    failed = []
    for fname in upload_targets:
        local = os.path.join(ROOT, fname)
        if not os.path.exists(local):
            failed.append((fname, 'local-missing'))
            continue
        try:
            with open(local, 'rb') as fh:
                ftp.storbinary(f'STOR {fname}', fh)
            uploaded += 1
            if uploaded % 50 == 0:
                print(f'    {uploaded}/{len(upload_targets)}')
        except Exception as e:
            failed.append((fname, str(e)))

    ftp.quit()
    print(f'\n  Uploaded: {uploaded}/{len(upload_targets)}')
    if failed:
        print(f'  FAILED: {len(failed)}')
        for f in failed[:10]:
            print(f'    {f}')

if __name__ == '__main__':
    main()
