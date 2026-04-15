import os
import re

DIR = r'c:\Users\Daniel Ibarra\Documents\DEFENJUR\defenjur_py\templates\legal'

mapping = {
    'tutela_list.html': ('tutela', 'tutela.id'),
    'peticion_list.html': ('peticion', 'p.id'),
    'proceso_activa_list.html': ('proceso_activo', 'p.id'),
    'proceso_pasiva_list.html': ('proceso_pasivo', 'p.id'),
    'proceso_terminado_list.html': ('proceso_terminado', 'p.id'),
    'peritaje_list.html': ('peritaje', 'p.id'),
    'pago_list.html': ('pago', 'p.id'),
    'sancionatorio_list.html': ('sancionatorio', 'p.id'),
    'requerimiento_list.html': ('requerimiento', 'r.id')
}

for filename, (tipo, id_var) in mapping.items():
    filepath = os.path.join(DIR, filename)
    if os.path.exists(filepath):
        content = open(filepath, 'r', encoding='utf-8').read()
        
        def repl(match):
            btn_inner = match.group(0)
            if 'hx-delete' not in btn_inner:
                return f'<button style="background:none;border:none;color:#f43f5e;cursor:pointer;" title="Eliminar" hx-delete="{{% url \'eliminar_registro\' \'{tipo}\' {id_var} %}}" hx-target="closest tr" hx-swap="outerHTML" hx-confirm="¿Seguro que desea eliminar el registro?"><i data-lucide="trash-2" style="width:18px;"></i></button>'
            return btn_inner

        content = re.sub(r'<button[^>]*>[^<]*<i data-lucide="trash-2"[^>]*></i>[^<]*</button>', repl, content)
        
        open(filepath, 'w', encoding='utf-8').write(content)
        print(f'Modificado {filename}')
