from pathlib import Path
import pandas as pd
import random
import math

'''
Things to add:
- make this a discord bot
    - add custom point values
    - form vs reaction inputs
    - add randomize team orders
    - add reshuffle
    - output who gets excluded
    - be able to remove/add players easily
    - add tutorial
    - add an update system
    - differentiate from players on tierlist vs new


'''

SPLUS = 16
S = 14
APLUS = 10
A = 6
B = 4
C = 2
D = 1

# parse tier list data
file_path = "gg2.csv"
file2 = "test3.txt"

df = pd.read_csv(file_path)
df.dropna(axis=1, how='all', inplace=True)

tierList = [
    "S+",
    "S",
    "A+",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F"
]

tier_dict = {}

for idx, tier in enumerate(tierList):
    if idx < len(df.columns):
        players = df.iloc[:, idx].dropna().astype(str).str.strip().tolist()
        tier_dict[tier] = players

def greedy_balance_with_points(players, num_teams, max_players_per_team):
    total_slots = num_teams * max_players_per_team
    if len(players) > total_slots:
        sorted_by_points = sorted(players.items(), key=lambda x: x[1])
        players = dict(sorted_by_points[-total_slots:])
        print(f"Removed {len(sorted_by_points)-total_slots} lowest-value players")
    
    sorted_players = sorted(players.items(), key=lambda x: -x[1])
    teams = {i: {'players': [], 'points': {}, 'total': 0, 'count': 0} for i in range(num_teams)}
    
    for player, points in sorted_players:
        eligible_teams = [t for t in teams.values() if t['count'] < max_players_per_team]
        if not eligible_teams:
            break
            
        min_team = min(eligible_teams, key=lambda x: x['total'])
        min_team['players'].append(player)
        min_team['points'][player] = points  # Store individual points
        min_team['total'] += points
        min_team['count'] += 1
    
    return teams

def simulated_annealing(players, num_teams, max_players_per_team, iterations=10000):
    # Remove excess players if needed
    total_slots = num_teams * max_players_per_team
    if len(players) > total_slots:
        sorted_by_points = sorted(players.items(), key=lambda x: x[1])
        players = dict(sorted_by_points[-total_slots:])
        print(f"Removed {len(sorted_by_points)-total_slots} lowest-value players")
    
    player_list = list(players.keys())
    
    def create_valid_assignment():
        assignment = {i: {'players': [], 'points': {}} for i in range(num_teams)}
        random.shuffle(player_list)
        for i, player in enumerate(player_list):
            team_idx = i % num_teams
            if len(assignment[team_idx]['players']) < max_players_per_team:
                assignment[team_idx]['players'].append(player)
                assignment[team_idx]['points'][player] = players[player]
        return assignment
    
    current = create_valid_assignment()
    
    def team_score(team):
        return sum(team['points'].values())
    
    def energy(assignment):
        scores = [team_score(team) for team in assignment.values()]
        return max(scores) - min(scores)
    
    for i in range(iterations):
        temp = 1 - i/iterations
        new = {k: {'players': v['players'].copy(), 'points': v['points'].copy()} for k, v in current.items()}
        
        # Find two teams that aren't empty and can swap players
        non_empty_teams = [i for i in range(num_teams) if new[i]['players']]
        if len(non_empty_teams) < 2:
            continue
            
        t1, t2 = random.sample(non_empty_teams, 2)
        p1 = random.choice(new[t1]['players'])
        p2 = random.choice(new[t2]['players'])
        
        # Swap players
        new[t1]['players'].remove(p1)
        new[t2]['players'].remove(p2)
        new[t1]['players'].append(p2)
        new[t2]['players'].append(p1)
        
        # Swap points
        p1_points = new[t1]['points'].pop(p1)
        p2_points = new[t2]['points'].pop(p2)
        new[t1]['points'][p2] = p2_points
        new[t2]['points'][p1] = p1_points
        
        # Ensure team sizes remain valid
        if len(new[t1]['players']) > max_players_per_team or len(new[t2]['players']) > max_players_per_team:
            continue
            
        delta_e = energy(new) - energy(current)
        if delta_e < 0 or random.random() < math.exp(-delta_e/temp):
            current = new
    
    # Format output
    result = {}
    for team, data in current.items():
        result[team] = {
            'players': data['players'],
            'points': data['points'],
            'total': sum(data['points'].values()),
            'count': len(data['players'])
        }
    return result

def round_robin(players, num_teams, max_players_per_team):
    # Remove excess players if needed
    total_slots = num_teams * max_players_per_team
    if len(players) > total_slots:
        sorted_by_points = sorted(players.items(), key=lambda x: x[1])
        players = dict(sorted_by_points[-total_slots:])
        print(f"Removed {len(sorted_by_points)-total_slots} lowest-value players")
    
    sorted_players = sorted(players.items(), key=lambda x: -x[1])
    teams = {i: {'players': [], 'points': {}, 'total': 0, 'count': 0} for i in range(num_teams)}
    
    forward = True
    while True:
        made_assignment = False
        team_order = range(num_teams) if forward else range(num_teams-1, -1, -1)
        
        for team_idx in team_order:
            if teams[team_idx]['count'] < max_players_per_team and sorted_players:
                player, points = sorted_players.pop(0)
                teams[team_idx]['players'].append(player)
                teams[team_idx]['points'][player] = points  # Store individual points
                teams[team_idx]['total'] += points
                teams[team_idx]['count'] += 1
                made_assignment = True
        
        if not made_assignment:
            break
        forward = not forward
    
    return teams

def genetic_algorithm(players, num_teams, max_players_per_team, population_size=50, generations=100):
    # Remove excess players if needed
    total_slots = num_teams * max_players_per_team
    if len(players) > total_slots:
        sorted_by_points = sorted(players.items(), key=lambda x: x[1])
        players = dict(sorted_by_points[-total_slots:])
        print(f"Removed {len(sorted_by_points)-total_slots} lowest-value players")
    
    player_list = list(players.keys())
    
    def create_valid_individual():
        individual = []
        team_counts = [0] * num_teams
        for player in player_list:
            available_teams = [i for i in range(num_teams) if team_counts[i] < max_players_per_team]
            if not available_teams:
                break
            team = random.choice(available_teams)
            individual.append(team)
            team_counts[team] += 1
        return individual
    
    def fitness(individual):
        team_scores = [0]*num_teams
        team_counts = [0]*num_teams
        for i, team in enumerate(individual):
            team_scores[team] += players[player_list[i]]
            team_counts[team] += 1
        
        # Penalize teams that exceed size limit
        size_penalty = sum(max(0, count - max_players_per_team) for count in team_counts) * 1000
        return 1/(max(team_scores) - min(team_scores) + 0.01 + size_penalty)
    
    population = [create_valid_individual() for _ in range(population_size)]
    
    for _ in range(generations):
        population = sorted(population, key=lambda x: -fitness(x))
        next_gen = population[:10]  # Elite selection
        
        while len(next_gen) < population_size:
            parent1, parent2 = random.choices(population[:10], k=2)
            child = []
            for i in range(len(player_list)):
                child.append(parent1[i] if random.random() < 0.5 else parent2[i])
            
            # Mutation
            if random.random() < 0.1:
                player_idx = random.randint(0, len(child)-1)
                available_teams = [i for i in range(num_teams) 
                                 if sum(1 for t in child if t == i) < max_players_per_team]
                if available_teams:
                    child[player_idx] = random.choice(available_teams)
            
            next_gen.append(child)
        
        population = next_gen
    
    # Get the best individual
    best = max(population, key=fitness)  # This line was missing!
    
    # Format output with points information
    result = {i: {'players': [], 'points': {}, 'total': 0, 'count': 0} for i in range(num_teams)}
    for i, team in enumerate(best):
        player = player_list[i]
        result[team]['players'].append(player)
        result[team]['points'][player] = players[player]
        result[team]['total'] += players[player]
        result[team]['count'] += 1
    
    return result

def format_teams(teams, title="Team Balance Results"):
    """
    Formats team balance results in a readable way
    
    Args:
        teams: Dictionary of teams from greedy_balance_with_points()
        title: Optional title for the output
    """
    # Calculate overall stats
    total_players = sum(team['count'] for team in teams.values())
    total_points = sum(team['total'] for team in teams.values())
    avg_points = total_points / len(teams) if teams else 0
    point_diff = max(team['total'] for team in teams.values()) - min(team['total'] for team in teams.values()) if teams else 0
    
    # Build the output string
    output = []
    border = f"╔{'═' * (len(title)+2)}╗"
    output.append(border)
    output.append(f"║ {title.upper()} ║")
    output.append(f"╠{'═' * (len(title)+2)}╣")
    output.append(f"║ Teams: {len(teams)} | Players: {total_players} | Avg Points: {avg_points:.1f} ║")
    output.append(f"║ Max Point Difference: {point_diff:.1f} ║")
    output.append(f"╚{'═' * (len(border)-2)}╝")
    output.append("")
    
    # Add each team's details
    for team_id, team in sorted(teams.items()):
        team_header = f"TEAM {team_id + 1} ({team['total']} pts, {team['count']} players)"
        output.append(team_header)
        output.append("-" * len(team_header))
        
        # Sort players by points descending
        sorted_players = sorted(team['points'].items(), key=lambda x: -x[1])
        
        for player, points in sorted_players:
            output.append(f"• {player}: {points} pts")
        
        output.append("")  # Empty line between teams
    
    return "\n".join(output)

# parse people who are playing 

with open(file2, "r", encoding="utf-8") as file:
    lines = file.readlines()
gg = [line.strip() for index, line in enumerate(lines) if index % 2 == 1]

masterList = {player: D for player in gg}

for playing in gg:
    for tier, players in tier_dict.items():
        for player in players:
            positions = [i for i in range(len(player)) if player.startswith(playing, i)]
            if positions:
                if tier == 'S+':
                    del masterList[playing]
                    masterList[player] = SPLUS
                elif tier == 'S':
                    del masterList[playing]
                    masterList[player] = S
                elif tier == 'A+':
                    del masterList[playing]
                    masterList[player] = APLUS
                elif tier == 'A':
                    del masterList[playing]
                    masterList[player] = A
                elif tier == 'B':
                    del masterList[playing]
                    masterList[player] = B
                elif tier == 'C':
                    del masterList[playing]
                    masterList[player] = C

numTeams = int(input("Enter desired amount of teams: "))
numPlrs = int(input("Enter number of players per team: "))
algo = int(input("(1) Greedy (simple and good for smaller team sizes)\n(2) Annealing (uses probabilistic swaps with temperature parameters and can escape local optima)\n(3) Round Robin (simple, but less adaptable to odd team sizes, a bit bias)\n(4) Genetic (goes through hundreds of iterations and mutations to find the global optimum team composition mimicing actual gene evolution. Overkill, but gets better the more complex each players stats are)\n"))

if masterList:
    # for key, value in masterList.items():
    #     print(f"Key: {key}, Value: {value}")

    if algo == 1:
        g = greedy_balance_with_points(masterList, numTeams, numPlrs)
        print(format_teams(g))
    elif algo == 2:
        s = simulated_annealing(masterList, numTeams, numPlrs, iterations=10000)
        print(format_teams(s))
    elif algo == 3:
        r = round_robin(masterList, numTeams, numPlrs)
        print(format_teams(r))
    elif algo == 4:
        ge = genetic_algorithm(masterList, numTeams, numPlrs, population_size=50, generations=100)
        print(format_teams(ge))
    else:
        print("invalid input")


