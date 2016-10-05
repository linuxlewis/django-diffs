Django Diffs
------------

.. image:: https://travis-ci.org/linuxlewis/django-diffs.svg?branch=master
    :target: https://travis-ci.org/linuxlewis/django-diffs


Django diffs allows models to be registered to cache it's changes (or diffs) over a fixed time period.

The diffs are stored in redis using a SortedSet and accessed via a manager-like object on the registered django model class.

It's compatible with Python 2/3 and Django 1.8 and above. It requires an available redis server.


Table of Contents
-----------------

- `Getting Started <#getting-started>`__
- `Configuration <#configuration>`__
- `Custom Serialization <#custom-serialization>`__
- `Related models <#related-models>`__


How does it Work?
-----------------

Models are registered with the ``@diffs.register`` decorator and their changes are serialized and saved to redis on signals.
The decorator installs django-dirtyfields to the model on registration to get the changed fields of the model instance.

Changes can be accessed via the ``diffs`` manager on the registered model. The diffs manager returns a list of ``Diff``
objects that have properties of ``data``, ``created``, and ``timestamp``.

Here's a quick example.

.. code:: python

    # models.py

    import diffs

    @diffs.register
    class Question(models.Model):
        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')

    question = Question.objects.create(question_text='What is life?')

    question.question_text = 'What is python?'
    question.save()

    diffs = Question.diffs.get_diffs(question.id)

    for diff in diffs:
        print(diff.timestamp)
        print(diff.data)
        print(diff.created)

Why?
----

You need to cache the changes to a single django model or collection of models for a fixed time period.

Tracking the changes prevents clients from having to re-request all of the model data which is assumed to be costly.



Getting Started
---------------


- Add ``django-diffs`` to ``requirements.txt``

.. code:: bash

    pip install django-diffs

- Add ``diffs`` to ``INSTALLED_APPS``

.. code:: python

    INSTALLED_APPS = (
        'diffs',
    )

- Register a Model

.. code:: python

    # models.py

    import diffs

    @diffs.register
    class Question(models.Model):
        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')

That's it! Changes will now be tracked automatically for this model.

Configuration
-------------

Django-diffs can be configured via ``django.conf.settings``. Below is the default configuration

.. code:: python

    # settings.py

    DIFFS_SETTINGS = {
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
        },
        'max_element_age': 60*60
    }


Custom Serialization
--------------------

By default django-diffs uses ``django.core.serializers`` module to serialize the diff to json.

To use your own custom serialization format just implement the ``serialize_diff`` method
on your model. It will be passed the list of ``dirty_fields``.

.. code:: python

    # models.py

    import diffs

    @diffs.register
    class Question(models.Model):
        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')

        def serialize_diff(self, dirty_fields):
            return {'fields': dirty_fields}

    question = Question.objects.create(question_text='What will happen?')

    Question.diffs.get_diffs(question.id).last().diff
    # {'fields': ['question_name']}


Related models
--------------

Sometimes you want to track changes on a collection of related models.
These could be individual items part of a larger Report object.

Django-diffs allows you to set a parent objects by implementing ``get_diff_parent`` on
the child model. It must return a model instance with an id defined.



.. code:: python

    # models.py

    import diffs

    @diffs.register
    class Question(models.Model):
        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')


    @diffs.register
    class Choice(models.Model):
        question = models.ForeignKey(Question, on_delete=models.CASCADE)
        choice_text = models.CharField(max_length=200)
        votes = models.IntegerField(default=0)

        def get_parent_object(self):
            # save the db lookup
            return Question(id=self.question_id)


    question = Question.objects.create(question_text='What will happen?')
    choice = Choice.objects.create(choice_text='Nothing', question=question)

    choice.choice_text = 'Something'
    choice.save()

    # returns diffs for question and it's choices
    len(Question.diffs.get_diffs(question.id)) # 3
