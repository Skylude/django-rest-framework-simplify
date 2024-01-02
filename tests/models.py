from django.db import models
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

from rest_framework_simplify.models import SimplifyModel
from rest_framework_simplify.fields import (
    SimplifyEncryptedCharField,
    SimplifyJsonTextField,
)


class BasicClass(SimplifyModel):
    CACHE = True
    CACHE_TIME = 15

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)
    active = models.BooleanField(null=False, default=True)
    created = models.DateTimeField(null=False, default=timezone.now)
    binary_field = models.BinaryField(
        null=True, blank=True, default=bytes("binarystring", "utf-8")
    )
    child_one = models.OneToOneField(
        "ChildClass",
        null=True,
        blank=True,
        related_name="basic_class_one",
        on_delete=models.CASCADE,
    )
    child_two = models.OneToOneField(
        "ChildClass",
        null=True,
        blank=True,
        related_name="basic_class_two",
        on_delete=models.CASCADE,
    )
    exclude_field = models.CharField(max_length=25, null=True, blank=True)
    child_three = models.ManyToManyField(
        "ChildClass", null=True, blank=True, related_name="basic_class_three"
    )
    model_with_sensitive_data = models.OneToOneField(
        "ModelWithSensitiveData", null=True, blank=True, on_delete=models.CASCADE
    )

    change_tracking_fields = ["name", "child_one"]

    @property
    def test_prop(self):
        return True

    @staticmethod
    def get_filters():
        return {
            "active": {
                "type": bool,
                "list": False,
            },
            "test_prop": {
                "type": bool,
                "list": False,
                "property": True,
            },
            "child_three__id__contains_all": {
                "type": int,
                "list": True,
            },
            "name__icontains": {
                "type": str,
                "list": False,
            },
            "name__revicontains": {
                "type": str,
                "list": False,
            },
        }

    @staticmethod
    def get_includes():
        return [
            "child_one__name",
            "child_three",
            "model_with_sensitive_data",
            "child_one",
            "child_one__nested_child",
        ]

    @staticmethod
    def get_excludes():
        return ["exclude_field"]


class ChildClass(SimplifyModel):
    CACHE = True

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=15)


class NestedChild(SimplifyModel):
    id = models.AutoField(primary_key=True)
    child_one = models.OneToOneField(
        "ChildClass",
        null=True,
        blank=True,
        related_name="nested_child",
        on_delete=models.CASCADE,
    )


class LinkingClass(SimplifyModel):
    id = models.AutoField(primary_key=True)
    basic_class = models.ForeignKey(
        "BasicClass",
        null=False,
        related_name="linking_classes",
        on_delete=models.CASCADE,
    )
    child_class = models.ForeignKey(
        "ChildClass",
        null=False,
        related_name="linking_classes",
        on_delete=models.CASCADE,
    )


class MetaDataClass(SimplifyModel):
    CHOICE_1 = "one"
    CHOICE_2 = "two"
    CHOICE_3 = "three"
    CHOICES = (
        (CHOICE_1, "One"),
        (CHOICE_2, "Two"),
        (CHOICE_3, "Three"),
    )
    id = models.AutoField(primary_key=True)
    choice = models.CharField(max_length=32, choices=CHOICES, default=CHOICE_2)


class EncryptedClass(SimplifyModel):
    id = models.AutoField(primary_key=True)
    encrypted_val = SimplifyEncryptedCharField(max_length=256, display_chars=-4)


class EncryptedClassNoDisplayChars(SimplifyModel):
    id = models.AutoField(primary_key=True)
    encrypted_val = SimplifyEncryptedCharField()


class JsonTextFieldClass(SimplifyModel):
    id = models.AutoField(primary_key=True)
    json_text = SimplifyJsonTextField(null=True, blank=True)


class OneToOneClass(SimplifyModel):
    alternative_id = models.IntegerField(primary_key=True)


class RequestFieldSaveClass(SimplifyModel):
    REQUEST_FIELDS_TO_SAVE = [("method", "method")]

    id = models.AutoField(primary_key=True)
    method = models.CharField(max_length=32, null=False, blank=False)


class Community(SimplifyModel):
    id = models.AutoField(primary_key=True)
    phase_group = models.ForeignKey(
        "PhaseGroup",
        null=False,
        blank=False,
        related_name="communities",
        on_delete=models.CASCADE,
    )


class Application(SimplifyModel):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=32)

    @staticmethod
    def get_lead_mgmt_application():
        try:
            application = Application.objects.get(name="Lead Mgmt")
        except ObjectDoesNotExist:
            application = Application(name="Lead Mgmt")
            application.save()
        return application


class PhaseGroup(SimplifyModel):
    id = models.AutoField(primary_key=True)

    @property
    def active(self):
        some_id = Application.get_lead_mgmt_application().id
        return bool(
            self.communities.community_applications.filter(
                application_id=some_id, active=True
            )
        )

    @staticmethod
    def get_filterable_properties():
        return {
            "active": {
                "query": models.Case(
                    models.When(
                        models.Q(
                            communities__community_applications__application_id=Application.get_lead_mgmt_application().id,
                            communities__community_applications__active=True,
                        ),
                        then=models.Value(True),
                    ),
                    default=models.Value(False),
                    output_field=models.BooleanField(),
                ),
            },
        }

    @staticmethod
    def get_filters():
        return {
            "active": {
                "type": bool,
                "list": False,
            },
            "id__in": {
                "type": int,
                "list": True,
            },
        }


class CommunityApplication(SimplifyModel):
    id = models.AutoField(primary_key=True)
    community = models.ForeignKey(
        "Community",
        null=False,
        blank=False,
        related_name="community_applications",
        on_delete=models.CASCADE,
    )
    application = models.ForeignKey(
        "Application",
        null=False,
        blank=False,
        related_name="community_applications",
        on_delete=models.CASCADE,
    )
    active = models.BooleanField(null=False, default=True)


class ModelWithSensitiveData(SimplifyModel):
    id = models.AutoField(primary_key=True)
    basic_text = models.CharField(max_length=32, null=True, blank=True)
    top_secret = models.CharField(max_length=32, null=True, blank=True)

    @staticmethod
    def get_excludes():
        return ["top_secret"]


class ModelWithParentResource(SimplifyModel):
    id = models.AutoField(primary_key=True)
    text_field = models.CharField(max_length=32, null=True, blank=True)
    basic_class = models.ForeignKey(
        "BasicClass", null=False, blank=False, on_delete=models.CASCADE
    )
