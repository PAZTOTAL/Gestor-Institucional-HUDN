"""
Router de base de datos para dirigir los modelos de la app 'clinico'
a la base de datos 'default' (clinico_sql) para operaciones CRUD.

Nota: Para consultas a DGEMPRES99 (base de datos de solo lectura del hospital),
se debe usar explícitamente .using('readonly') en las consultas.
"""


class PartoRouter:
    """
    Router que dirige todos los modelos de la app 'parto' 
    a la base de datos 'default' (clinico_sql) para operaciones CRUD.
    
    La base de datos 'readonly' (DGEMPRES99) se usa solo para consultas
    directas de datos del hospital y debe especificarse explícitamente
    usando .using('readonly').
    """
    
    # Nombre de la app que debe usar default
    app_label = 'parto'
    
    # Nombre de la base de datos destino para modelos parto
    db_name = 'default'  # clinico_sql
    
    def db_for_read(self, model, **hints):
        """
        Sugiere qué base de datos usar para operaciones de lectura.
        Los modelos de 'parto' usan 'default' (clinico_sql).
        Para consultar DGEMPRES99, usar explícitamente .using('readonly').
        """
        if model._meta.app_label == self.app_label:
            return self.db_name
        return None
    
    def db_for_write(self, model, **hints):
        """
        Sugiere qué base de datos usar para operaciones de escritura.
        Los modelos de 'parto' siempre escriben en 'default' (clinico_sql).
        """
        if model._meta.app_label == self.app_label:
            return self.db_name
        return None
    
    def allow_relation(self, obj1, obj2, **hints):
        """
        Permite relaciones entre objetos si ambos están en la misma base de datos.
        """
        # Si ambos objetos son de la app parto, permitir la relación
        if (obj1._meta.app_label == self.app_label and 
            obj2._meta.app_label == self.app_label):
            return True
        
        # Si uno es de parto y el otro no, no permitir relación
        # (ya que están en bases de datos diferentes)
        if (obj1._meta.app_label == self.app_label or 
            obj2._meta.app_label == self.app_label):
            return False
        
        # Para otros casos, permitir (Django decidirá)
        return None
    
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Asegura que las migraciones de 'parto' solo se ejecuten en 'default' (clinico_sql).
        Las migraciones de otras apps solo se ejecutan en 'default'.
        La base de datos 'readonly' (DGEMPRES99) nunca debe recibir migraciones.
        """
        if app_label == self.app_label:
            # Las migraciones de parto solo en default (clinico_sql)
            return db == self.db_name
        else:
            # Las migraciones de otras apps solo en default
            return db == 'default'
