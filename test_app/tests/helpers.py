import uuid

from random import randint

from test_app.models import *


class DataGenerator:
    @staticmethod
    def set_up_basic_class(name=None, child_one=None, child_two=None, active=True, write_db='default', child_three_count=2):
        if not name:
            name = str(uuid.uuid4())[:15]

        basic_class = BasicClass(name=name, child_one=child_one, child_two=child_two, active=active)

        basic_class.save(using=write_db)
        for x in range(0, child_three_count):
            basic_class.child_three.add(DataGenerator.set_up_child_class(write_db=write_db))
            basic_class.save(using=write_db)
        return basic_class

    @staticmethod
    def set_up_child_class(name=None, write_db='default'):
        if not name:
            name = str(uuid.uuid4())[:15]

        child_class = ChildClass(name=name)
        child_class.save(using=write_db)
        return child_class

    @staticmethod
    def set_up_encrypted_class(value=None):
        if not value:
            value = str(uuid.uuid4())[:9]

        encrypted_class = EncryptedClass(encrypted_val=value)
        encrypted_class.save()
        return encrypted_class

    @staticmethod
    def set_up_linking_class(basic_class=None, child_class=None):
        if not basic_class:
            basic_class = DataGenerator.set_up_basic_class()
        if not child_class:
            child_class = DataGenerator.set_up_child_class()
        linking_class = LinkingClass(basic_class=basic_class, child_class=child_class)
        linking_class.save()
        return linking_class

    @staticmethod
    def set_up_meta_data_class():
        rand_choice = randint(0, len(MetaDataClass.CHOICES) - 1)
        meta_data_class = MetaDataClass(choice=MetaDataClass.CHOICES[rand_choice][0])
        meta_data_class.save()
        return meta_data_class

    @staticmethod
    def set_up_ont_to_one_class():
        oto = OneToOneClass(alternative_id=1)
        oto.save()
        return oto

    @staticmethod
    def set_up_community(phase_group=None):
        if not phase_group:
            phase_group = DataGenerator.set_up_phase_group()
            phase_group.save()
        community = Community(phase_group=phase_group)
        community.save()
        return community

    @staticmethod
    def set_up_phase_group():
        phase_group = PhaseGroup()
        phase_group.save()
        return phase_group

    @staticmethod
    def set_up_community_application(community=None, application=None, active=True):
        if not community:
            community = DataGenerator.set_up_community()
            community.save()
        if not application:
            application = DataGenerator.set_up_application()
            application.save()
        community_application = CommunityApplication(community=community, application=application, active=active)
        community_application.save()
        return community_application


    @staticmethod
    def set_up_application():
        application = Application()
        application.save()
        return application
