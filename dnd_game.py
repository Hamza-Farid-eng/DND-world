import random
import time
import sys


class Color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_slow(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def print_colored(text, color):
    print(f"{color}{text}{Color.ENDC}")


class Character:
    def __init__(self, name, char_class, level=1):
        self.name = name
        self.char_class = char_class
        self.level = level
        self.max_hp = self._calculate_max_hp()
        self.current_hp = self.max_hp
        self.attack_bonus = self._calculate_attack_bonus()
        self.damage_dice = self._calculate_damage_dice()

    def _calculate_max_hp(self):
        if self.char_class == "fighter":
            return random.randint(10, 12) * self.level
        elif self.char_class == "wizard":
            return random.randint(6, 8) * self.level
        elif self.char_class == "rogue":
            return random.randint(6, 8) * self.level
        else:
            return random.randint(8, 10) * self.level

    def _calculate_attack_bonus(self):
        if self.char_class == "fighter":
            return 5
        elif self.char_class == "wizard":
            return 2
        elif self.char_class == "rogue":
            return 4
        else:
            return 3

    def _calculate_damage_dice(self):
        if self.char_class == "fighter":
            return "1d8"
        elif self.char_class == "wizard":
            return "1d4"
        elif self.char_class == "rogue":
            return "1d6"
        else:
            return "1d8"

    def take_damage(self, damage):
        self.current_hp -= damage
        if self.current_hp < 0:
            self.current_hp = 0
        print_colored(f"{self.name} takes {damage} damage! HP: {self.current_hp}/{self.max_hp}", Color.WARNING)
        return self.current_hp == 0

    def attack(self, target):
        to_hit = random.randint(1, 20) + self.attack_bonus
        armor_class = target.ac if hasattr(target, 'ac') else 10
        hit = to_hit >= armor_class
        damage = self._roll_damage()
        if hit:
            target.take_damage(damage)
            return True, damage
        else:
            print_colored(f"{self.name} misses!", Color.WARNING)
            return False, 0

    def _roll_damage(self):
        sides = int(self.damage_dice.replace("d", ""))
        base = random.randint(1, sides)
        return base + self.level


def create_character():
    print_colored("\n=== Character Creation ===", Color.HEADER)
    name = input("Enter your name: ")
    char_class = input("Choose class (fighter/wizard/rogue): ").lower()
    while char_class not in ["fighter", "wizard", "rogue"]:
        char_class = input("Invalid class. Choose (fighter/wizard/rogue): ").lower()
    return Character(name, char_class)


def main():
    player = create_character()
    enemy = Character("Goblin", "fighter", level=1)
    enemy.ac = 15

    print_colored(f"\nWelcome, {player.name} the {player.char_class}!", Color.OKGREEN)
    print_colored(f"HP: {player.current_hp}/{player.max_hp}", Color.OKCYAN)
    print_colored(f"AC: {player.ac if hasattr(player, 'ac') else 10}", Color.OKCYAN)

    while player.current_hp > 0 and enemy.current_hp > 0:
        print("\n--- Your Turn ---")
        print("1. Attack")
        print("2. Heal (50 HP, once per battle)")
        choice = input("Choose action: ")

        if choice == "1":
            hit, dmg = player.attack(enemy)
            if hit:
                print_colored(f"Dealt {dmg} damage!", Color.OKGREEN)
        elif choice == "2":
            if player.current_hp < player.max_hp:
                heal = min(50, player.max_hp - player.current_hp)
                player.current_hp += heal
                print_colored(f"Healed for {heal} HP!", Color.OKCYAN)
            else:
                print_colored("Already at max HP!", Color.WARNING)

        if enemy.current_hp > 0:
            print("\n--- Enemy Turn ---")
            enemy_attack_success, dmg = enemy.attack(player)
            if enemy_attack_success:
                print_colored(f"Goblin dealt {dmg} damage!", Color.FAIL)

    if player.current_hp > 0:
        print_colored("\n=== Victory! ===", Color.OKGREEN)
    else:
        print_colored("\n=== Defeated ===", Color.FAIL)


if __name__ == "__main__":
    main()