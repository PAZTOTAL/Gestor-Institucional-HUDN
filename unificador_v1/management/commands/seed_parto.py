from django.core.management.base import BaseCommand
from unificador_v1.models.parto import (
    ItemParto as Item,
    ParametroParto as Parametro,
    CampoParametroParto as CampoParametro,
    TipoValorParto as TipoValor,
    AseguradoraParto as Aseguradora,
)


class Command(BaseCommand):
    help = 'Poblar las tablas Item, Parametro y CampoParametro con datos clínicos de trabajo de parto'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando seed de datos clínicos...')
        self.create_aseguradoras()

        items_data = [
            {
                'codigo': 'CTRL_MAT',
                'nombre': 'Controles Maternos',
                'parametros': [
                    {'codigo': 'TENSION_ART',    'nombre': 'Tensión arterial',         'unidad': 'mmHg', 'orden': 1},
                    {'codigo': 'FREC_CARD',       'nombre': 'Frec. Cardiaca',           'unidad': 'lpm',  'orden': 2},
                    {'codigo': 'FREC_RESP',       'nombre': 'Frec. Respiratoria',       'unidad': 'rpm',  'orden': 3},
                    {'codigo': 'TEMPERATURA',     'nombre': 'Temperatura',              'unidad': '°C',   'orden': 4},
                ],
            },
            {
                'codigo': 'CONTRAC_UTER',
                'nombre': 'Contracciones uterinas',
                'parametros': [
                    {'codigo': 'FRECUENCIA',  'nombre': 'Frecuencia', 'unidad': 'min',  'orden': 1},
                    {'codigo': 'DURACION',    'nombre': 'Duración',   'unidad': 'seg',  'orden': 2},
                    {'codigo': 'INTENSIDAD',  'nombre': 'Intensidad', 'unidad': None,   'orden': 3},
                ],
            },
            {
                'codigo': 'CTRL_FETAL',
                'nombre': 'Control Fetal',
                'parametros': [
                    {'codigo': 'FREC_CARD_FETAL', 'nombre': 'Frecuencia Cardiaca Fetal', 'unidad': 'lpm', 'orden': 1},
                    {'codigo': 'MOV_FETALES',     'nombre': 'Movimientos Fetales',       'unidad': None,  'orden': 2},
                    {'codigo': 'PRESENTACION',    'nombre': 'Presentación',              'unidad': None,  'orden': 3},
                ],
            },
            {
                'codigo': 'TACTO_VAG',
                'nombre': 'Tacto Vaginal',
                'parametros': [
                    {'codigo': 'MEMB_INTEGRAS', 'nombre': 'Membranas Integras', 'unidad': None,  'orden': 1},
                    {'codigo': 'MEMB_ROTAS',    'nombre': 'Membranas Rotas',    'unidad': None,  'orden': 2},
                    {'codigo': 'LIQ_AMNIOTICO', 'nombre': 'Liquido Amniotico',  'unidad': None,  'orden': 3},
                    {'codigo': 'HORA_RUPTURA',  'nombre': 'Hora Ruptura',       'unidad': None,  'orden': 4},
                    {'codigo': 'DILATACION',    'nombre': 'Dilatación',         'unidad': 'cm',  'orden': 5},
                    {'codigo': 'BORRAMIENTO',   'nombre': 'Borramiento',        'unidad': '%',   'orden': 6},
                ],
            },
            {
                'codigo': 'MON_FETAL',
                'nombre': 'Monitoreo Fetal',
                'parametros': [
                    {'codigo': 'HORA',      'nombre': 'Hora',      'unidad': None, 'orden': 1},
                    {'codigo': 'CATEGORIA', 'nombre': 'Categoria', 'unidad': None, 'orden': 2},
                ],
            },
            {
                'codigo': 'OXITOCINA',
                'nombre': 'Oxitocina',
                'parametros': [
                    {'codigo': 'MILIUNIDADES', 'nombre': 'Miliunidades', 'unidad': 'mU',   'orden': 1},
                    {'codigo': 'CC_H',         'nombre': 'CC/H',         'unidad': 'cc/h', 'orden': 2},
                ],
            },
        ]

        for item_data in items_data:
            item, created = Item.objects.get_or_create(
                codigo=item_data['codigo'],
                defaults={'nombre': item_data['nombre']}
            )
            estado = '[OK] Creado' if created else '[-] Existente'
            self.stdout.write(f'{estado}: Item {item.nombre}')

            for pd in item_data['parametros']:
                param, created = Parametro.objects.get_or_create(
                    item=item,
                    codigo=pd['codigo'],
                    defaults={'nombre': pd['nombre'], 'unidad': pd['unidad'], 'orden': pd['orden']}
                )
                estado = '[OK]' if created else '[-]'
                self.stdout.write(f'  {estado} Parametro: {param.nombre}')

        self.create_campos()
        self.stdout.write(self.style.SUCCESS('\n¡Seed completado exitosamente!'))

    def create_aseguradoras(self):
        self.stdout.write('\nAseguradoras:')
        for nombre in ['Sura EPS', 'Nueva EPS', 'Sanitas', 'Famisanar', 'Coosalud', 'Mutual SER', 'Emssanar']:
            _, created = Aseguradora.objects.get_or_create(nombre=nombre)
            self.stdout.write(f'  {"[OK]" if created else "[-]"} {nombre}')

    def create_campos(self):
        self.stdout.write('\nCampos de parámetros:')

        tension = Parametro.objects.filter(codigo='TENSION_ART').first()
        if tension:
            for cod, nom, orden in [('SISTOLICA', 'Sistólica', 1), ('DIASTOLICA', 'Diastólica', 2)]:
                _, created = CampoParametro.objects.get_or_create(
                    parametro=tension, codigo=cod,
                    defaults={'nombre': nom, 'tipo_valor': TipoValor.NUMBER, 'unidad': 'mmHg', 'orden': orden}
                )
                self.stdout.write(f'  {"[OK]" if created else "[-]"} TENSION_ART ->{nom}')

        numeric_params = ['FREC_CARD', 'FREC_RESP', 'TEMPERATURA', 'FREC_CARD_FETAL', 'DILATACION', 'BORRAMIENTO',
                          'MILIUNIDADES', 'CC_H']
        for cod in numeric_params:
            param = Parametro.objects.filter(codigo=cod).first()
            if param:
                _, created = CampoParametro.objects.get_or_create(
                    parametro=param, codigo='VALOR',
                    defaults={'nombre': 'Valor', 'tipo_valor': TipoValor.NUMBER, 'unidad': param.unidad, 'orden': 1}
                )
                self.stdout.write(f'  {"[OK]" if created else "[-]"} {cod} ->Valor')

        text_params = ['INTENSIDAD', 'MOV_FETALES', 'PRESENTACION', 'LIQ_AMNIOTICO', 'CATEGORIA']
        for cod in text_params:
            param = Parametro.objects.filter(codigo=cod).first()
            if param:
                _, created = CampoParametro.objects.get_or_create(
                    parametro=param, codigo='DESCRIPCION',
                    defaults={'nombre': 'Descripción', 'tipo_valor': TipoValor.TEXT, 'orden': 1}
                )
                self.stdout.write(f'  {"[OK]" if created else "[-]"} {cod} ->Descripción')

        bool_params = ['MEMB_INTEGRAS', 'MEMB_ROTAS']
        for cod in bool_params:
            param = Parametro.objects.filter(codigo=cod).first()
            if param:
                _, created = CampoParametro.objects.get_or_create(
                    parametro=param, codigo='ESTADO',
                    defaults={'nombre': 'Estado', 'tipo_valor': TipoValor.BOOLEAN, 'orden': 1}
                )
                self.stdout.write(f'  {"[OK]" if created else "[-]"} {cod} ->Estado')

        time_params = ['FRECUENCIA', 'DURACION', 'HORA_RUPTURA', 'HORA']
        for cod in time_params:
            param = Parametro.objects.filter(codigo=cod).first()
            if param:
                _, created = CampoParametro.objects.get_or_create(
                    parametro=param, codigo='TIEMPO',
                    defaults={'nombre': 'Tiempo', 'tipo_valor': TipoValor.TEXT, 'orden': 1}
                )
                self.stdout.write(f'  {"[OK]" if created else "[-]"} {cod} ->Tiempo')
