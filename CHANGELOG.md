### 12/18/2018 1.3.0
Added force_refresh_on_save to SimplifyModel so if you are doing any logic in a post_save that needs to be refreshed before serialization you can set this to True on the model

### 9/14/2018 1.2.5
psycopg2 updated to version 2.7.3 so verify compatability

### 8/16/2018 1.2.2
Added exclude functionality on included items to ensure they are never included by accident

### 5/15/2018 1.2.0
Added get_filterable_properties to the SimplifyModel which will allow you to filter based on a property that is on the model. Currently this is restricted to predefined values and cannot accept arguments to the filter at this time. Look at the PhaseGroup model and URL for examples.

### 5/6/2018 - 1.1.7
Added REQUEST_FIELDS_TO_SAVE to the SimplifyModel which will allow us to save fields from the request object directly to the SimplifyModel. This is a property that is set on the SimplifyModel and it is a list of tuples. For example if you wanted to save the "method" from the request onto a SimplyModel field of "verb" you would simply add the attribute REQUEST_FIELDS_TO_SAVE = [('method', 'verb')]
