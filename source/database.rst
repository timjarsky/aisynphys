.. _database_access:

Database Access
===============

- We use sqlalchemy to handle database access
- Tested with postgres and sqlite
- Link to DB schema info
- Short description of DB classes
- Example queries

.. automodule:: multipatch_analysis.database.SynphysDatabase
    :members:
    :show-inheritance:

.. automodule:: multipatch_analysis.database.Database
    :members:
    :show-inheritance:

===============
Database Schema
===============

The Synaptic Physiology Dataset is organized in a Postgres Database and we use SQLAlchemy to interact with the database in Python.
The database is a relational one and it is important to understand what the relationships are in the database so that you can navigate to your data of interest. The full database schema can be found `here <>`_ but we'll point out some important relationships when getting started. Relationships can be 1-to-1 or 1-to-many. The database heirarchy somewhat follows that of the experiment and analyses.

* The **slice** table is the top-most table in the database and thus contains much of the metadata one might be interested in, such as species, age, etc. 
* Multiple entries in the **experiment** table can relate to a single *slice*.
* The **pair** table is another important one and sits in the middle of the schema. This table will likely be your point of entry for any analyses as it is for many of the ones we provide.
    
    * A *pair* entry contains a relation to the pre- and postsynaptic cell and whether there is a synapse, among other attributes
    * The pair table also links directly to several tables that contain data such as **synapse**, **resting_state_fit**, and **dynamics**.

=====================
Querying the Database
=====================

The `SQLAlchemy query API <https://docs.sqlalchemy.org/en/13/orm/query.html>`_ is an excellent resource for writing queries in Python.

**Database Class**

The Database Class is a relational database with sqlalchemy interaction. This class has methods for managing a database and interacting with a database, for instance making or droping tables, querying, and session handling. The Database Class is merely a scaffold, the schema for the database is implemented outside of this class

**SynphysDatabase Class**

The SynphysDatabase Class is a subclass of Database and includes helper methods for interacting with the Synpatic Physiology data specifically. We'll go through a couple of these methods here:

*pair_query()*

This method allows you to query the SynphysDatabase for cell pairs and specify a variety of filtering criteria. It handles all of the relevant joins across the tables of the database and returns a query object. For example, if you were interested in knowing how many excitatory synapses exist in the mouse your pair_query would look like::

    pair_query(synapse_type='ex', species='mouse')

