# 🔬 Lab3: Python


## 📌 Objectives

- Students should be able to understand Object-Oriented Programming (OOP), including classes, attributes, and methods.
- Students should be able to explain inheritance and method overriding in OOP.
- Students should be able to implement game mechanics using programming logic in a game simulation.

---

## 📜 Overview of the Simplified Risk Game 

This simplified version of the Risk board game involves:
- Two players (a user and the computer).
- Recruiting armies with different unit types (`Footman`, `Archer`, `Knight`, and `SiegeMachine`).
- Taking turns to attack until one side is defeated.
- Using dice rolls to determine attack outcomes.

### Rules for This Simplified Risk Game

This version of Risk is a simplified, turn-based game involving two players: the **user** and the **computer**. Players recruit armies within a budget and take turns attacking each other until one side is eliminated. The game is played as follows:

---

### 1. Game Setup
- **Players**: There are two players:
  - **User**: You, the player.
  - **Computer**: Controlled by the program.
- **Budget**: Each player starts with a fixed number of coins to recruit their army. By default, this budget is 30 coins.
- **Unit Types**:
  - **Footman**: Cost: 1 coin, Health: 1, Hit Threshold: 5+
  - **Archer**: Cost: 2 coins, Health: 1, Hit Threshold: 4+
  - **Knight**: Cost: 3 coins, Health: 2, Hit Threshold: 3+
  - **Siege Machine**: Cost: 10 coins, Health: 3, Hit Threshold: 3+ (rolls two dice when attacking)

  The hit threshold is the minimum dice roll a unit needs to score a successful hit during an attack (e.g., a Footman hits on a roll of 5 or higher). It determines the unit's effectiveness in battle, with lower thresholds making a unit more likely to hit.

- **Recruitment**: 
  - Players recruit units randomly until their budget runs out.
  - A maximum of **2 Siege Machines** can be recruited per player.

---

### 2. Combat Mechanics
- **Turn-Based Gameplay**:
  - The **user** attacks first, followed by the **computer**.
  - Players alternate turns until one side is completely defeated.

- **Attacking**:
  - Players attack with one type of unit at a time (in the order: Siege Machine → Archer → Knight → Footman).
  - Each unit rolls dice to determine how many hits they score:
    - A unit scores a hit if the dice roll is greater than or equal to its **hit threshold**.
    - **Footman, Archer, and Knight** roll one die.
    - **Siege Machines** roll two dice.
  - The total number of hits is calculated and applied to the opposing player.

- **Defending**:
  - The defending player absorbs hits by assigning damage to random units in their army.
  - Units with zero health are eliminated and removed from the army.

---

### 3. End of Game
- The game ends when one player's army is completely defeated.
- The remaining player's army is declared the winner.
- The program displays:
  - The composition of the winning army.
  - A message announcing the winner.

---

### 4. Example Walkthrough
1. **Recruitment Phase**:
   - Both players recruit units based on their budget. For example:
     - User: 2 Footmen, 1 Archer, 1 Knight, 1 Siege Machine.
     - Computer: 3 Footmen, 2 Archers, 1 Knight.
   - The composition of each army is displayed before the battle begins.

1. **Battle Phase**:
   - **Turn 1**: 
     - User's Siege Machine rolls two dice and scores 1 hit. The hit is applied to a random unit in the computer's army.
     - Computer's Siege Machine rolls two dice and scores 2 hits. The hits are applied to the user's units.
   - **Subsequent Turns**:
     - Both players alternate attacking with their next unit types (e.g., Archers, Knights).
     - Damage is applied to the defending player's army after each attack.

1. **Game Over**:
   - The game ends when one player's army is eliminated. The program announces the winner and shows the remaining army of the victorious player.

---

This straightforward set of rules ensures that the focus remains on implementing and understanding the **object-oriented programming concepts** behind the game.

---

## 💻 Procedure

1. **Understand the Code**:
   - Read through each class and its methods.
   - Pay attention to the `TODO` sections.

1. **Implement the Missing Functionality**:
   - Follow the instructions in the `TODO` comments to complete the methods:

1. **Test the Implementation**:
   - Use the `test()` function provided in the code to test individual unit behaviors (e.g., `roll_attack` and `take_damage`).
   - Uncomment the `main()` function to play the full game after completing the `TODO` sections.

---

### Setup

1. Go to your local repository, e.g., 
    ```bash  
    cd ~/master_ws/src/ece387-baek  
    ```  
    If you already have a `lab3` directory, delete it:
    ```bash  
    rm -rf lab3  
    ```  
    Then, create a new lab3 directory:
    ```bash  
    mkdir lab3  
    ```  
        

1. Download the [`risk.zip`](../files/risk.zip) file in your `~/Downloads` directory and unzip it. You should see five files:
    - `COLCON_IGNORE`: ROS2 will ignore this folder for the later labs
    - `course_roster.py`: OOP Example used in class. Review this file to learn OOP.
    - `example_output.txt`: Your final output should resemble this example.
    - `README.MD`: The README file for this lab
    - `risk_base.py`: The file you will copy and use for this lab. 

1. Move the five files into the `lab3` directory. You can do this using on the GUI.

1. Navigate to your local repository and copy `risk_base.py` to create your own working file. 
    ```bash
    cd ~/master_ws/src/lab3
    cp risk_base.py risk.py
    ```

1. Do **not** modify `risk_base.py`. All your work should be done in `risk.py`


1. Open **VS Code** by running the following command in your terminal:  
    ```bash  
    code .  
    ```  
    Make all changes **only** in `risk.py`.
   
### Classes and Responsibilities

```{hint}
You can find an example output in `example_output.txt`.  
```

#### **1. `Unit` Class**
- Represents a generic unit in the game.
- Attributes include:
  - `name`: The name of the unit.
  - `cost`: How much it costs to recruit this unit.
  - `health`: The unit's health points.
  - `hit_threshold`: The minimum dice roll needed for the unit to score a hit.
- **Methods**:
  - `roll_attack()`: Simulates a dice roll and determines if the unit scores a hit. It returns the total number of hits scored by the unit.
  - `take_damage(damage)`: Reduces the unit's health by the specified damage.
    - **TODO**: Subtract the damage value from `self.health` and ensure health doesn't go below 0. Hint: Use the `max()` function to ensure health doesn't drop below 0.
  - `isalive()`: Checks if the unit is still alive (health > 0). Hint: Check the value of `self.health` and return a boolean.
    - **TODO**: Return `True` if health > 0, else return `False`.

#### **2. Subclasses (`Footman`, `Archer`, `Knight`, `SiegeMachine`)**
- Inherit from the `Unit` class.
- Each unit type has specific attributes for `cost`, `health`, and `hit_threshold`.
- **SiegeMachine Special Ability**:
  - Rolls **two dice** instead of one for its attack.
  - **TODO**: Implement the `roll_attack` method in the `SiegeMachine` class to roll two dice and count the hits. Hint: Count how many rolls are greater than or equal to `hit_threshold` and return that count. Use `random.randint(1, 6)` to simulate rolling a six-sided die.

#### **3. `Player` Class**
- Represents a player (user or computer).
- Attributes include:
  - `name`: The player's name.
  - `budget`: Coins available for recruiting units.
  - `army`: List of units the player has recruited.
- **Methods**:
  - `recruit_units()`: Randomly recruits units within the player's budget. Ensure the player doesn't exceed the max allowed Siege Machines.
    - **TODO**: 
      - Check the player's remaining budget before adding a unit. 2
      - If the selected unit is a Siege Machine, ensure the player has not exceeded `MaxSiegeUnits`.
      - Append the unit to `self.army` and deduct the unit's cost from `self.budget`.
    - **HINTs**: Inside the while loop:
      - Use isinstance() to check if the unit is an instance of the SiegeMachine class.
      - Logic to skip adding another Siege Machine if `siege_count >= MaxSiegeUnits`.
      - Add the unit to the player's army.
      - Deduct the unit's cost from `self.budget`.
  - `attack(defender)`: Simulates an attack on another player. Roll dice for units of the current type and calculate the total hits.
    - **TODO**: 
      - Loop through `self.army` and roll attack dice for units of the current type.
      - Keep track of the total number of hits and print the results.
      - Call `defender.resolve_damage()` with the total hits.
    - **HINTS**: Inside the for loop:
      - Roll attack dice for the unit.
      - Add the resulting hits to `total_hits`.
      - Print the result, e.g., "Knight (Health: 2) scores 1 hit(s)"

  - `resolve_damage(total_damage)`: Applies damage to the player's units and resolve damage by applying it to random units in the army. Units with zero health should be removed from the army.
    - **TODO**: 
      - While the total damage is nonzero, randomly pick a unit from `self.army` using `random.choice()`.
      - Call `unit.take_damage(1)` for the chosen unit.
      - If the unit's health drops to 0, remove it from the army.
      - Print the name of the unit eliminated (if any).
    
#### **4. `Risk` Class**
- Represents the overall game.
- Attributes:
  - `user`: The human player.
  - `computer`: The AI opponent.
- **Methods**:
  - `play()`: Runs the game loop until one player is defeated.
  - Prints the final outcome of the game.



### **Expected Outputs**

#### **Test Function**
When you run `test()`, you should see:
- Units rolling dice and scoring hits.
- Units taking damage and being eliminated when their health reaches 0.

#### **Main Game**
When you run the game:
- Both players will recruit armies based on their budget.
- Players will take turns attacking until one is defeated.
- The final result will display the surviving army composition for the winner.

---

## 🚚 **Deliverables**  

1. Complete all `TODO` sections in your code.  
1. Test your code thoroughly to ensure it works as expected.  
1. Once your code is complete, save the output to a file by running:  
    ```bash  
    python risk.py > output.txt  
    ```  
1. Push both your code and the output file (`output.txt`) to your GitHub repository.  
1. Submit the **Lab3** assignment on Gradescope.  
---

Good luck, and enjoy coding! 🎯