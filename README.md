*This project has been created as part of the 42 curriculum by <vlourenc>.*

# Fly-in

An autonomous multi-agent drone routing simulator in discrete time that navigates a fleet of drones from a starting hub to an end hub while minimizing total simulation turns and strictly satisfying dynamic spatial and capacity constraints.

---

## Description

The objective of **Fly-in** is to orchestrate collision-free trajectories for multiple drones through a connected network of aerial zones. The simulation operates in discrete turns where drones can move simultaneously across links, provided all node and edge capacities are respected at all times.

### Core Simulation Mechanics:
- **Node Capacities (`max_drones`):** Limits how many drones can simultaneously occupy a zone during any given turn (default: 1; hubs have infinite capacity).
- **Link Capacities (`max_link_capacity`):** Limits concurrent crossings between two connected zones (default: 1).
- **Heterogeneous Zone Types:**
  - `normal`: Standard zone requiring 1 simulation turn.
  - `restricted`: High-risk zone requiring 2 turns (the drone occupies the connection link during transit).
  - `priority`: Preferred zone requiring 1 turn, favored during path exploration.
  - `blocked`: Inaccessible obstacles pruned during graph ingestion.
- **Simultaneous Flow & Pipelining:** Drones departing a zone immediately free capacity for incoming drones on that exact same turn ("train movement").

---

## Instructions

### Prerequisites
- Python 3.10 or later
- `uv` package manager (or standard `pip` / `python3 -m venv`)

### Installation & Virtual Environment
Install development dependencies and configure the isolated environment:
	
	make install


## Execution
Run the simulation by providing a map configuration file:

### Standard output (step-by-step turns)

python main.py maps/easy/01_linear_path.txt

### Or via Makefile

make run MAP=maps/easy/01_linear_path.txt

### Optional Flags
Interactive Visual Feedback:
	
	python main.py maps/medium/03_priority_puzzle.txt --visual

Real-Time Capacity Monitoring (Live Coding flag):
	
	python main.py maps/hard/02_capacity_hell.txt --capacity-info

Code Quality & Static TypingRun strict PEP 8 and static typing checks:
	
	make lint
	make lint-strict

Unit Tests: Run the comprehensive unit test suite:
	
	pytest tests/ -v

## Algorithm Explanation
### Approach: Prioritized Planning with Space-Time A*
Traditional static graph algorithms (e.g., Edmonds-Karp, Suurballe, or standard Dijkstra) fail when multi-turn restricted zones, edge locking, and deliberate waiting actions are introduced.
Fly-in models the aerial space as a 3D Space-Time Graph $(V \times T)$ where each node state is defined by (zone, turn). Pathfinding is performed via Prioritized Planning:
	
	Admissible Reverse Heuristic: A reverse Dijkstra search starts from end_hub across accessible zones to compute the exact minimum transit cost $h(u)$ from any zone $u$ to the destination.

	Space-Time A Search:* For each drone $D_i$, an $A^*$ search navigates through the space-time grid:

		Transition 1 (Normal/Priority): Moves to adjacent zone in turn $t+1$ if both link and destination node have capacity.

		Transition 2 (Restricted): Takes 2 turns ($t+2$), locking the connection edge in turn $t+1$ and occupying the target zone at $t+2$.

		Transition 3 (Strategic Wait): Stays at the current zone in turn $t+1$ if capacity permits, allowing bottlenecks to clear.

		Tie-Breaking: Paths with equal arrival turns prioritize paths containing priority zones.
	
	Reservation Table Commit: Once the optimal schedule for drone $D_i$ is determined, its booked nodes and edges are committed to an atomic ReservationTable, acting as dynamic obstacles for subsequent drones ($D_{i+1}, \dots$).
	

### Complexity Analysis
Time Complexity: For $D$ drones, $V$ zones, $E$ connections, and time horizon $T$, the overall fleet search complexity is $O(D \cdot (V + E) \cdot T \log(V \cdot T))$.

Space Complexity: $O(V + E + D \cdot T)$ to retain the adjacency lists and time-indexed reservation dictionaries.

## Visual Representation
The terminal visualizer leverages native ANSI escape sequences without third-party dependencies:
	Drones are highlighted in bold cyan (D1, D2).
	Zones are dynamically styled matching their metadata [color=<value>] tag (e.g., red, green, yellow, blue).
	Drones in transit across 2-turn restricted connections are highlighted in magenta.
	The dashboard displays a summary of fleet size, topology stats, and total simulation turn counts.

### Example Input and Expected Output 
#### Input Map (example.txt)
nb_drones: 2

start_hub: start 0 0 [color=green]

end_hub: goal 10 10 [color=yellow]

hub: mid 5 5 [zone=normal color=blue max_drones=1]

connection: start-mid

connection: mid-goal

#### Expected Output
D1-mid

D1-goal D2-mid

D2-goal

## Resources
Multi-Agent Pathfinding (MAPF): Stern, R. et al., Multi-Agent Pathfinding: Definitions, Variants, and Benchmarks (2019).Space-Time Reservation Models: Silver, D., Cooperative Pathfinding (AIIDE 2005).Python Typing Standard: PEP 484 and PEP 526 guidelines for strict type annotations.

### AI Usage Declaration
AI was utilized as an interactive pair-programming assistant to:
	Structure the test cases for edge-case coverage in tests/test_parser.py. (all pytest done by AI pretty much)
	Structure the scripts/benchmark.py file. Completely made by Gemini, designed to help the evaluator understand some of the mechanics
	Make this README file with some changes from myself on the main stuff.
