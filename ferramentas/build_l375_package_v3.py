#!/usr/bin/env python3
"""Build the Epson L375 4624 mm + experimental borderless bundle (V3)."""
import hashlib
import json
import re
import shutil
import struct
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'L375_X64_260_LA.exe'
SOURCE_SHA256 = '1d121e1d46dd647303f985eabd563f3d2801273c9e1a4fbd0bbee74d193fd06c'
ANALYSIS = ROOT / 'analysis' / 'l375'
OUT = ROOT / 'dist' / 'L375_4624mm_SEM_MARGEM_WIN7_V3'
NS = {'e': 'http://schema.epson.net/fusion/business/v150'}
FILES = [
    ('E_JC1N9A.CFX', 'E_TCXN8A.CFX', 'ce34976fee477b08c4c798e11e1761205cbabed352df916420cf99c679cf4ddf', 'cb186b5120acce700c67a69134365e6cea80e21113ec47c3db18f6a023c7db09;1fdf74439b88ba5728bbfc08e01a7b90a4f7ee243a87f8cc998297cadd121356'),
    ('E_JC1N9E.CFX', 'E_TCXN8E.CFX', 'bf9bda9c8977bc86d2bc183a07b694ace42f7f2d6a262aed27e3b4403b4f7353', '1878eb1f457a38d060621ed1134365c5f985b80891efdc9c23a5039f9585a0a9;88629d518afc86365d8250474a23f245fcbab6811fe0cccbdd70147bb460643d'),
]
BINARIES = [
    (['ConfigFile'], 'E_WU1MA0.DLL', 'E_YUICN8E.DLL', '95293390d98319fd8e097a1ba09fd61dcc7bec131cbf05a00abd2c7e79c967c5'),
    (['DriverPath'], 'E_WMAI50.DLL', 'E_YMAIN8E.DLL', '5ad910fc3d4210fa30389da395682eb3ab7801c15ce23bb2cc0cb55861bdf04d'),
    (['DataFile'], 'E_WM1N8E.VIF', 'E_YVIFN8E.VIF', 'f89d1b151c412797255ff4c91b0620baeb641df59e962dafe946f329d6343e46'),
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def patch_config(data):
    """Set 4624 mm limits; field 230 (Check Paper Width) stays hidden as shipped."""
    tree = ET.fromstring(data)
    extent = tree.findall("e:f/e:F[@f='7']/e:E[@e='261']", NS)
    metric = tree.findall("e:f/e:F[@f='11']/e:E[@e='0']/e:V", NS)
    imperial = tree.findall("e:f/e:F[@f='13']/e:E[@e='0']/e:V", NS)
    assert len(extent) == len(metric) == len(imperial) == 1
    assert (extent[0].get('J'), extent[0].get('K')) == ('2159', '11176')
    assert (metric[0].get('n'), metric[0].get('x'), metric[0].text) == ('1270', '11176', '2970')
    assert (imperial[0].get('n'), imperial[0].get('x'), imperial[0].text) == ('500', '4400', '1169')
    field_230 = tree.find("e:f/e:F[@f='230']", NS)
    reset_230 = tree.find("e:y/e:F[@f='230']", NS)
    assert field_230 is not None and field_230.get('r') == '20145' and field_230.get('S') == 'f'
    assert reset_230 is not None
    replacements = [(b'K="11176"', b'K="46240"'), (b'x="11176"', b'x="46240"'), (b'x="4400"', b'x="18205"')]
    extent[0].set('K', '46240')
    metric[0].set('x', '46240')
    imperial[0].set('x', '18205')
    result = data
    for before, after in replacements:
        assert data.count(before) == 1
        result = result.replace(before, after)
    assert ET.tostring(tree) == ET.tostring(ET.fromstring(result))
    patched_tree = ET.fromstring(result)
    assert patched_tree.find("e:f/e:F[@f='230']", NS) is not None
    assert patched_tree.find("e:f/e:F[@f='230']", NS).get('S') == 'f'
    assert patched_tree.find("e:y/e:F[@f='230']", NS) is not None
    return add_borderless(result)

# The L375 driver ships the borderless controls (Main 2793, user size 6307) but
# no CFX definitions; these come from the L4260 CFX (same z="103" schema).
L4260_BORDERLESS_TABLE = (
    '<BE T="0" N="6" U="0"/>'
    '<BD i="0" e="1" o="2" di="27" W="360" X="110" Y="360" Z="310"/>'
    '<BD i="1" e="1" o="1" di="28" W="180" X="60" Y="180" Z="160"/>'
    '<BD i="2" e="1" o="0" di="29" W="90" X="30" Y="90" Z="80"/>'
    '<BD i="3" e="2" o="2" di="30" W="360" X="130" Y="360" Z="380"/>'
    '<BD i="4" e="2" o="1" di="31" W="180" X="70" Y="180" Z="190"/>'
    '<BD i="5" e="2" o="0" di="32" W="90" X="40" Y="90" Z="100"/>'
)
# Field 213 without L4260's message index (m="38"), which may differ in this UI.
L4260_BORDERLESS_FIELDS = (
    '<F f="213" r="20142" t="0" F="0x0300"><E e="0" r="10000" D="t"/><E e="1" r="10001"/></F>'
    '<F f="214" r="20143" t="0" F="0x0308"><E e="0" r="10234"/><E e="1" r="10235"/><E e="2" r="10236" D="t"/>'
    '<D><C><E f="213" e="0"/></C></D></F>'
    '<F f="215" r="20144" t="0" F="0x0308"><E e="0" r="10237" D="t"/><E e="1" r="10238"><R><E f="214" C="t"/></R></E>'
    '<D><C><E f="213" e="0"/></C></D></F>'
)
SMALL_BORDERLESS = {'285', '281', '263'}


def add_borderless(data):
    """Add L4260 borderless fields, expansion table and source; open every feedable size."""
    text = data.decode('utf-8')
    assert '<F f="213"' not in text and '<BD ' not in text
    anchor = '<SV v="0x00000006"/></l>'
    assert text.count(anchor) == 1
    text = text.replace(anchor, L4260_BORDERLESS_TABLE + anchor)
    anchor = '<F f="230" r="20145"'
    assert text.count(anchor) == 1
    text = text.replace(anchor, L4260_BORDERLESS_FIELDS + anchor)
    anchor = '<F f="35"/><F f="16"/>'
    assert text.count(anchor) == 1 and text.index(anchor) > text.index('<y>')
    text = text.replace(anchor, '<F f="35"/><F f="213"/><F f="214"/><F f="215"/><F f="16"/>')
    user = re.search(r'<E e="261" r="98" [^>]*/>', text).group(0)
    attrs = dict(re.findall(r' (\w+)="([^"]*)"', user))
    assert attrs['K'] == '46240' and 'se' not in attrs
    # sr 87 -> string 2487 "Rear Feed-Borderless" (F f=7 uses base b="2400").
    patched = user.replace('<E e="261" r="98" ', '<E e="261" r="98" se="292" sr="87" ', 1)
    patched = patched.replace(' K="46240"', f' K="46240" Dw="{attrs["j"]}" Dh="{attrs["k"]}" DW="{attrs["J"]}" DH="46240"', 1)
    text = text.replace(user, patched, 1)
    for field, label in (('9', '20004'), ('35', '20025')):
        start = text.index(f'<F f="{field}" r="{label}"')
        end = text.index('</F>', start)

        def mark(match):
            entry = match.group(0)
            if ' p="' in entry or ' L="t"' in entry or match.group(1) == '256' or ' w="' not in entry:
                return entry
            kind = '1' if match.group(1) in SMALL_BORDERLESS else '2'
            # Same attribute position as the L4260 CFX: right after the length.
            return re.sub(r'( l="\d+")', rf'\1 p="{kind}" P="{kind}"', entry, count=1)
        text = text[:start] + re.sub(r'<E e="(\d+)" [^>]*>', mark, text[start:end]) + text[end:]
    result = text.encode('utf-8')
    tree = ET.fromstring(result)
    for field in ('213', '214', '215'):
        assert tree.find(f"e:f/e:F[@f='{field}']", NS) is not None
        assert tree.find(f"e:y/e:F[@f='{field}']", NS) is not None
    assert len(tree.findall('e:i/e:l/e:BD', NS)) == 6
    source = tree.find("e:f/e:F[@f='7']/e:E[@e='261']", NS)
    assert (source.get('se'), source.get('sr'), source.get('DH')) == ('292', '87', '46240')
    for field in ('9', '35'):
        for entry in tree.findall(f"e:f/e:F[@f='{field}']/e:E", NS):
            if entry.get('w') and entry.get('L') != 't' and entry.get('e') != '256':
                assert entry.get('p') in ('1', '2'), (field, entry.attrib)
    return result


def text_file(path, text):
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8-sig'))


def make_test_pdf(path, length_mm, model='L375'):
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
        line(15, mm, 40 if mm != 1100 else 180, mm)
        label(45, mm + 4, f'{mm} mm' + (' - perto do antigo limite (1117 mm)' if mm == 1100 else ''))
        if mm in (1300, 1500, 2000, 2500, 3000, 3500, 4000, 4500):
            label(90, mm + 4, f'MARCA ALEM DO ANTIGO LIMITE: {mm / 1000:.1f} m', 10)
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
    assert digest(SOURCE.read_bytes()) == SOURCE_SHA256, 'Unexpected L375 installer'
    inf = (ANALYSIS / 'windows64' / 'WINX64' / 'E_WF1N8E.INF').read_text(encoding='utf-16le')
    assert '"EPSON L375 Series"' in inf
    assert 'DriverVer=10/09/2025,2.60.00.00' in inf
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'patch').mkdir(exist_ok=True)
    (OUT / 'originais').mkdir(exist_ok=True)
    entries = []
    for source_name, installed_name, expected, previous in FILES:
        assert installed_name + ',' + source_name in inf
        original = (ANALYSIS / 'unpacked' / source_name).read_bytes()
        assert digest(original) == expected, source_name
        patched = patch_config(original)
        (OUT / 'patch' / installed_name).write_bytes(patched)
        (OUT / 'originais' / installed_name).write_bytes(original)
        entries.append({
            'source_name': source_name, 'installed_name': installed_name,
            'original_sha256': expected, 'patched_sha256': digest(patched),
            'previous_sha256': previous,
            'changed_attributes': ['F[f=7]/E[e=261]@K', 'F[f=11]/E[e=0]/V@x', 'F[f=13]/E[e=0]/V@x', 'l/BE,BD (L4260)', 'F[f=213,214,215] + y (L4260)', 'F[f=7]/E[e=261]@se,sr,Dw,Dh,DW,DH', 'F[f=9,35]/E@p,P'],
        })
    binaries = []
    for properties, source_name, installed_name, expected in BINARIES:
        assert installed_name + ',' + source_name in inf
        data = (ANALYSIS / 'unpacked' / source_name).read_bytes()
        assert digest(data) == expected, source_name
        if source_name.endswith('.DLL'):
            pe_offset = struct.unpack_from('<I', data, 0x3c)[0]
            assert data[pe_offset:pe_offset + 4] == b'PE\0\0'
            assert struct.unpack_from('<H', data, pe_offset + 4)[0] == 0x8664, 'Non-AMD64 DLL'
        binaries.append({'properties': properties, 'source_name': source_name, 'installed_name': installed_name, 'sha256': expected})
    manifest = {
        'format': 1, 'release': 3, 'status': 'experimental-not-tested-on-windows-or-printer',
        'driver': 'EPSON L375 Series', 'driver_version': '2.60.00.00',
        'architecture': 'amd64', 'minimum_powershell': '2.0',
        'target_os': 'Windows 7 x64', 'legacy_inf': 'E_WF1N8E.INF',
        'original_installer_sha256': SOURCE_SHA256,
        'original_max_length_tenths_mm': 11176, 'patched_max_length_tenths_mm': 46240,
        'patched_max_length_hundredths_inch': 18205,
        'binaries': binaries, 'files': entries,
    }
    text_file(OUT / 'manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    document = ET.Element('l375', {'format': '1', 'driver': manifest['driver'], 'original_installer_sha256': SOURCE_SHA256})
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
    script = (ROOT / 'tools' / 'Install-L375-Win7-V3.ps1').read_text()
    assert not re.search(r'(?i)-(shr|shl|in|notin)\b', script), 'PS3+ operator in PS2 installer'
    for incompatible in ['Get-Printer', 'Get-PrintJob', 'Get-FileHash', 'ConvertFrom-Json', 'ConvertTo-Json', '-Raw', '[pscustomobject]', '$PSScriptRoot', '$PSCommandPath', 'IsNullOrWhiteSpace', 'Is64BitProcess', 'Is64BitOperatingSystem']:
        assert incompatible not in script, 'Unexpected installer dependency: ' + incompatible
    text_file(OUT / 'Install-L375.ps1', script)
    text_file(OUT / 'L375-Process.cs', (ROOT / 'tools' / 'L375-Process.cs').read_text())
    text_file(OUT / 'L375-Spooler.cs', (ROOT / 'tools' / 'L375-Spooler.cs').read_text())
    for name, action in [('instalar', 'Install'), ('restaurar', 'Restore'), ('verificar', 'Verify'), ('abrir-preferencias', 'Preferences')]:
        cmd = rf'''@echo off
setlocal
cd /d "%~dp0"
set "L375_POWERSHELL=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if exist "%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe" set "L375_POWERSHELL=%SystemRoot%\Sysnative\WindowsPowerShell\v1.0\powershell.exe"
"%L375_POWERSHELL%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-L375.ps1" -Action {action}
set "L375_RESULT=0"
if errorlevel 1 set "L375_RESULT=1"
if errorlevel 2 set "L375_RESULT=2"
if errorlevel 3 set "L375_RESULT=1"
if not errorlevel 0 set "L375_RESULT=1"
echo.
echo Codigo %L375_RESULT%: 0 = concluido; 1 = erro; 2 = verificacao pendente ou limite nao confirmado.
pause
exit /b %L375_RESULT%
'''
        (OUT / (name + '.cmd')).write_bytes(cmd.replace('\n', '\r\n').encode('ascii'))
    for length in (1500, 3000, 4600):
        make_test_pdf(OUT / f'teste-{length}mm.pdf', length, model='L375')
    text_file(OUT / 'LEIA-ME.txt', r"""EPSON L375 V3 - SEM MARGEM EXPERIMENTAL E PAPEL ATE 4624 mm
Windows 7 x64 Intel/AMD, PowerShell 2.0 ou superior

ATENCAO: a Epson nao fez sem margem para a L375. Nem o driver de Windows
nem os dados da Epson para Linux listam tamanho sem margem para ela. Esta
versao liga o sem margem por conta e risco. A tinta que passa da borda do
papel pode cair na base da impressora (a L375 nao tem espuma para isso) e
manchar o verso das proximas folhas.

1. Extraia TODO o ZIP em uma pasta nova.
2. Feche as preferencias Epson e os aplicativos que usam a impressora.
   Aguarde as filas de impressao terminarem.
3. Clique com o botao direito em instalar.cmd > Executar como administrador.
4. Ao terminar, confira "comprimento maximo informado": 4624 mm.
5. Execute abrir-preferencias.cmd e veja se aparece a caixa "Sem margens"
   na tela Principal e a opcao "Sem margens" no Definido pelo usuario.
6. PRIMEIRO TESTE: uma folha 10 x 15 cm ou A4 velha, sem margem, com uma
   imagem que encoste nas bordas. Depois de imprimir, abra a tampa e olhe a
   base por onde o papel passa. Se tiver tinta, limpe com pano umido e nao
   continue com sem margem.
7. So depois teste papel longo (teste-3000mm.pdf, depois teste-4600mm.pdf).
8. Se der erro ou a impressora recusar, rode restaurar.cmd.

O que a V3 faz:
A tela da L375 ja tem os controles de sem margem (caixa 2793 na Principal,
opcao 6307 no papel do usuario), mas o CFX nao define o recurso. A V3
copia do CFX da L4260 (mesmo esquema z="103") os campos 213-215 (Sem
margens, Expansao, Metodo), a tabela de expansao BE/BD e a origem
"Alimentador traseiro - Sem margens"; marca sem margem em todos os
tamanhos que a L375 alimenta e abre o papel do usuario sem margem de 89 a
215,9 mm de largura e 127 a 4624 mm de comprimento. A3, A3+, A2, B4 e B3
(maiores que a impressora) ficam como estao. O aviso de sem margem da
L4260 nao foi copiado.

O instalador reconhece o CFX original de 1117,6 mm, o da V1 e o da V2.
Sem perfis em %ProgramData%\EPSON\EPSON L375 Series, ajusta os CFX do
driver no spooler e o driver regenera o cache. Nao modifica DLLs,
registro, permissoes, assinaturas ou DriverStore.

restaurar.cmd recupera os CFX originais de 1117,6 mm (exige backup da V3).
verificar.cmd consulta arquivos e o limite sem aplicar nada.
Logs e backups: C:\ProgramData\L375-Comprimento-Experimental-Win7

Pacote experimental; nada disso foi testado no Windows ou na impressora.
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
    repair = ROOT / 'dist' / 'L375_CORRECAO_PREFERENCIAS_V3.zip'
    repair_files = [path for path in sorted(OUT.rglob('*')) if path.is_file() and path.name not in ['DriverOriginal.exe', 'SHA256SUMS.txt']]
    repair_sums = ''.join(f'{digest(path.read_bytes())}  {path.relative_to(OUT).as_posix()}\n' for path in repair_files)
    with zipfile.ZipFile(repair, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in repair_files:
            z.write(path, Path('L375_CORRECAO_PREFERENCIAS_V3') / path.relative_to(OUT))
        z.writestr('L375_CORRECAO_PREFERENCIAS_V3/SHA256SUMS.txt', repair_sums)
    with zipfile.ZipFile(repair) as z:
        assert z.testzip() is None
    result['repair'] = {'archive': str(repair), 'bytes': repair.stat().st_size, 'sha256': digest(repair.read_bytes())}
    (ANALYSIS / 'package-build-v3.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ['archive', 'bytes', 'sha256']}, indent=2))
    print(json.dumps(result['repair'], indent=2))


if __name__ == '__main__':
    main()
