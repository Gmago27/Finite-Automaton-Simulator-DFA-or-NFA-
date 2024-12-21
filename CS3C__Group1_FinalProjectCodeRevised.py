from tkinter import *
from tkinter import messagebox
from graphviz import Digraph
from PIL import Image, ImageTk
import os

class TransitionError(Exception):
    """Custom exception for transition validation errors."""
    pass

class InputError(Exception):
    """Custom exception for input string validation errors."""
    pass

class FiniteAutomaton:
    def __init__(self, states, alphabet, transitions, start_state, accept_states):
        self.states = states
        self.alphabet = alphabet
        self.transitions = transitions
        self.start_state = start_state
        self.accept_states = accept_states
        
        # First check if it's a DFA to determine validation strategy
        self.is_dfa = self.check_if_dfa()
        # Only validate transitions if it's a DFA
        if self.is_dfa:
            self.validate_transitions()

    def validate_input_string(self, input_string):
        """Validate that input string only contains symbols from the alphabet."""
        invalid_symbols = set()
        for symbol in input_string:
            if symbol not in self.alphabet:
                invalid_symbols.add(symbol)
        
        if invalid_symbols:
            error_msg = "Input string contains invalid symbols:\n"
            error_msg += f"Invalid symbols: {', '.join(invalid_symbols)}\n"
            error_msg += f"Allowed symbols (alphabet): {', '.join(self.alphabet)}"
            raise InputError(error_msg)

    def validate_transitions(self):
        """Validate transitions only for DFA cases."""
        if not self.is_dfa:
            return  # Skip validation for NFAs
            
        missing_transitions = []
        
        # For DFAs, check each state and alphabet combination
        for state in self.states:
            # Skip validation for accept states
            if state in self.accept_states:
                continue
                
            if state not in self.transitions:
                # State has no transitions at all
                missing_transitions.extend([f"({state}, {symbol})" for symbol in self.alphabet])
                continue
                
            for symbol in self.alphabet:
                if symbol not in self.transitions[state]:
                    missing_transitions.append(f"({state}, {symbol})")
                elif len(self.transitions[state][symbol]) != 1:
                    # For DFAs, each state-symbol pair should have exactly one next state
                    missing_transitions.append(f"({state}, {symbol}) - multiple transitions not allowed in DFA")
        
        if missing_transitions:
            error_msg = "DFA Validation Errors:\n"
            error_msg += "\n".join(missing_transitions)
            raise TransitionError(error_msg)

    def check_if_dfa(self):
        """Check if the automaton is a DFA."""
        # If there are any epsilon transitions, it's not a DFA
        for state in self.states:
            if state in self.transitions:
                if 'ε' in self.transitions[state]:
                    return False
                # Check if any symbol has multiple transitions
                for symbol in self.transitions[state]:
                    if len(self.transitions[state][symbol]) > 1:
                        return False
        
        return all(
            state in self.transitions and
            all(symbol in self.transitions[state] for symbol in self.alphabet)
            for state in self.states if state not in self.accept_states
        )

    def get_epsilon_closure(self, states):
        """Calculate epsilon closure for a set of states."""
        closure = set(states)
        stack = list(states)
        
        while stack:
            state = stack.pop()
            if state in self.transitions and 'ε' in self.transitions[state]:
                for next_state in self.transitions[state]['ε']:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)
        
        return closure

    def simulate(self, input_string):
        # First validate the input string
        self.validate_input_string(input_string)
        
        current_states = self.get_epsilon_closure({self.start_state})

        for symbol in input_string:
            next_states = set()
            for state in current_states:
                if state in self.transitions and symbol in self.transitions[state]:
                    next_states.update(self.transitions[state][symbol])
            
            next_states = self.get_epsilon_closure(next_states)
            
            if not next_states:
                return False

            current_states = next_states

        return bool(current_states & self.accept_states)

    def visualize(self, filename="automaton"):
        dot = Digraph()
        dot.attr(rankdir="LR")
        dot.attr("node", shape="circle")

        for state in self.states:
            if state in self.accept_states:
                dot.node(state, shape="doublecircle")
            else:
                dot.node(state)

        dot.node("start", shape="none", label="")
        dot.edge("start", self.start_state)

        for state, edges in self.transitions.items():
            for symbol, next_states in edges.items():
                for next_state in next_states:
                    dot.edge(state, next_state, label=symbol)

        dot.render(filename, format="png", cleanup=True)
        return f"{filename}.png"


class FiniteAutomatonGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Finite Automaton Simulator")

        # States
        self.states_label = Label(root, text="States (comma-separated):")
        self.states_label.pack()
        self.states_entry = Entry(root)
        self.states_entry.pack()

        # Alphabet
        self.alphabet_label = Label(root, text="Alphabet (comma-separated):")
        self.alphabet_label.pack()
        self.alphabet_entry = Entry(root)
        self.alphabet_entry.pack()

        # Start State
        self.start_state_label = Label(root, text="Start State:")
        self.start_state_label.pack()
        self.start_state_entry = Entry(root)
        self.start_state_entry.pack()

        # Accept States
        self.accept_states_label = Label(root, text="Accept States (comma-separated):")
        self.accept_states_label.pack()
        self.accept_states_entry = Entry(root)
        self.accept_states_entry.pack()

        # Transition input
        self.transitions_label = Label(root, text="Transitions (State, Symbol -> NextState, use 'eps' or 'epsilon' for ε transitions):")
        self.transitions_label.pack()
        self.transitions_text = Text(root, height=5, width=50)
        self.transitions_text.pack()

        # Example format label
        self.example_label = Label(root, text="Example format:\nq0,0 -> q1\nq0,eps -> q2\nq1,1 -> q2")
        self.example_label.pack()

        # Input string
        self.input_string_label = Label(root, text="Input String:")
        self.input_string_label.pack()
        self.input_string_entry = Entry(root)
        self.input_string_entry.pack()

        # Automaton type display
        self.automaton_type_label = Label(root, text="")
        self.automaton_type_label.pack()

        # Simulate Button
        self.simulate_button = Button(root, text="Simulate", command=self.simulate_automaton)
        self.simulate_button.pack()

        # Area to show graph
        self.graph_label = Label(root)
        self.graph_label.pack()

    def validate_basic_inputs(self):
        """Validate the basic inputs before processing transitions."""
        # Get and validate states
        states = [s.strip() for s in self.states_entry.get().split(',') if s.strip()]
        if not states:
            raise ValueError("States cannot be empty")

        # Get and validate alphabet
        alphabet = [s.strip() for s in self.alphabet_entry.get().split(',') if s.strip()]
        if not alphabet:
            raise ValueError("Alphabet cannot be empty")

        # Get and validate start state
        start_state = self.start_state_entry.get().strip()
        if not start_state:
            raise ValueError("Start state cannot be empty")
        if start_state not in states:
            raise ValueError(f"Start state '{start_state}' must be one of the defined states: {', '.join(states)}")

        # Get and validate accept states
        accept_states = set(s.strip() for s in self.accept_states_entry.get().split(',') if s.strip())
        if not accept_states:
            raise ValueError("Accept states cannot be empty")
        invalid_accept_states = accept_states - set(states)
        if invalid_accept_states:
            raise ValueError(f"Invalid accept states: {', '.join(invalid_accept_states)}\n"
                           f"Accept states must be from defined states: {', '.join(states)}")

        return states, alphabet, start_state, accept_states

    def parse_transitions(self, text):
        transitions = {}
        state_set = set(s.strip() for s in self.states_entry.get().split(','))
        alphabet_set = set(s.strip() for s in self.alphabet_entry.get().split(','))
        
        # Add epsilon to valid symbols if needed
        valid_symbols = alphabet_set | {'eps', 'epsilon', 'ε'}
        
        for line_num, line in enumerate(text.strip().split("\n"), 1):
            if not line.strip():  # Skip empty lines
                continue
                
            parts = line.split("->")
            if len(parts) != 2:
                raise ValueError(f"Invalid transition format at line {line_num}: {line}\n"
                               f"Expected format: state,symbol -> next_state")

            left = parts[0].strip()
            right = parts[1].strip()

            try:
                state, symbol = left.split(",")
            except ValueError:
                raise ValueError(f"Invalid transition format at line {line_num}: {line}\n"
                               f"Left side must contain exactly one state and one symbol separated by a comma")

            state = state.strip()
            symbol = symbol.strip().lower()
            next_state = right.strip()

            # Validate current state
            if state not in state_set:
                raise ValueError(f"Invalid state at line {line_num}: '{state}'\n"
                               f"State must be one of: {', '.join(sorted(state_set))}")

            # Validate symbol
            if symbol not in valid_symbols:
                raise ValueError(f"Invalid symbol at line {line_num}: '{symbol}'\n"
                               f"Symbol must be one of: {', '.join(sorted(alphabet_set))} "
                               f"(or 'eps'/'epsilon' for ε-transitions)")

            # Validate next state
            if next_state not in state_set:
                raise ValueError(f"Invalid next state at line {line_num}: '{next_state}'\n"
                               f"Next state must be one of: {', '.join(sorted(state_set))}")

            # Convert 'eps' or 'epsilon' to 'ε'
            if symbol in ['eps', 'epsilon']:
                symbol = 'ε'

            if state not in transitions:
                transitions[state] = {}
            if symbol not in transitions[state]:
                transitions[state][symbol] = []

            transitions[state][symbol].append(next_state)

        return transitions

    def simulate_automaton(self):
        try:
            # Clear any existing graph
            self.graph_label.config(image='')
            self.automaton_type_label.config(text="")

            # Validate basic inputs first
            states, alphabet, start_state, accept_states = self.validate_basic_inputs()

            # Parse transitions with enhanced error handling
            transitions = self.parse_transitions(self.transitions_text.get("1.0", "end-1c"))

            # Initialize automaton (this will validate transitions)
            automaton = FiniteAutomaton(states, alphabet, transitions, start_state, accept_states)

            # Determine automaton type
            automaton_type = "DFA"
            if not automaton.is_dfa:
                has_epsilon = any('ε' in transitions.get(state, {}) for state in states)
                automaton_type = "ε-NFA" if has_epsilon else "NFA"
            
            self.automaton_type_label.config(text=f"This automaton is a {automaton_type}")

            # Visualize
            graph_image = automaton.visualize(filename="automaton")
            self.display_graph(graph_image)

            # Simulate if input string is provided
            input_string = self.input_string_entry.get().strip()
            if input_string:
                is_accepted = automaton.simulate(input_string)
                result = f"The string '{input_string}' is {'ACCEPTED' if is_accepted else 'REJECTED'} by the automaton."
                messagebox.showinfo("Simulation Result", result)

        except InputError as e:
            messagebox.showerror("Invalid Input String", str(e))
        except TransitionError as e:
            messagebox.showerror("Incomplete Transitions", str(e))
        except ValueError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def display_graph(self, graph_image):
        image = Image.open(graph_image)
        photo = ImageTk.PhotoImage(image)
        self.graph_label.config(image=photo)
        self.graph_label.image = photo

def main():
    root = Tk()
    gui = FiniteAutomatonGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()