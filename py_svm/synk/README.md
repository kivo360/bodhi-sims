# 10 Ways to Develop the simulation database quickly

1. Start with the interface for the queries
2. Make sure the interface is what you need.
3. Copy the interface from the Jamboree library.
4. Create a `processor` interface that will be used for pulling information from the database.
5. Fill in a `processor` interface with `dataset`.
6. Create a new `processor` with meilisearch.
7. Use dataframe as an example.
8. Completely write out design docs for the database.
9. Use SurrealDB instead of Meilisearch
   * It's a document/graph/SQL database that easily trumps EdgeDB AND Meilisearch combined.
   * It has search functionality.
10. Start with single core, single computer model.

* Expand to a full cluster using [Hazelcast](https://hazelcast.readthedocs.io/en/stable/api/proxy/cp/atomic_reference.html), TIKV, and Memgraph.
  * Expand using a server (FastAPI for starters)

11. Build on top of [`Hash.ai`](https://hash.ai/blog/what-is-agent-based-modeling) to reach full functionality.

* Seriously though, you should do that. There are several caveats to that approach, though after the first version or so you should be able to create a wrapper around their software.

1.  Use cosmic mind stuff to get it working to nail the networking.
13.Utilize Python to other language codegen (to write lower-level languages faster).
