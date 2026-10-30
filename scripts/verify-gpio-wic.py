#!/usr/bin/env python3
"""Read-only WIC inspection; extract regular local files, never access block devices."""
import argparse
import bz2
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('image',type=Path)
p.add_argument('build_dir',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
image=a.image.resolve(); build=a.build_dir.resolve(); out=a.output.resolve()
assert image.is_file() and not image.is_block_device()
out.mkdir(parents=True,exist_ok=True); out.chmod(0o700)
work=build/'tmp/work/raspberrypi4_64-poky-linux'
native=work/'yocto-gpio-toggle-image/1.0/recipe-sysroot-native/usr/bin'
dtbin=work/'lab-gpio-overlay/1.0/recipe-sysroot-native/usr/bin'
deploy=build/'tmp/deploy/images/raspberrypi4-64'
def run(args):
    return subprocess.check_output([str(x) for x in args],stderr=subprocess.PIPE)
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
report={'image':str(image),'bytes':image.stat().st_size,'sha256':digest(image),'format':'bzip2' if image.suffix=='.bz2' else 'raw WIC','checks':[]}
def passed(s): report['checks'].append(s); print('PASS:',s,flush=True)
wic=out/'image.wic'
if image.suffix=='.bz2':
    with bz2.open(image,'rb') as src, wic.open('wb') as dst: shutil.copyfileobj(src,dst)
else: shutil.copyfile(image,wic)
report['uncompressed_bytes']=wic.stat().st_size; report['uncompressed_sha256']=digest(wic)
with wic.open('rb') as f:
    mbr=f.read(512); assert mbr[510:]==b'\x55\xaa'
    parts=[]
    for i in range(4):
        e=mbr[446+i*16:462+i*16]; start,size=struct.unpack_from('<II',e,8)
        if size: parts.append({'type':e[4],'start_sector':start,'sectors':size})
assert len(parts)==2 and parts[0]['type'] in (0xb,0xc,0xe) and parts[1]['type']==0x83
report['partitions']=parts
passed('MBR: FAT boot + Linux root partitions')
boot=out/'boot'; boot.mkdir(exist_ok=True)
for name in ['config.txt','cmdline.txt','overlays/lab-gpio-eight-overlay.dtbo','bcm2711-rpi-4-b.dtb','kernel8.img']:
    dest=boot/name; dest.parent.mkdir(exist_ok=True,parents=True)
    run([native/'mcopy','-o','-i',str(wic)+'@@'+str(parts[0]['start_sector']*512),'::/'+name,dest])
config=(boot/'config.txt').read_text(); cmdline=(boot/'cmdline.txt').read_text()
active=[x.strip() for x in config.splitlines() if x.strip() and not x.lstrip().startswith('#')]
assert active[-3:]==['[all]','enable_uart=1','dtoverlay=lab-gpio-eight-overlay']
assert [x for x in active if x.startswith('dtoverlay=lab-gpio')]==['dtoverlay=lab-gpio-eight-overlay']
assert cmdline.count('\n')==1 and cmdline.split().count('console=serial0,115200')==1
assert 'root=/dev/mmcblk0p2' in cmdline and 'rootwait' in cmdline
assert digest(boot/'kernel8.img')==digest(deploy/'Image')
passed('Actual FAT: private config + UART command line + overlay + deployed ARM64 kernel')
overlay=boot/'overlays/lab-gpio-eight-overlay.dtbo'
assert digest(overlay)==digest(deploy/'devicetree/lab-gpio-eight-overlay.dtbo')
merged=out/'merged-offline.dtb'
run([dtbin/'fdtoverlay','-i',boot/'bcm2711-rpi-4-b.dtb','-o',merged,overlay])
def prop(path,key,typ='s'):
    return run([dtbin/'fdtget','-t',typ,merged,path,key]).decode().strip()
leds=[5,6,12,13,19,16,26,20]; buttons=[4,17,18,27,22,23,24,25]
assert len(set(leds+buttons))==16 and not {14,15}.intersection(leds+buttons)
controller=prop('/soc/gpio@7e200000','phandle','u')
for n,(led,button) in enumerate(zip(leds,buttons)):
    node='/lab-gpio'+('-d'+str(n) if n else '')
    assert prop(node,'status')=='okay' and prop(node,'compatible')=='yocto-lab,gpio-demo'
    assert prop(node,'led-gpios','u')==f'{controller} {led} 0'
    assert prop(node,'button-gpios','u')==f'{controller} {button} 1'
assert prop('/aliases','serial0')=='/soc/serial@7e215040'
passed('Offline DT merge: 8 active nodes, BCM offsets/polarities, serial0 mini-UART; no GPIO14/15 overlap')
root=out/'root.ext4'
with wic.open('rb') as src, root.open('wb') as dst:
    src.seek(parts[1]['start_sector']*512); remaining=parts[1]['sectors']*512
    while remaining:
        b=src.read(min(1024*1024,remaining)); assert b; dst.write(b); remaining-=len(b)
def read(path): return run(['debugfs','-R','cat '+path,root])
def stat(path): return run(['debugfs','-R','stat '+path,root]).decode()
app=out/'lab_gpio_test'; app.write_bytes(read('/usr/bin/lab_gpio_test'))
appelf=run(['readelf','-h',app]).decode(); assert 'AArch64' in appelf
(out/'app-readelf.txt').write_text(appelf)
release=(build/'tmp/work-shared/raspberrypi4-64/kernel-build-artifacts/include/config/kernel.release').read_text().strip()
module=out/'lab_gpio.ko'; module.write_bytes(lzma.decompress(read('/lib/modules/'+release+'/updates/lab_gpio.ko.xz')))
modelf=run(['readelf','-h',module]).decode(); assert 'AArch64' in modelf
vermagic=run(['modinfo','-F','vermagic',module]).decode().strip(); assert vermagic.split()[0]==release
(out/'module-readelf.txt').write_text(modelf); (out/'module-vermagic.txt').write_text(vermagic+'\n')
report['kernel_release']=release; report['vermagic']=vermagic
manifest=deploy/image.name.replace('.wic.bz2','.manifest').replace('.wic','.manifest')
assert manifest.is_file(),manifest
text=manifest.read_text(); actual='kernel-module-lab-gpio-'+release
for pkg in [actual,'lab-gpio-test','lab-gpio-autostart','kmod','shadow','shadow-base']:
    assert re.search(r'^'+re.escape(pkg)+r'\s',text,re.M),pkg
assert not re.search(r'^(thermal|hello-drv|dropbear|openssh|nginx)',text,re.M)
shutil.copyfile(manifest,out/'package.manifest'); report['manifest']=str(manifest); report['module_package']=actual
passed('WIC rootfs: AArch64 app/module, kernel ABI matches, actual module package in manifest')
init=read('/etc/init.d/lab-gpio')
source=Path(__file__).resolve().parents[1]/'layers/meta-yocto-lab/recipes-core/lab-gpio-autostart/files/lab-gpio-init'
assert init==source.read_bytes()
for path in ['/etc/init.d/lab-gpio','/usr/bin/lab_gpio_test']:
    assert '0755' in stat(path)
for n in (2,3,4,5): assert '../init.d/lab-gpio' in stat(f'/etc/rc{n}.d/S99lab-gpio')
for n in (0,1,6): assert '../init.d/lab-gpio' in stat(f'/etc/rc{n}.d/K01lab-gpio')
inittab=read('/etc/inittab').decode(); assert '115200 ttyS0' in inittab
(out/'inittab.txt').write_text(inittab)
assert 'init.sysvinit' in stat('/sbin/init')
assert 'login.shadow' in stat('/bin/login')
# No secrets printed or saved in the report.
shadow=read('/etc/shadow').decode(); fields=next(x.split(':') for x in shadow.splitlines() if x.startswith('root:'))
assert fields[1]==(build/'conf/gpio-private/root-password.hash').read_text().strip()
assert fields[1].startswith('$6$') and any(mode in stat('/etc/shadow') for mode in ('0400', '0600'))
assert 'ttyS0' in read('/etc/securetty').decode().splitlines()
password = (build/'conf/gpio-private/root-password.txt').read_bytes()
check = subprocess.check_output(['openssl','passwd','-6','-salt',fields[1].split('$')[2],'-stdin'],input=password).decode().strip()
assert check == fields[1]
passwd=read('/etc/passwd').decode(); assert next(x.split(':')[1] for x in passwd.splitlines() if x.startswith('root:'))=='x'
fstab=read('/etc/fstab').decode(); mountscript=read('/etc/init.d/mountall.sh').decode()
assert re.search(r'^tmpfs\s+/run\s+tmpfs',fstab,re.M)
(out/'fstab.txt').write_text(fstab)
assert 'mount' in mountscript
modprobe=stat('/sbin/modprobe'); assert 'kmod' in modprobe or 'modprobe' in modprobe
passed('Rootfs: executable init/app, SysV runlevels, ttyS0 getty, shadow login/private hash, tmpfs /run, modprobe')
report['hardware']='NOT TESTED; offline merge does not prove firmware/live-DT or electrical behavior'
(out/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
