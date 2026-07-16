# Testimonial - Kolkata Metro Assessment

## My Approach
I started by reading through the repo structure end to end before touching any code -
README, INSTRUCTIONS.md, and the database schema doc (sqlite_ddl_description.md) first,
then the backend (FastAPI routes, services, db clients) and finally the frontend components.
Once I understood how the pieces connected, I got the project running locally, fixed the
Stage 1 setup issue, then moved on to implementing the missing features.

## Understanding the Project
The project is a dual-database system: SQLite stores the static metro graph (stations,
connections, interchanges) used for route-finding, while PostgreSQL handles transactional
data (ticket bookings, system config, worker heartbeat). All API routes are registered
under an /api prefix in main.py. Stations are modeled per-line, so interchange stations
(e.g. Esplanade on multiple lines) exist as separate rows connected via the interchanges
table - this was key to getting the routing logic right.

## Bugs Encountered During Setup
Running `pip install -r requirements.txt` failed with
`ModuleNotFoundError: No module named 'sqlalchemy'`. The backend code (postgres_client.py)
imports SQLAlchemy directly to define the ORM models, but it wasn't listed as a dependency
in requirements.txt.

## How I Resolved Them
Added `sqlalchemy>=2.0.0` to requirements.txt and reinstalled dependencies in a clean venv
to confirm the fix - the app now installs and starts cleanly with no missing-module errors.

## Feature Implementation Notes
- Feature 1: Integrated the existing `/api/allstations` endpoint into the frontend station
  dropdown, with loading and error states while stations are fetched.
- Feature 2: Implemented Dijkstra's algorithm in graph_engine.py to compute the shortest
  path over the combined graph of `connections` (train edges) and `interchanges` (transfer
  edges), handling the fact that a station name can map to multiple line-specific rows.
  Kept the existing `/api/route?source=&destination=` contract unchanged and matched the
  response shape (`route_summary` + `ordered_itinerary`) that the frontend already expected.

## Challenges Faced
The main challenge was matching the exact response contract the frontend (RouteSelector.jsx)
expected without being able to change the endpoint signature - this meant designing the
internal path-building logic (tracking interchange flags per edge) so the final response
could cleanly map to `is_interchange` / `transfer_to` fields per station in the itinerary.

## Assumptions Made
- Station names are matched case-insensitively when looking up source/destination.
- When a station name resolves to multiple line-specific IDs (interchange stations),
  the algorithm considers all of them as valid start/end candidates and returns whichever
  produces the lowest-cost path.
- Ties in Dijkstra's priority queue are broken arbitrarily by heap order, since the schema
  doesn't define a tie-breaking priority.

## Improvements With More Time
- Cache the graph in memory instead of rebuilding it from SQLite on every /route request.
- Add unit tests for the routing logic, especially around interchange stations and
  disconnected/invalid station names.
- Add a fare-optimized route option alongside the current fastest-route calculation.
- Clean up a few minor inconsistencies (indentation in routes.py, some invalid Tailwind
  utility classes in the frontend) found during a final pass.