# Data Model

I need to deeply consider the data model for the environment system. There are circumstances where the data model will need multiple of a given class of data (such as pricable information), as well as the history of that information. Grabbing a single piece of data is okay, but when you have multiple of a given class the number of accesses to that class can explode exponentially. 


Need latest information for each group sorted by instrument, and ordered by timestamp. I could try thinking about how to do this using pandas first, then try out a few different queries.


**NOTE: Going to ignore database interactions for a bit. Truthfully, it gets in the way of creating the simulation software iteratively.**