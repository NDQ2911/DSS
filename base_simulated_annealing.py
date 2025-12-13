import random
import math
import itertools

# --- Configuration & Weights ---
WEIGHTS = {
    'sleep': 2.0,      # High priority: Mismatched sleep schedules cause the most fights
    'cleanliness': 1.5,
    'noise': 1.0,
    'temp': 0.8,
    'guests': 1.0
}

NUM_STUDENTS = 2500

# Fixed Inventory of Rooms
# 30 rooms of 10, 20 rooms of 8, 20 rooms of 6
ROOM_INVENTORY_CONFIG = {
    10: 100,
    8: 110,
    6: 110
}

class Student:
    def __init__(self, id, gender, smoker, traits):
        self.id = id
        self.gender = gender    # 'M' or 'F'
        self.smoker = smoker    # True or False
        self.traits = traits    # Dictionary of scores 1-5

    def __repr__(self):
        return f"S{self.id}"

def generate_mock_students(count):
    students = []
    for i in range(count):
        traits = {
            'sleep': random.randint(1, 5),
            'cleanliness': random.randint(1, 5),
            'noise': random.randint(1, 5),
            'temp': random.randint(1, 5),
            'guests': random.randint(1, 5)
        }
        gender = random.choice(['M', 'F'])
        smoker = random.choice([True, False])
        students.append(Student(i, gender, smoker, traits))
    return students

def calculate_pair_friction(student_a, student_b):
    sum_sq_diff = 0
    for trait, weight in WEIGHTS.items():
        diff = student_a.traits[trait] - student_b.traits[trait]
        sum_sq_diff += weight * (diff ** 2)
    return math.sqrt(sum_sq_diff)

def calculate_room_friction(room):
    if len(room) < 2:
        return 0

    total_room_friction = 0
    pair_count = 0
    for s1, s2 in itertools.combinations(room, 2):
        total_room_friction += calculate_pair_friction(s1, s2)
        pair_count += 1

    return total_room_friction / pair_count if pair_count > 0 else 0

def calculate_total_friction(rooms):
    total_score = 0
    for room in rooms:
        total_score += calculate_room_friction(room)
    return total_score

def optimize_group(rooms, iterations=5000):
    """
    Optimizes room assignments using Simulated Annealing.
    Allows temporary 'bad' moves to escape local optima.
    """
    active_rooms = [r for r in rooms if len(r) > 0]

    if len(active_rooms) < 2:
        return rooms

    # --- Simulated Annealing Parameters ---
    temperature = 100.0   # Initial 'heat' - willingness to accept bad moves
    cooling_rate = 0.995  # How fast the system cools down per iteration
    min_temperature = 0.01 # Stop cooling when we hit this bottom

    current_friction_total = calculate_total_friction(active_rooms)

    for i in range(iterations):
        # 1. Pick two random rooms
        r_idx1, r_idx2 = random.sample(range(len(active_rooms)), 2)
        room1 = active_rooms[r_idx1]
        room2 = active_rooms[r_idx2]

        # 2. Pick one random student from each room
        s_idx1 = random.randint(0, len(room1) - 1)
        s_idx2 = random.randint(0, len(room2) - 1)

        # Calculate friction ONLY for the two affected rooms (optimization speedup)
        # We don't need to recalculate the entire building's score
        old_local_friction = calculate_room_friction(room1) + calculate_room_friction(room2)

        # 3. Create tentative new rooms (Simulate Swap)
        new_room1 = room1[:]
        new_room2 = room2[:]

        student1 = new_room1[s_idx1]
        student2 = new_room2[s_idx2]
        new_room1[s_idx1] = student2
        new_room2[s_idx2] = student1

        new_local_friction = calculate_room_friction(new_room1) + calculate_room_friction(new_room2)

        # 4. Calculate Delta (Change in friction)
        # Negative delta means improvement (friction went down)
        # Positive delta means worsening (friction went up)
        delta = new_local_friction - old_local_friction

        accept_swap = False

        if delta < 0:
            # Improvement: Always accept
            accept_swap = True
        else:
            # Worsening: Accept with probability e^(-delta / temperature)
            # As temperature drops, probability of acceptance drops
            if temperature > min_temperature:
                probability = math.exp(-delta / temperature)
                if random.random() < probability:
                    accept_swap = True

        # 5. Apply Swap if Accepted
        if accept_swap:
            active_rooms[r_idx1][:] = new_room1
            active_rooms[r_idx2][:] = new_room2

        # 6. Cool Down
        if temperature > min_temperature:
            temperature *= cooling_rate

    return active_rooms

def generate_global_room_inventory():
    """Creates a flat list of all available room capacities."""
    inventory = []
    for size, count in ROOM_INVENTORY_CONFIG.items():
        inventory.extend([size] * count)
    # Shuffle so that different student groups get a random mix of room sizes
    random.shuffle(inventory)
    return inventory

def partition_into_rooms(students, room_inventory):
    """
    Pulls room sizes from the global inventory until all students are assigned.
    """
    rooms = []
    current_idx = 0
    total_students = len(students)

    while current_idx < total_students:
        if not room_inventory:
            raise ValueError("Not enough rooms in inventory for all students!")

        # Take the next available room size from the global pile
        room_capacity = room_inventory.pop(0)

        # Determine how many students go in (capacity or however many are left)
        num_to_take = min(room_capacity, total_students - current_idx)

        # Create the room
        chunk = students[current_idx : current_idx + num_to_take]
        rooms.append(chunk)
        current_idx += num_to_take

    return rooms

def assign_rooms(students):
    # --- Step 0: Setup Global Inventory ---
    # We must maintain this list across all groups so we don't double-book rooms
    global_inventory = generate_global_room_inventory()
    total_spots = sum(global_inventory)
    print(f"--- Campus Capacity: {total_spots} spots ({len(global_inventory)} rooms) ---")

    if len(students) > total_spots:
        print(f"WARNING: {len(students)} students but only {total_spots} spots!")

    # --- Step 1: Pre-Filtering (Hard Constraints) ---
    buckets = {}
    for s in students:
        key = (s.gender, s.smoker)
        if key not in buckets:
            buckets[key] = []
        buckets[key].append(s)

    final_assignments = []

    print(f"--- Processing Assignments for {len(students)} Students ---")

    for key, group in buckets.items():
        if not group: continue

        gender_str = "Male" if key[0] == 'M' else "Female"
        smoker_str = "Smoker" if key[1] else "Non-Smoker"
        print(f"\nProcessing Group: {gender_str} / {smoker_str} ({len(group)} students)")

        # Initial Random Assignment using the Global Inventory
        random.shuffle(group)

        # Pass the global inventory so this group consumes specific room slots
        rooms = partition_into_rooms(group, global_inventory)

        initial_score = calculate_total_friction(rooms)

        # --- Step 2: Optimization (Simulated Annealing) ---
        iterations = len(group) * 150 # Increased iterations slightly for better convergence
        optimized_rooms = optimize_group(rooms, iterations=iterations)

        final_score = calculate_total_friction(optimized_rooms)

        print(f"  > Initial Friction: {initial_score:.2f}")
        print(f"  > Optimized Friction: {final_score:.2f}")
        print(f"  > Improvement: {initial_score - final_score:.2f}")

        final_assignments.extend(optimized_rooms)

    return final_assignments

if __name__ == "__main__":
    # 1. Generate Data
    all_students = generate_mock_students(NUM_STUDENTS)

    # 2. Run Algorithm
    assignments = assign_rooms(all_students)

    # 3. Print Results (FULL LIST)
    print("\n\n" + "="*60)
    print(f"--- FULL ROOM ASSIGNMENT REPORT ({len(assignments)} Rooms Filled) ---")
    print("Sorted by Compatibility (Lower Friction = Better Match)")
    print("="*60 + "\n")

    # Sort by lowest friction (best match)
    assignments.sort(key=lambda r: calculate_room_friction(r))

    for i, room in enumerate(assignments, 1):
        friction = calculate_room_friction(room)

        avg_sleep = sum(s.traits['sleep'] for s in room) / len(room)
        avg_clean = sum(s.traits['cleanliness'] for s in room) / len(room)
        avg_noise = sum(s.traits['noise'] for s in room) / len(room)
        avg_temp = sum(s.traits['temp'] for s in room) / len(room)
        avg_guests = sum(s.traits['guests'] for s in room) / len(room)

        print(f"ROOM #{i} [Size: {len(room)}] | Friction Score: {friction:.2f}")
        print(f"  > Group Vibe: Sleep ~{avg_sleep:.1f} | Clean ~{avg_clean:.1f} | Noise ~{avg_noise:.1f} | Temp ~{avg_temp:.1f} | Guests ~{avg_guests:.1f}")
        print("  > Residents:")

        for s in room:
            print(f"    - {s} ({s.gender}/{'S' if s.smoker else 'NS'}): "
                  f"Sleep {s.traits['sleep']}, "
                  f"Clean {s.traits['cleanliness']}, "
                  f"Noise {s.traits['noise']}, "
                  f"Temp {s.traits['temp']}, "
                  f"Guests {s.traits['guests']}"
                 )

        print("-" * 60)