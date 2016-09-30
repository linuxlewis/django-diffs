Django Diffs
------------

.. image:: https://travis-ci.org/linuxlewis/django-diffs.svg?branch=master
    :target: https://travis-ci.org/linuxlewis/django-diffs


Django diffs allows models to be registered to track it's changes (or diffs) over time.
It adds a manager to registered model to easily access it's changes

It's compatible with Python 2/3 and Django 1.8 and above. It requires a postgresql database.


Table of Contents
-----------------

- `Getting Started <#getting-started>`__
- `Custom Serialization <#custom-serialization>`__
- `Tracking related models <#related-models>`__


How does it Work?
-----------------

It allows models to be registered similar to ``ModelAdmin``. When the model is saved the diff is serialized and stored.
It relies on django-dirtyfields to track the changes on models. Changes can be accessed via the ``diffs`` manager on the registered model.

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

    diffs = Question.diffs.get_diffs(question.id).all()

    for diff in diffs:
        print(diff.diff)

Why?
----

You need to track the changes over time to a single or collection of related django models.


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

- Run Migrations

.. code:: bash

    python manage.py migrate

- Register a Model

.. code:: python

    # models.py

    import diffs

    @diffs.register
    class Question(models.Model):
        question_text = models.CharField(max_length=200)
        pub_date = models.DateTimeField('date published')

That's it! Changes will now be tracked automatically for this model.


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

Django-diffs allows you to set a parent objects by implementing ``get_parent_object`` on
the child model. It must return a model instance with an id defined.

To access all the changes on the parent or child objects use the diffs manager ``get_all_diffs`` method.


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
    Question.diffs.get_all_diffs(question.id).count() # 3
