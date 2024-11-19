#!/usr/bin/env python3
# main.py
import os
import sys
import time
import json
import subprocess
import tempfile
from dataclasses import dataclass
from typing import List, Callable, Any
from pathlib import Path
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import TerminalFormatter

@dataclass
class TestCase:
    inputs: List[Any]
    expected_output: Any

RESET = '\033[0m'
base_dir = Path.home() / '.termcode'
base_dir.mkdir(exist_ok=True)
problems_dir = base_dir / 'problems'
solutions_dir = base_dir / 'solutions'
creations_dir = base_dir / 'creations'
config_path = base_dir / '.config.json'


def difficulty_attr(difficulty):
    if difficulty.lower() == 'easy':
        return f'\033[92m{difficulty.capitalize()}{RESET}'  # Green
    elif difficulty.lower() == 'medium':
        return f'\033[93m{difficulty.capitalize()}{RESET}'  # Yellow
    elif difficulty.lower() == 'hard':
        return f'\033[91m{difficulty.capitalize()}{RESET}'  # Red
    return difficulty  # Default case


@dataclass
class Problem:
    id: int
    title: str
    difficulty: str
    description: str
    function_template: str
    test_cases: List[TestCase]
    completion: str
    @classmethod
    def from_json(cls, json_data: dict) -> 'Problem':
        return cls(
            id=json_data['id'],
            title=json_data['title'],
            difficulty=json_data['difficulty'],
            description=json_data['description'],
            function_template=json_data['function_template'],
            test_cases=[TestCase(**tc) for tc in json_data['test_cases']],
            completion=json_data['completion']
        )
    def to_json(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'difficulty': self.difficulty,
            'description': self.description,
            'function_template': self.function_template,
            'test_cases': [{'inputs': tc.inputs, 'expected_output': tc.expected_output} 
                          for tc in self.test_cases],
            'completion': self.completion
        }

class TerminalLeetCode:
    def __init__(self):
        # load files
        self.base_dir = Path.home() / '.termcode'
        self.base_dir.mkdir(exist_ok=True)
        self.problems_dir = self.base_dir / 'problems'
        self.solutions_dir = self.base_dir / 'solutions'
        self.creations_dir = self.base_dir / 'creations'
        self.config_path = self.base_dir / '.config.json'

        self.problems = []
        self.current_problem = None
        self.user_code = ""
        self.editor = 'vi'  # Default editor

        self.problems_dir.mkdir(exist_ok=True)
        self.solutions_dir.mkdir(exist_ok=True)

        if self.config_path.exists():
            self.load_config(self.config_path)

        self.problems = []
        self.current_problem = None
        self.user_code = ""
        
        # Create necessary directories
        self.problems_dir.mkdir(exist_ok=True)
        self.solutions_dir.mkdir(exist_ok=True)
        
        # Load problems
        self.load_problems()

    def load_config(self, config_path):
        try:
            with open(config_path, 'r') as f:  # Use config_path parameter instead of self.config_path
                config = json.load(f)
                self.editor = config.get('editor', 'vi')  # Use get() with default value
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"\033[91mError loading config: {e}. Using default editor (vi)\033[0m")
            self.editor = 'vi'
            global editor
            editor = self.editor

    def load_problems(self):
        for problem_file in self.problems_dir.glob('*.json'):
            with open(problem_file, 'r') as f:
                problem_data = json.load(f)
                self.problems.append(Problem.from_json(problem_data))
        self.problems.sort(key=lambda x: x.id)

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def highlight_code(self, code):
        return highlight(code, PythonLexer(), TerminalFormatter())
    def print_header(self):
        print(f"""
\033[90m╔╦╗╔═╗╦═╗╔╦╗\033[93m╔═╗╔═╗╔╦╗╔═╗
\033[90m ║ ║╣ ╠╦╝║║║\033[93m║  ║ ║ ║║║╣ 
\033[90m ╩ ╚═╝╩╚═╩ ╩\033[93m╚═╝╚═╝═╩╝╚═╝\033[0m
              """)

    def display_problems(self):
        self.clear_screen()
        self.print_header()
        print(f"\033[97mAvailable Problems:{RESET}\n")
        # Initialize lists for different difficulty levels
        easy = []
        med = []
        hard = []
        completed = []
        incomplete = []
        titlelen = 40  # Adjust this value based on your needs

        for problem in self.problems:
            title = problem.title
            check = problem.completion  # You'll need to add this attribute to your Problem class
            difficulty = problem.difficulty
            prob_id = problem.id
            
            # Set completion symbol
            if check == 'no':
                check_show = f'\033[91m✗{RESET}'
            elif check == 'yes':
                check_show = f'\033[92m✓{RESET}'
            elif check == 'incomplete':
                check_show = f'\033[93m⚠{RESET}'
            else:
                check_show = ' '
            
            # Create line formation
            if check == 'yes':
                formatted = f"{prob_id} │ \033[09m\033[97m{title.capitalize()}{RESET}{((titlelen+3) - len(title)) * ' '}{check_show} │ {difficulty_attr(difficulty)}"
            else:
                formatted = f"{prob_id} │ \033[97m{title.capitalize()}{RESET}{((titlelen+3) - len(title)) * ' '}{check_show} │ {difficulty_attr(difficulty)}"
            # find longest title
            # Sort problems by difficulty
            if check == 'yes':
                completed.append(formatted)
            #if check == 'incomplete':
            #    incomplete.append(formatted)
            elif difficulty.lower() == 'easy':
                easy.append(formatted)
            elif difficulty.lower() == 'medium':
                med.append(formatted)
            elif difficulty.lower() == 'hard':
                hard.append(formatted)

        # Combine all problems in order
        result = incomplete + easy + med + hard + completed
        
        # Display all problems
        grid_inf = (f"ID│ {RESET}Problem Title{RESET}{((titlelen+3) - 23) * ' '} Completion │ Difficulty")
        print(f"{grid_inf}\n{'─' * (len(grid_inf)-8)}")
        for line in result:
            print(line)
        
        print("\nEnter problem number to select, or 'q' to quit")

    #def save_problem_state(self, problem: Problem):
    #    # Convert problem to json and save it
    #    try:
    #        problem_path = self.problems_dir / f"{problem.title}.json"
    #        with open(problem_path, 'w') as f:
    #            json.dump(problem.__dict__, f, indent=4)  # Assuming you want to save all attributes
    #    except Exception as e:
    #        print(f"\033[91mError saving problem state: {e}\033[0m")

    def display_problem(self, problem: Problem):
        #problem.completion = 'incomplete'
        #self.save_problem_state(problem)


        if problem.difficulty.lower() == 'easy':
            difficulty_colored = f'\033[92m{problem.difficulty}{RESET}'
        elif problem.difficulty.lower() == 'medium':
            difficulty_colored = f'\033[93m{problem.difficulty}{RESET}'
        elif problem.difficulty.lower() == 'hard':
            difficulty_colored = f'\033[91m{problem.difficulty}{RESET}'
        else:
            difficulty_colored = problem.difficulty  # Default, no color
        self.clear_screen()
        self.print_header()
        print(f"\033[90mProblem {problem.id} \033[94m{problem.title}{RESET}")
        print(f"\033[90mDifficulty: {difficulty_colored}")
        print("\n\033[90mDescription:")
        print(f"\033[97m{problem.description}{RESET}\n")
        for i in range(2):
            test_case = problem.test_cases[i]
            inputs_str = (highlight(repr(test_case.inputs), PythonLexer(), TerminalFormatter()).strip())
            expected_output_str = (highlight(repr(test_case.expected_output), PythonLexer(), TerminalFormatter()).strip())
            print(f"Test Case {i + 1}:")
            print(f"  \033[90mInputs: {RESET}{inputs_str}{RESET}")
            print(f"  \033[90mExpected: {RESET}{expected_output_str}{RESET}\n")
        print("\nOptions:")
        print("w. Write solution")
        print("t. Test solution")
        print("r. Return to problem list")
        print("q. Quit")

    def get_editor_command(self, editor=None):
         # Priority: passed editor > environment variable > config file editor > default (vi)
        if editor:
            return editor
        return os.environ.get('EDITOR', self.editor)

    def write_solution(self):
        # Create solution file if it doesn't exist
        solution_file = self.solutions_dir / f"problem_{self.current_problem.id}_solution.py"
        
        if not solution_file.exists():
            with open(solution_file, 'w') as f:
                f.write(self.current_problem.function_template)

        # Open the solution file in the user's preferred editor
        editor = self.get_editor_command(self.editor)
        subprocess.call([editor, str(solution_file)])

        # Read the solution after editing
        with open(solution_file, 'r') as f:
            self.user_code = f.read()

    def run_tests(self):
        self.clear_screen()
        self.print_header()
        print("Running tests...\n")

        if not self.user_code:
            print("No solution provided yet!")
            return

        try:
            # Create a namespace for the user's code
            namespace = {}
            exec(self.user_code, namespace)
            
            # Get the function from the namespace
            func_name = self.current_problem.function_template.split('def ')[1].split('(')[0]
            user_function = namespace[func_name]

            all_passed = True
            for i, test_case in enumerate(self.current_problem.test_cases, 1):
                print(f"Test case {i}:")
                print(f"Input: {test_case.inputs}")
                print(f"Expected: {test_case.expected_output}")
                
                try:
                    if len(test_case.inputs) == 1:
                        result = user_function(test_case.inputs[0])
                    else:
                        result = user_function(*test_case.inputs)
                    
                    print(f"Your output: {result}")
                    
                    if result == test_case.expected_output:
                        print("✓ Passed")
                    else:
                        print("✗ Failed")
                        all_passed = False
                except Exception as e:
                    print(f"✗ Error: {str(e)}")
                    all_passed = False
                print()

            if all_passed:
                print("Congratulations! All test cases passed!")
                
            else:
                print("Some test cases failed. Keep trying!")

        except Exception as e:
            print(f"Error in your code: {str(e)}")

        input("\nPress Enter to continue...")

    def run(self):
        while True:
            if self.current_problem is None:
                self.display_problems()
                choice = input("\nEnter your choice: ").strip().lower()
                
                if choice == 'q':
                    break
                
                try:
                    problem_id = int(choice)
                    self.current_problem = next((p for p in self.problems if p.id == problem_id), None)
                    if not self.current_problem:
                        print("\033[91mUknown Problem Input Detected\033[0m")
                        time.sleep(1)
                except ValueError:
                    print("\033[91mUknown Input Detected\033[0m")
                    time.sleep(1)
            else:
                self.display_problem(self.current_problem)
                choice = input("\nEnter your choice: ").strip().lower()
                
                if choice == 'q':
                    break
                elif choice == 'w':
                    self.write_solution()
                elif choice == 't':
                    self.run_tests()
                elif choice == 'r':
                    self.current_problem = None
                    self.user_code = ""
                else:
                    print("\033[91mUknown Input Detected\033[0m")
                    time.sleep(1)

        self.clear_screen()
        #print("Thank you for using Terminal LeetCode!")

def reshuffle_id_nums():
    shuffled = False
    for _ in os.listdir(problems_dir):
        id_nums_seen = []
        for filename in os.listdir(problems_dir):
            file_path = os.path.join(problems_dir, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'r') as f:
                    problem_data = json.load(f)
                    id_num = problem_data['id']
                    if id_num not in id_nums_seen:
                        id_nums_seen.append(id_num)
                    else:
                        id_num += 1
                        problem_data['id'] = id_num
                        with open(file_path, 'w') as f:
                            json.dump(problem_data, f, indent=4)
                        print("\033[92mDuplicate ID's Detected!\nID numbers reshuffled successfully!\033[0m")
                        shuffled = True
    if not shuffled:
        print("\033[91mNo duplicate ID's detected!\033[0m")

                        

            

def create_template():
    subprocess.run(['curl','-s', '-o',  os.path.join(creations_dir, 'template.json'), 'https://raw.githubusercontent.com/sjapanwala/termcode/main/problems/template.json'])
    print("\033[92mTemplate created successfully!\nStored in ~/.termcode/creations\033[0m")
    subprocess.run(['curl', 'https://raw.githubusercontent.com/sjapanwala/termcode/main/problems/template.json'])

def usage():
    return(f"""
\033[90m╔╦╗╔═╗╦═╗╔╦╗\033[93m╔═╗╔═╗╔╦╗╔═╗
\033[90m ║ ║╣ ╠╦╝║║║\033[93m║  ║ ║ ║║║╣ 
\033[90m ╩ ╚═╝╩╚═╩ ╩\033[93m╚═╝╚═╝═╩╝╚═╝\033[0m
           
Welcome To Termcode, The \033[03mLeetcode{RESET} Recreation Built In Python!
A fun little CLI tool built to import and solve Leetcode problems (or any other coding challenge!).

USAGE:
  termcode <options>

OPTIONS:
 (no args)          Run the program
  --v               Print the version number
  --help            Print this help message
  --editor          Specify the editor to use (default: vi)
  --template        creates a json template to create custom problems
  --import (url)    import a problem (read documentation)
  --shuffle         if imorted problems are out of order (occurs by default anyways)
  --update          updates the application (sudo)
  --remove          remove the application (sudo)

NOTE:
    Imported Files / Folders Are Directed To Go TO 
        \033[92m~/.termcode/problems/\033[0m
    Solutions Are Created In
        \033[92m~/.termcode/solutions/\033[0ma
    Config File Is Stored In (where editior option is)
        \033[92m~/.termcode/.config.json\033[0m
    Template File Is Stored In
        \033[92m~/.termcode/creations/template.json\033[0m

For More Documentation, Please Visit ReadME.md on Github Repo
    \033[92m\033[03mhttps://github.com/sjapanwala/TermCode{RESET}
          """)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        app = TerminalLeetCode()
        app.run()
    elif sys.argv[1] == "--v":
        print(f"\033[90mTerm\033[93mCode {RESET} v\033[90m0.5\033[0m\n\033[92m\033[03mhttps://github.com/sjapanwala/TermCode{RESET}")
    elif sys.argv[1] == "--help":
        print(usage())
    elif sys.argv[1] == "--editor":
        subprocess.run(["vi", config_path])
    elif sys.argv[1] == "--template":
        create_template()
        subprocess.run(["vi", creations_dir/"template.json"])
    elif sys.argv[1] == "--shuffle":
        reshuffle_id_nums()

