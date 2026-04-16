class HospitalRouter:
    """
    A router to control all database operations on models in the
    auth and contenttypes applications.
    """
    route_app_labels = {'consultas_externas', 'consultas'}

    def db_for_read(self, model, **hints):
        """
        Attempts to read from the readonly database for specific apps.
        """
        if model._meta.app_label in self.route_app_labels:
            return 'readonly'
        return 'default'

    def db_for_write(self, model, **hints):
        """
        Attempts to write to the readonly database for specific apps.
        (Although they are readonly, Django needs a target DB)
        """
        if model._meta.app_label in self.route_app_labels:
            return 'readonly'
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        """
        Allow relations if a model in the route_app_labels is involved.
        """
        if (
            obj1._meta.app_label in self.route_app_labels or
            obj2._meta.app_label in self.route_app_labels
        ):
           return True
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """
        Do not allow migrations for external apps (consultas_externas, consultas)
        """
        if app_label in self.route_app_labels:
            return False
        return db == 'default'
