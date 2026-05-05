from django.shortcuts import render
from django.db import connections
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

class DocumentoInventarioListView(LoginRequiredMixin, ListView):
    template_name = 'inventarios/documentos_list.html'
    context_object_name = 'documentos'
    paginate_by = 50

    def get_queryset(self):
        # 1. Determinar qué base de datos usar (Persistir en sesión)
        db_choice = self.request.GET.get('db')
        if db_choice in ['readonly', 'nexus']:
            self.request.session['inventory_db'] = db_choice
        
        # Por defecto usar 'readonly' (DGEMPRES03)
        selected_db = self.request.session.get('inventory_db', 'readonly')

        # Capturar filtros de la URL (Sin valores por defecto para máxima flexibilidad)
        tipo_doc = self.request.GET.get('tipo')
        usuario_oid = self.request.GET.get('usuario')
        estado = self.request.GET.get('estado', '0') # Mantenemos estado 0 (Activo) por defecto
        consecutivo = self.request.GET.get('consecutivo')
        fecha_desde = self.request.GET.get('desde')
        fecha_hasta = self.request.GET.get('hasta')

        base_query = """
        SELECT TOP 500
            CASE 
                WHEN IDTIPDOC= 0 THEN 'ORDEN DE COMPRA'
                WHEN IDTIPDOC= 1 THEN 'REMISION DE ENTRADA'
                WHEN IDTIPDOC= 2 THEN 'COMPROBANTE ENTRADA'
                WHEN IDTIPDOC= 3 THEN 'SUMINISTRO PACIENTE'
                WHEN IDTIPDOC= 4 THEN 'INVENTARIO INICIAL'
                WHEN IDTIPDOC= 5 THEN 'DEVOLUCION SUMINISTRO'
                WHEN IDTIPDOC= 6 THEN 'CIERRE MENSUAL'
                WHEN IDTIPDOC= 7 THEN 'COTIZACION'
                WHEN IDTIPDOC= 8 THEN 'REMISION SALIDA'
                WHEN IDTIPDOC= 9 THEN 'PEDIDO'
                WHEN IDTIPDOC= 10 THEN 'PRESTAMO MERCANCIA'
                WHEN IDTIPDOC= 11 THEN 'AJUSTE INVENTARIO'
                WHEN IDTIPDOC= 12 THEN 'FACTURA'
                WHEN IDTIPDOC= 13 THEN 'COMPROMISOS'
                WHEN IDTIPDOC= 14 THEN 'DEVOLUCION REMISION'
                WHEN IDTIPDOC= 15 THEN 'DEVOLUCION COMPRA'
                WHEN IDTIPDOC= 16 THEN 'DEVOLUCION VENTA'
                WHEN IDTIPDOC= 17 THEN 'ORDEN DESPACHO'
                WHEN IDTIPDOC= 18 THEN 'CONTRATO'
                WHEN IDTIPDOC= 19 THEN 'ORDEN SERVICIO'
                WHEN IDTIPDOC= 20 THEN 'ORDEN PRODUCCION'
                WHEN IDTIPDOC= 21 THEN 'DEVOLUCION ORDEN'
                WHEN IDTIPDOC= 22 THEN 'SOLICITUD PEDIDO'
                WHEN IDTIPDOC= 23 THEN 'DEMANDA INSATISF'
                WHEN IDTIPDOC= 24 THEN 'TRASLADO PRODUCTO'
                WHEN IDTIPDOC= 25 THEN 'RECIBO ORDEN DE'
                WHEN IDTIPDOC= 26 THEN 'RECLASIFICACION RE'
                WHEN IDTIPDOC= -1 THEN 'MOVIMIENTO KARDEX'
                ELSE 'DESCONOCIDO'
            END AS TIPO_DOCUMENTO_TEXT, 
            "GENUSUARIO"."USUDESCRI" as USUARIO_NOMBRE,
            INNDOCUME.*
        FROM INNDOCUME
        INNER JOIN "dbo"."GENUSUARIO" "GENUSUARIO" 
            ON "GENUSUARIO"."OID" = "INNDOCUME"."GENUSUARIO2"
        WHERE 1=1
        """
        
        params = []
        if tipo_doc:
            base_query += " AND IDTIPDOC = %s "
            params.append(tipo_doc)
        
        if usuario_oid:
            base_query += " AND GENUSUARIO2 = %s "
            params.append(usuario_oid)
            
        if estado:
            base_query += " AND IDESTADO = %s "
            params.append(estado)
            
        if consecutivo:
            consec_clean = consecutivo.strip()
            if consec_clean.isdigit():
                consec_padded = consec_clean.zfill(14)
                base_query += " AND (IDCONSEC = %s OR IDCONSEC LIKE %s) "
                params.append(consec_padded)
                params.append(f"%{consec_clean}")
            else:
                base_query += " AND IDCONSEC LIKE %s "
                params.append(f"%{consec_clean}%")
        
        # Solo aplicar fechas si se proporcionan explícitamente
        if fecha_desde:
            base_query += " AND IDFECDOC >= %s "
            params.append(fecha_desde)
            
        if fecha_hasta:
            base_query += " AND IDFECDOC <= %s "
            params.append(fecha_hasta + " 23:59:59")

        # Orden ASC según script del usuario para ver lo más antiguo pendiente primero
        base_query += " ORDER BY INNDOCUME.IDFECDOC ASC "
        
        with connections[selected_db].cursor() as cursor:
            cursor.execute(base_query, params)
            columns = [col[0] for col in cursor.description]
            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        selected_db = self.request.session.get('inventory_db', 'readonly')
        ctx['selected_db'] = selected_db
        ctx['titulo'] = 'Listado de Documentos de Inventario'
        
        tipo_doc = self.request.GET.get('tipo')
        usuario_oid = self.request.GET.get('usuario')
        estado = self.request.GET.get('estado', '0')
        fecha_desde = self.request.GET.get('desde')
        fecha_hasta = self.request.GET.get('hasta')
        
        ctx['fecha_desde_default'] = fecha_desde
        ctx['fecha_hasta_default'] = fecha_hasta

        # 1. Obtener lista completa de usuarios para el dropdown (Optimizado)
        with connections[selected_db].cursor() as cursor:
            cursor.execute("SELECT OID, USUDESCRI FROM GENUSUARIO ORDER BY USUDESCRI")
            ctx['usuarios_responsables'] = [dict(zip(['OID', 'USUDESCRI'], row)) for row in cursor.fetchall()]

        # 2. Obtener resumen de responsables según FILTROS ACTUALES
        summary_query = """
        SELECT USUDESCRI, COUNT(*) as TOTAL
        FROM INNDOCUME
        INNER JOIN "dbo"."GENUSUARIO" "GENUSUARIO" ON "GENUSUARIO"."OID" = "INNDOCUME"."GENUSUARIO2"
        WHERE 1=1
        """
        params = []
        if tipo_doc:
            summary_query += " AND IDTIPDOC = %s "
            params.append(tipo_doc)
        if usuario_oid:
            summary_query += " AND GENUSUARIO2 = %s "
            params.append(usuario_oid)
        if estado:
            summary_query += " AND IDESTADO = %s "
            params.append(estado)
        if fecha_desde:
            summary_query += " AND IDFECDOC >= %s "
            params.append(fecha_desde)
        if fecha_hasta:
            summary_query += " AND IDFECDOC <= %s "
            params.append(fecha_hasta + " 23:59:59")

        summary_query += " GROUP BY USUDESCRI ORDER BY TOTAL DESC "

        with connections[selected_db].cursor() as cursor:
            cursor.execute(summary_query, params)
            ctx['resumen_responsables'] = [dict(zip(['nombre', 'total'], row)) for row in cursor.fetchall()]

        ctx['tipos_doc'] = [
            (0, 'ORDEN DE COMPRA'), (1, 'REMISION DE ENTRADA'), (2, 'COMPROBANTE ENTRADA'),
            (3, 'SUMINISTRO PACIENTE'), (4, 'INVENTARIO INICIAL'), (5, 'DEVOLUCION SUMINISTRO'),
            (6, 'CIERRE MENSUAL'), (7, 'COTIZACION'), (8, 'REMISION SALIDA'),
            (9, 'PEDIDO'), (10, 'PRESTAMO MERCANCIA'), (11, 'AJUSTE INVENTARIO'),
            (12, 'FACTURA'), (13, 'COMPROMISOS'), (14, 'DEVOLUCION REMISION'),
            (15, 'DEVOLUCION COMPRA'), (16, 'DEVOLUCION VENTA'), (17, 'ORDEN DESPACHO'),
            (18, 'CONTRATO'), (19, 'ORDEN SERVICIO'), (20, 'ORDEN PRODUCCION'),
            (21, 'DEVOLUCION ORDEN'), (22, 'SOLICITUD PEDIDO'), (23, 'DEMANDA INSATISF'),
            (24, 'TRASLADO PRODUCTO'), (25, 'RECIBO ORDEN DE'), (26, 'RECLASIFICACION RE'),
            (-1, 'MOVIMIENTO KARDEX')
        ]
            
        return ctx
