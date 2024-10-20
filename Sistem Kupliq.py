import simpy
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx

# Coffee Shop Simulation
class CoffeeShop(object):
    def __init__(self, env):
        self.env = env
        self.server_1 = simpy.Resource(env, 1)  # One server for Server 1
        self.server_2 = simpy.Resource(env, 1)  # One server for Server 2
        self.requests = []  # To track actions for animation

    def serve_customer(self, customer_id, service_time, server_type):
        yield self.env.timeout(service_time)  # Service time (in minutes)
        self.requests.append({'action': 'served', 'id': customer_id, 'server': server_type})
        print(f"Customer {customer_id} finishes being served at {server_type} at time {self.env.now}")

def customer_arrival(env, customer_id, coffee_shop, arrival_time_1, service_time_1, arrival_time_2, service_time_2):
    # Customer arrives at Server 1 at time 'arrival_time_1'
    yield env.timeout(arrival_time_1)  # Wait for customer arrival at Server 1

    # Server 1 process
    with coffee_shop.server_1.request() as request_1:
        coffee_shop.requests.append({'action': 'arrive', 'id': customer_id, 'server': "Server 1"})
        yield request_1  # Wait for Server 1 to be available
        yield env.process(coffee_shop.serve_customer(customer_id, service_time_1, "Server 1"))

    # Wait for customer to arrive at Server 2
    delay = max(0, arrival_time_2 - env.now)  # Ensure delay is non-negative
    yield env.timeout(delay)  # Wait until arrival time at Server 2

    # Server 2 process
    with coffee_shop.server_2.request() as request_2:
        coffee_shop.requests.append({'action': 'arrive', 'id': customer_id, 'server': "Server 2"})
        yield request_2  # Wait for Server 2 to be available
        yield env.process(coffee_shop.serve_customer(customer_id, service_time_2, "Server 2"))

def run_coffee_shop(env, coffee_shop, arrival_times_1, service_times_1, arrival_times_2, service_times_2):
    # Process for all customers
    for customer_id, (arrival_time_1, service_time_1, arrival_time_2, service_time_2) in enumerate(zip(arrival_times_1, service_times_1, arrival_times_2, service_times_2)):
        env.process(customer_arrival(env, customer_id, coffee_shop, arrival_time_1, service_time_1, arrival_time_2, service_time_2))
    
    yield env.timeout(0)  # To make the function a generator

def main():
    # Initialize the simulation environment
    env = simpy.Environment()

    # Load the Excel file
    data = pd.read_excel('C:/Users/ASUS/OneDrive/Desktop/SEMESTER 5/PEMODELAN DAN SIMULASI/antrianKupliq/antrianKupliq.xlsx')

    # Correct column names from the Excel file
    arrival_times_server_1 = data['Waktu Kedatangan Customer ke Server 1 (menit)'].tolist()  # Arrival time at Server 1
    service_times_server_1 = data['Lama Waktu Pelayanan Customer oleh Server 1 (menit)'].tolist()  # Service time at Server 1
    arrival_times_server_2 = data['Waktu Kedatangan Customer ke Server 2 (menit)'].tolist()  # Arrival time at Server 2
    service_times_server_2 = data['Lama Waktu Pelayanan Customer oleh Server 2 (menit)'].tolist()  # Service time at Server 2

    # Initialize Coffee Shop
    coffee_shop = CoffeeShop(env)

    # Run simulation
    env.process(run_coffee_shop(env, coffee_shop, arrival_times_server_1, service_times_server_1, arrival_times_server_2, service_times_server_2))
    env.run()

    # Initialize graph for animation
    G = nx.DiGraph()
    G.add_node("Customer")
    G.add_node("Server 1")
    G.add_node("Server 2")
    G.add_edge("Customer", "Server 1")
    G.add_edge("Server 1", "Server 2")
    
    pos = {
        "Customer": (0, 0),
        "Server 1": (1, 1),
        "Server 2": (2, 1),
        "Served by Server 1": (1, 2),
        "Served by Server 2": (2, 2)
    }

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 4))
    plt.axis('off')

    # Draw initial nodes and edges
    nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=1500)
    nx.draw_networkx_labels(G, pos)
    edges = nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20, edge_color='grey')
    edge_labels = nx.get_edge_attributes(G, 'label')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='grey')

    # Animation update function
    def update(num):
        ax.clear()  # Clear the plot axis
        plt.axis('off')  # Turn off axis for visual focus
        nx.draw_networkx_nodes(G, pos, node_color='skyblue', node_size=1500)  # Redraw nodes
        nx.draw_networkx_labels(G, pos)  # Redraw labels

        # Ensure there is a request to process
        if num < len(coffee_shop.requests):
            action = coffee_shop.requests[num]['action']
            customer_id = coffee_shop.requests[num]['id']
            server = coffee_shop.requests[num]['server']

            # Debugging: Print the node names and server reference
            print(f"Debug: Action={action}, Customer ID={customer_id}, Server={server}")

            # Ensure 'server' is in the pos dictionary
            if server not in pos:
                print(f"Error: Server '{server}' not found in pos dictionary")
                return  # Stop further execution if server is not found

            if action == 'arrive':
                edges = nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20, edge_color='green', edgelist=[("Customer", server) if server == "Server 1" else ("Server 1", "Server 2")])
                edge_labels = {("Customer", server): f"Customer {customer_id} arriving"} if server == "Server 1" else {("Server 1", "Server 2"): f"Customer {customer_id} going to Server 2"}
            elif action == 'served':
                served_node = f"Served by {server}"
                if served_node not in G:
                    G.add_node(served_node)  # Add new node
                    G.add_edge(server, served_node)  # Add new edge
                    pos[served_node] = (pos[server][0], pos[server][1] + 1)  # Set new node position

                edges = nx.draw_networkx_edges(G, pos, arrowstyle='->', arrowsize=20, edge_color='orange', edgelist=[(server, served_node)])
                edge_labels = {(server, served_node): f"Customer {customer_id} served"}

            # Draw edge labels
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='grey')

    # Run animation
    ani = FuncAnimation(fig, update, frames=len(coffee_shop.requests), repeat=False)
    ani.save('kupliq_cafe_simulation.gif', writer='pillow', fps=120)
    plt.show()

    print("Simulation completed.")

if __name__ == "__main__":
    main()
