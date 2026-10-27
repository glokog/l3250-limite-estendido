#!/usr/bin/env python3
"""Build the L3250 Windows 7/PowerShell 2 experimental 4624 mm + borderless bundle."""
import hashlib
import json
import re
import shutil
import struct
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / 'analysis' / 'l3250'
SOURCE = ROOT / 'L3250_L3251_X64_38005_LA.exe'
SOURCE_SHA256 = '8cdb2c34bebc163578c0fcdaaf9c77e50b08184ef6c3d7b2038aab940df9c145'
OUT = ROOT / 'dist' / 'L3250_4624mm_SEM_MARGEM_WIN7_V7'
NS = {'e': 'http://schema.epson.net/fusion/business/v150'}
FILES = [
    ('E_JC1YVA.CFX', 'E_TCXYWA.CFX', '0094b9fc1051353271780568e3670fb39e5997419e4bc107514b1512793e061a', 'a2d5f02911050354a46f71235c90feede09e7cfa4ff3bc2c085960c456a26017'),
    ('E_JC1YVE.CFX', 'E_TCXYWE.CFX', '45df278d23297369466053b81b74b527f2520c92f6b7955beb2896ac970f3a3e', '66628920f655ca4caba03fc496199294e7b5aa23ccd7e43b19b9c75cd58baf61'),
]
BINARIES = [
    (['ConfigFile'], 'E_WU1YA0.DLL', 'E_YUICYWE.DLL', '6335cd6ab5ea8e826b57e333764d0f24a19e972a4b119dc90e27eace333ec8b8'),
    (['DriverPath'], 'E_WMAI51.DLL', 'E_YMAIYWE.DLL', '194dba4e6b707007fe86e825a79ec24db4882439ad9ac6dc79571d437d7493d1'),
    (['DataFile'], 'E_WM1YWE.VIF', 'E_YVIFYWE.VIF', '1179402f182daa5c5e309014aef51bb0f693aaafcafcb138428f61c78a9a292e'),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patch_config(data, include_inches=True):
    """Set 4624 mm limits and L4260 borderless rules."""
    tree = ET.fromstring(data)
    extent = tree.findall("e:f/e:F[@f='7']/e:E[@e='261']", NS)
    metric = tree.findall("e:f/e:F[@f='11']/e:E[@e='0']/e:V", NS)
    imperial = tree.findall("e:f/e:F[@f='13']/e:E[@e='0']/e:V", NS)
    assert len(extent) == len(metric) == len(imperial) == 1
    assert (extent[0].get('J'), extent[0].get('K')) == ('2159', '12000')
    assert (metric[0].get('n'), metric[0].get('x'), metric[0].text) == ('860', '12000', '2970')
    assert (imperial[0].get('n'), imperial[0].get('x'), imperial[0].text) == ('339', '4724', '1169')
    assert tree.find("e:f/e:F[@f='230']", NS) is None
    assert tree.find("e:y/e:F[@f='230']", NS) is None
    replacements = [(b'K="12000"', b'K="46240"'), (b'x="12000"', b'x="46240"')]
    extent[0].set('K', '46240')
    metric[0].set('x', '46240')
    if include_inches:
        # 182.05 in = 4624.07 mm, matching the 4624 mm metric limit.
        replacements.append((b'x="4724"', b'x="18205"'))
        imperial[0].set('x', '18205')
    result = data
    for before, after in replacements:
        assert data.count(before) == 1
        result = result.replace(before, after)
    assert ET.tostring(tree) == ET.tostring(ET.fromstring(result))
    # Field 230 (label 20145) is "Check Paper Width Before Printing", not a
    # borderless control; V7 no longer adds it.
    result = enable_l4260_borderless(result)
    assert ET.fromstring(result).find("e:f/e:F[@f='230']", NS) is None
    return result


# The L3250 and L4260 config DLLs share identical code sections; borderless
# availability differs only in these CFX entries, copied from the L4260 CFX.
BORDERLESS_SIZES = [
    b'<E e="9" r="9" F="0x000000" w="2100" l="2970"',
    b'<E e="284" r="284" F="0x010000" w="1270" l="1780"',
    b'<E e="268" r="268" F="0x010000" w="2032" l="2540"',
    b'<E e="1" r="1" F="0x000000" w="2159" l="2794"',
]
BORDERLESS_BLOCKS = [
    b'<P><E f="9" e="%s"/><E f="34" e="0"/><E f="213" e="1"/></P>' % size for size in (b'9', b'268', b'284', b'1')
] + [
    b'<P><E f="35" e="%s"/><E f="213" e="1"/></P>' % size for size in (b'9', b'268', b'284', b'1')
]
USER_BORDERLESS = (b'J="2159" K="46240" pp1=', b'J="2159" K="46240" Dw="1820" Dh="2570" DW="2159" DH="46240" pp1=')


def enable_l4260_borderless(data):
    """Allow borderless on A4/Letter/5x7/8x10 and on user sizes 182-215.9 mm wide."""
    for size in BORDERLESS_SIZES:
        assert data.count(size) == 2 and data.count(size + b' p="2"') == 0, size
        data = data.replace(size, size + b' p="2" P="2"')
    for block in BORDERLESS_BLOCKS:
        assert data.count(block) == 1, block
        data = data.replace(block, b'')
    assert data.count(USER_BORDERLESS[0]) == 1
    data = data.replace(*USER_BORDERLESS)
    tree = ET.fromstring(data)
    user = tree.findall("e:f/e:F[@f='7']/e:E[@e='261']", NS)
    assert len(user) == 1 and (user[0].get('Dw'), user[0].get('DH')) == ('1820', '46240')
    for field in ('9', '35'):
        for size in ('9', '284', '268', '1'):
            entry = tree.find(f"e:f/e:F[@f='{field}']/e:E[@e='{size}']", NS)
            assert (entry.get('p'), entry.get('P')) == ('2', '2'), (field, size)
    return data


def text_file(path, text):
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8-sig'))


def make_test_pdf(path, length_mm, model='L3250'):
    scale = 72 / 25.4
    width, height = 210 * scale, length_mm * scale
    commands = ['0 G', '0.6 w']

    def line(x, y, x2, y2):
        commands.append(f'{x * scale:.3f} {height - y * scale:.3f} m {x2 * scale:.3f} {height - y2 * scale:.3f} l S')

    def label(x, y, message, size=11):
        message = message.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
        commands.append(f'BT /F1 {size} Tf {x * scale:.3f} {height - y * scale:.3f} Td ({message}) Tj ET')

    label(15, 18, f'EPSON {model} - TESTE {length_mm} mm', 14)
    label(15, 27, f'Uma pagina de 210 x {length_mm} mm. Escala 100%. Papel com margens.', 10)
    label(15, 35, 'Nao usar Poster, Mosaico, Ajustar pagina ou varias paginas por folha.', 10)
    line(15, 50, 15, length_mm - 15)
    for mm in range(100, length_mm, 100):
        line(15, mm, 40 if mm != 1200 else 180, mm)
        label(45, mm + 4, f'{mm} mm' + (' - antigo limite' if mm == 1200 else ''))
        if mm in (1300, 1500, 2000, 2500, 3000, 3500, 4000, 4500):
            label(90, mm + 4, f'MARCA ALEM DE 1,20 m: {mm / 1000:.1f} m', 10)
    label(40, length_mm - 18, f'FIM - {length_mm} mm; medir a folha, sem reducao de escala.', 11)
    stream = ('\n'.join(commands) + '\n').encode('ascii')
    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {width:.5f} {height:.5f}] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>'.encode(),
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
        f'<< /Length {len(stream)} >>\nstream\n'.encode() + stream + b'endstream',
    ]
    output = bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n')
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output += f'{index} 0 obj\n'.encode() + obj + b'\nendobj\n'
    start = len(output)
    output += b'xref\n0 6\n0000000000 65535 f \n'
    output += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    output += f'trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode()
    path.write_bytes(output)


def main():
    assert digest(SOURCE.read_bytes()) == SOURCE_SHA256, 'Unexpected L3250 installer'
    inf = (ANALYSIS / 'E2WF1YWE.inf.txt').read_text()
    legacy_models = inf.split('[EPSON.NTamd64.5.2]', 1)[1].split('[EPSON.NTamd64.10.0]', 1)[0]
    assert '"EPSON L3250 Series"' in legacy_models
    assert 'DriverVer=06/18/2026,3.80.05.00' in inf
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'patch').mkdir(exist_ok=True)
    (OUT / 'originais').mkdir(exist_ok=True)
    entries = []
    for source_name, installed_name, expected, previous in FILES:
        assert installed_name + ',' + source_name in inf
        original = (ANALYSIS / 'expanded' / source_name).read_bytes()
        assert digest(original) == expected, source_name
        patched = patch_config(original)
        (OUT / 'patch' / installed_name).write_bytes(patched)
        (OUT / 'originais' / installed_name).write_bytes(original)
        entries.append({
            'source_name': source_name, 'installed_name': installed_name,
            'original_sha256': expected, 'patched_sha256': digest(patched),
            'previous_sha256': previous,
            'changed_attributes': ['F[f=7]/E[e=261]@K', 'F[f=11]/E[e=0]/V@x', 'F[f=13]/E[e=0]/V@x', 'F[f=7]/E[e=261]@Dw,Dh,DW,DH', 'F[f=9,35]/E[e=9,284,268,1]@p,P', 'P[213=1 com tamanhos 9,284,268,1] removidas'],
        })
    binaries = []
    for properties, source_name, installed_name, expected in BINARIES:
        assert installed_name + ',' + source_name in inf
        location = 'data-expanded' if source_name.endswith('.VIF') else 'expanded'
        data = (ANALYSIS / location / source_name).read_bytes()
        assert digest(data) == expected, source_name
        if source_name.endswith('.DLL'):
            pe_offset = struct.unpack_from('<I', data, 0x3c)[0]
            assert data[pe_offset:pe_offset + 4] == b'PE\0\0'
            assert struct.unpack_from('<H', data, pe_offset + 4)[0] == 0x8664, 'Non-AMD64 DLL'
        binaries.append({'properties': properties, 'source_name': source_name, 'installed_name': installed_name, 'sha256': expected})
    manifest = {
        'format': 1, 'release': 7, 'status': 'experimental-not-tested-on-windows-or-printer',
        'driver': 'EPSON L3250 Series', 'driver_version': '3.80.05.00',
        'architecture': 'amd64', 'minimum_powershell': '2.0',
        'target_os': 'Windows 7 x64', 'legacy_inf': 'E2WF1YWE.INF',
        'original_installer_sha256': SOURCE_SHA256,
        'original_max_length_tenths_mm': 12000, 'patched_max_length_tenths_mm': 46240,
        'patched_max_length_hundredths_inch': 18205,
        'borderless_source': 'L4260 CFX (identical config DLL code)',
        'binaries': binaries, 'files': entries,
    }
    text_file(OUT / 'manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    document = ET.Element('l3250', {'format': '1', 'driver': manifest['driver'], 'original_installer_sha256': SOURCE_SHA256})
    files_xml = ET.SubElement(document, 'files')
    for entry in entries:
        ET.SubElement(files_xml, 'file', {key: entry[key] for key in ['installed_name', 'original_sha256', 'previous_sha256', 'patched_sha256']})
    binaries_xml = ET.SubElement(document, 'binaries')
    for binary in binaries:
        ET.SubElement(binaries_xml, 'binary', {
            'properties': ','.join(binary['properties']), 'source_name': binary['source_name'], 'sha256': binary['sha256'],
        })
    (OUT / 'manifest.xml').write_bytes(ET.tostring(document, encoding='utf-8', xml_declaration=True))
    shutil.copyfile(SOURCE, OUT / 'DriverOriginal.exe')
    script = (ROOT / 'tools' / 'Install-L3250-Win7-V7.ps1').read_text()
    assert not re.search(r'(?i)-(shr|shl|in|notin)\b', script), 'PS3+ operator in PS2 installer'
    for incompatible in ['Get-Printer', 'Get-PrintJob', 'Get-FileHash', 'ConvertFrom-Json', 'ConvertTo-Json', '-Raw', '[pscustomobject]', '$PSScriptRoot', '$PSCommandPath', 'IsNullOrWhiteSpace', 'Is64BitProcess', 'Is64BitOperatingSystem']:
        assert incompatible not in script, 'Unexpected installer dependency: ' + incompatible
    text_file(OUT / 'Install-L3250.ps1', script)
    text_file(OUT / 'L3250-Process.cs', (ROOT / 'tools' / 'L3250-Process.cs').read_text())
    text_file(OUT / 'L3250-Spooler.cs', (ROOT / 'tools' / 'L3250-Spooler.cs').read_text())
    for name, action in [('instalar', 'Install'), ('restaurar', 'Restore'), ('verificar', 'Verify'), ('abrir-preferencias', 'Preferences')]:
        cmd = rf'''@echo off
setlocal
cd /d "%~dp0"
set "L3250_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "L3250_POWERSHELL=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%L3250_POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-L3250.ps1" -Action {action}
set "L3250_RESULT=0"
if errorlevel 1 set "L3250_RESULT=1"
if errorlevel 2 set "L3250_RESULT=2"
if errorlevel 3 set "L3250_RESULT=1"
if not errorlevel 0 set "L3250_RESULT=1"
echo.
echo Codigo %L3250_RESULT%: 0 = concluido; 1 = erro; 2 = verificacao pendente ou limite nao confirmado.
pause
exit /b %L3250_RESULT%
'''
        (OUT / (name + '.cmd')).write_bytes(cmd.replace('\n', '\r\n').encode('ascii'))
    for length in (1500, 3000, 4600):
        make_test_pdf(OUT / f'teste-{length}mm.pdf', length, model='L3250')
    text_file(OUT / 'LEIA-ME.txt', r"""EPSON L3250 V7 - SEM MARGEM COMO NA L4260 E PAPEL ATE 4624 mm
Windows 7 x64 Intel/AMD, PowerShell 2.0 ou superior

1. Extraia TODO o ZIP em uma pasta nova.
2. Feche as preferencias Epson e os aplicativos que usam a impressora.
   Aguarde as filas de impressao terminarem.
3. Clique com o botao direito em instalar.cmd > Executar como administrador.
4. Ao terminar, confira "comprimento maximo informado": 4624 mm.
5. Execute abrir-preferencias.cmd. Em Definido pelo usuario deve aparecer a
   opcao de papel sem margem para larguras de 182 a 215,9 mm e comprimento
   de 257 a 4624 mm. "Sem margens" tambem fica liberado em A4, Carta,
   13 x 18 cm e 20 x 25 cm, como no driver da L4260.
6. Teste de impressao, um de cada vez: primeiro teste-3000mm.pdf, depois
   teste-4600mm.pdf; escala 100%, sem Ajustar pagina. Diga a ultima marca
   que saiu no papel.
7. Se der erro, envie o log install-*.log indicado na janela.

O que muda em relacao a V6:
A DLL de configuracao da L3250 e a da L4260 tem o mesmo codigo (secoes
identicas byte a byte); o que muda e o CFX. A V7 copia da L4260:
  - marcacao p="2" P="2" (sem margem) em A4, Carta, 13x18 e 20x25;
  - retirada das 8 regras que proibiam sem margem nesses tamanhos;
  - faixa de sem margem do papel definido pelo usuario (Dw/Dh/DW/DH),
    com comprimento maximo estendido para 4624 mm.
Os valores de expansao da margem continuam os da L3250.

O instalador reconhece o CFX original de 1200 mm e o da V6. Quando nao
existem perfis em %ProgramData%\EPSON\EPSON L3250 Series, ajusta os CFX
do driver no spooler; o driver regenera o cache CFB a partir deles.
Nao modifica DLLs, registro, permissoes, assinaturas ou DriverStore.

restaurar.cmd devolve os CFX originais de 1200 mm (exige backup da V7).
verificar.cmd consulta arquivos e o limite sem aplicar nada.
Logs/backups: C:\ProgramData\L3250-Comprimento-Experimental-Win7

Atencao: no driver original a Epson so libera sem margem na L3250 ate
10,16 cm de largura. Sem margem em papel mais largo joga tinta alem da
borda do papel; observe se aparecem manchas no verso ou na bandeja.
Pacote experimental; sem margem e 4624 mm ainda nao foram testados aqui.
""")
    sums = ''.join(f'{digest(path.read_bytes())}  {path.relative_to(OUT).as_posix()}\n' for path in sorted(OUT.rglob('*')) if path.is_file() and path.name != 'SHA256SUMS.txt')
    (OUT / 'SHA256SUMS.txt').write_text(sums)
    archive = OUT.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(OUT.rglob('*')):
            if path.is_file():
                z.write(path, Path(OUT.name) / path.relative_to(OUT))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert digest(z.read(OUT.name + '/DriverOriginal.exe')) == SOURCE_SHA256
        for entry in entries:
            assert digest(z.read(OUT.name + '/patch/' + entry['installed_name'])) == entry['patched_sha256']
    result = {'archive': str(archive), 'bytes': archive.stat().st_size, 'sha256': digest(archive.read_bytes()), 'manifest': manifest}
    repair = ROOT / 'dist' / 'L3250_CORRECAO_PREFERENCIAS_V7.zip'
    repair_files = [path for path in sorted(OUT.rglob('*')) if path.is_file() and path.name not in ['DriverOriginal.exe', 'SHA256SUMS.txt']]
    repair_sums = ''.join(f'{digest(path.read_bytes())}  {path.relative_to(OUT).as_posix()}\n' for path in repair_files)
    with zipfile.ZipFile(repair, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in repair_files:
            z.write(path, Path('L3250_CORRECAO_PREFERENCIAS_V7') / path.relative_to(OUT))
        z.writestr('L3250_CORRECAO_PREFERENCIAS_V7/SHA256SUMS.txt', repair_sums)
    with zipfile.ZipFile(repair) as z:
        assert z.testzip() is None
    result['repair'] = {'archive': str(repair), 'bytes': repair.stat().st_size, 'sha256': digest(repair.read_bytes())}
    (ANALYSIS / 'package-build-win7-v7.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['archive', 'bytes', 'sha256']}, indent=2))
    print(json.dumps(result['repair'], indent=2))


if __name__ == '__main__':
    main()
