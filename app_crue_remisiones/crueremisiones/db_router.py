"""
Database router for CRUE Remisiones.

Routes crueremisiones app models to the 'external' database.
All other apps (auth, admin, sessions, contenttypes) stay on 'default'.
"""


class CrueRemisionesRouter:
    """
    Routes database operations for the crueremisiones app to the 'external' database.
    """

    app_label = 'crueremisiones'

    def db_for_read(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'external'
        return None

    def db_for_write(self, model, **hints):
        if model._meta.app_label == self.app_label:
            return 'external'
        return None

    def allow_relation(self, obj1, obj2, **hints):
        # Allow relations between crueremisiones models
        if (obj1._meta.app_label == self.app_label and
                obj2._meta.app_label == self.app_label):
            return True
        # Allow relations between crueremisiones and auth (for created_by FK)
        if (obj1._meta.app_label == self.app_label or
                obj2._meta.app_label == self.app_label):
            return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.app_label:
            # crueremisiones models only migrate to 'external'
            return db == 'external'
        else:
            # All other apps only migrate to 'default'
            return db == 'default'
