.. _api_schema:

Database Schema
===============

- can be accessed using any standard sqlite library
- we also provide (and prefer) an sqlalchemy model that provides a richer interface for interacting with the db
- the api reference below describes sqlalchemy model classes, but also doubles as a description of the relational database schema

.. autoclass:: aisynphys.database.database.slice
   :members:
   :inherited-members:
   :private-members:
   :special-members:

.. autoclass:: aisynphys.database.schema.Experiment
   :members:
   :inherited-members:
   :private-members:
   :special-members:



