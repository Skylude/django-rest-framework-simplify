from rest_framework_simplify.views import (
    SimplifyStoredProcedureView,
    SimplifyView,
    SimplifyEmailTemplateView,
)

from tests.models import (
    BasicClass,
    ChildClass,
    LinkingClass,
    MetaDataClass,
    OneToOneClass,
    RequestFieldSaveClass,
    PhaseGroup,
    ModelWithParentResource,
)
from tests import forms, email_templates


class BasicClassHandler(SimplifyView):
    def __init__(self):
        super().__init__(
            BasicClass,
            supported_methods=["GET", "GET_LIST", "POST_SUB", "POST", "DELETE"],
        )


class ChildClassHandler(SimplifyView):
    def __init__(self):
        linked_objects = []
        child_one = {
            "parent_resource": "basicClasses",
            "parent_cls": BasicClass,
            "parent_name": "basic_class",
            "linking_cls": None,
            "sub_resource_name": "child_one",
            "lives_on_parent": True,
        }
        linked_objects.append(child_one)
        super().__init__(
            ChildClass,
            supported_methods=["GET", "GET_SUB", "POST_SUB"],
            linked_objects=linked_objects,
        )


class LinkingClassWithNoLinkingClsDefinedHandler(SimplifyView):
    def __init__(self):
        linked_objects = []
        linking_class = {
            "parent_resource": "basicClasses",
            "parent_cls": BasicClass,
            "parent_name": "basic_class",
            "linking_cls": None,
            "sub_resource_name": "child_class",
        }
        linked_objects.append(linking_class)
        super().__init__(
            ChildClass,
            supported_methods=["GET", "POST_SUB"],
            linked_objects=linked_objects,
        )


class LinkingClassHandler(SimplifyView):
    def __init__(self):
        linked_objects = []
        linking_class = {
            "parent_resource": "basicClasses",
            "parent_cls": BasicClass,
            "parent_name": "basic_class",
            "linking_cls": LinkingClass,
            "sub_resource_name": "child_class",
        }
        linked_objects.append(linking_class)
        super().__init__(
            ChildClass,
            supported_methods=["GET", "POST_SUB", "DELETE", "DELETE_SUB"],
            linked_objects=linked_objects,
        )


class MetaDataClassHandler(SimplifyView):
    def __init__(self):
        super().__init__(MetaDataClass, supported_methods=["GET"])


class ReadReplicaBasicClassHandler(SimplifyView):
    def __init__(self):
        super().__init__(BasicClass, supported_methods=["GET"], read_db="readreplica")


class SecondDatabaseBasicClassHandler(SimplifyView):
    def __init__(self):
        super().__init__(
            BasicClass,
            supported_methods=["GET", "POST", "POST_SUB"],
            write_db="readreplica",
            read_db="readreplica",
        )


class SqlStoredProcedureHandler(SimplifyStoredProcedureView):
    def __init__(self, *args, **kwargs):
        # add items to kwargs
        kwargs["forms"] = forms
        kwargs["engine"] = "sqlserver"
        super().__init__(*args, **kwargs)


class PostgresStoredProcedureHandler(SimplifyStoredProcedureView):
    def __init__(self, *args, **kwargs):
        # add items to kwargs
        kwargs["forms"] = forms
        kwargs["engine"] = "postgres"
        super().__init__(*args, **kwargs)


class SendEmailHandler(SimplifyEmailTemplateView):
    def __init__(self, *args, **kwargs):
        # add items to kwargs
        kwargs["templates"] = email_templates
        super().__init__(*args, **kwargs)


class OneToOneHandler(SimplifyView):
    def __init__(self):
        super().__init__(OneToOneClass, supported_methods=["GET"])


class RequestFieldSaveHandler(SimplifyView):
    def __init__(self):
        super().__init__(RequestFieldSaveClass, supported_methods=["POST"])


class PhaseGroupHandler(SimplifyView):
    def __init__(self):
        super().__init__(PhaseGroup, supported_methods=["GET", "GET_LIST"])


class ModelWithParentResourceHandler(SimplifyView):
    def __init__(self):
        linked_objects = []
        model_with_parent_resource = {
            "parent_resource": "basicClasses",
            "parent_cls": BasicClass,
            "parent_name": "basic_class",
            "linking_cls": None,
            "sub_resource_name": None,
            "lives_on_parent": False,
        }
        linked_objects.append(model_with_parent_resource)
        super().__init__(
            ModelWithParentResource,
            supported_methods=["GET_SUB"],
            linked_objects=linked_objects,
        )
