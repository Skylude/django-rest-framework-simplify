from django.urls import re_path

from test_app.views import BasicClassHandler, ChildClassHandler, LinkingClassHandler, \
    LinkingClassWithNoLinkingClsDefinedHandler, MetaDataClassHandler, ReadReplicaBasicClassHandler, \
    SqlStoredProcedureHandler, PostgresStoredProcedureHandler, SecondDatabaseBasicClassHandler, SendEmailHandler, \
    OneToOneHandler, RequestFieldSaveHandler, PhaseGroupHandler, ModelWithParentResourceHandler

urlpatterns = [
    re_path(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/childOne$', ChildClassHandler.as_view()),
    re_path(r'^(?P<parent_resource>[a-zA-Z]+)/(?P<parent_pk>[0-9]+)/childClassNoLinker$',
        LinkingClassWithNoLinkingClsDefinedHandler.as_view()),
    re_path(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/childClass/(?P<pk>[0-9]+)$',
        LinkingClassHandler.as_view()),
    re_path(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/childClass$', LinkingClassHandler.as_view()),
    re_path(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/modelWithParentResources/(?P<pk>[0-9]+)$',
        ModelWithParentResourceHandler.as_view()),
    re_path(r'^basicClass/(?P<pk>[0-9]+)$', BasicClassHandler.as_view()),
    re_path(r'^basicClass', BasicClassHandler.as_view()),
    re_path(r'^metaDataClass', MetaDataClassHandler.as_view()),
    re_path(r'^oneToOne/(?P<pk>[0-9]+)$', OneToOneHandler.as_view()),
    re_path(r'^readReplicaBasicClass/(?P<pk>[0-9]+)$', ReadReplicaBasicClassHandler.as_view()),
    re_path(r'^requestFieldsToSaveClass$', RequestFieldSaveHandler.as_view()),
    re_path(r'^secondDatabaseBasicClass$', SecondDatabaseBasicClassHandler.as_view()),
    re_path(r'^sendEmail$', SendEmailHandler.as_view()),
    re_path(r'^sqlStoredProcedures$', SqlStoredProcedureHandler.as_view()),
    re_path(r'^postgresStoredProcedures$', PostgresStoredProcedureHandler.as_view()),
    re_path(r'^phaseGroups$', PhaseGroupHandler.as_view())
]
