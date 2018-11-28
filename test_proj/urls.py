from django.conf.urls import url

from test_app.views import BasicClassHandler, ChildClassHandler, LinkingClassHandler, \
    LinkingClassWithNoLinkingClsDefinedHandler, MetaDataClassHandler, ReadReplicaBasicClassHandler, \
    SqlStoredProcedureHandler, PostgresStoredProcedureHandler, SecondDatabaseBasicClassHandler, SendEmailHandler, \
    OneToOneHandler, RequestFieldSaveHandler, PhaseGroupHandler, ModelWithParentResourceHandler

urlpatterns = [
    url(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/childOne$', ChildClassHandler.as_view()),
    url(r'^(?P<parent_resource>[a-zA-Z]+)/(?P<parent_pk>[0-9]+)/childClassNoLinker$',
        LinkingClassWithNoLinkingClsDefinedHandler.as_view()),
    url(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/childClass/(?P<pk>[0-9]+)$',
        LinkingClassHandler.as_view()),
    url(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/childClass$', LinkingClassHandler.as_view()),
    url(r'^(?P<parent_resource>[a-zA-z]+)/(?P<parent_pk>[0-9]+)/modelWithParentResources/(?P<pk>[0-9]+)$',
        ModelWithParentResourceHandler.as_view()),
    url(r'^basicClass/(?P<pk>[0-9]+)$', BasicClassHandler.as_view()),
    url(r'^basicClass', BasicClassHandler.as_view()),
    url(r'^metaDataClass', MetaDataClassHandler.as_view()),
    url(r'^oneToOne/(?P<pk>[0-9]+)$', OneToOneHandler.as_view()),
    url(r'^readReplicaBasicClass/(?P<pk>[0-9]+)$', ReadReplicaBasicClassHandler.as_view()),
    url(r'^requestFieldsToSaveClass$', RequestFieldSaveHandler.as_view()),
    url(r'^secondDatabaseBasicClass$', SecondDatabaseBasicClassHandler.as_view()),
    url(r'^sendEmail$', SendEmailHandler.as_view()),
    url(r'^sqlStoredProcedures$', SqlStoredProcedureHandler.as_view()),
    url(r'^postgresStoredProcedures$', PostgresStoredProcedureHandler.as_view()),
    url(r'^phaseGroups$', PhaseGroupHandler.as_view())
]
