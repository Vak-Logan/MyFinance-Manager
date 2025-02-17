import sqlite3
from datetime import datetime


class DatabaseManager:
    """
    Handles the database connection and query execution.

    This class manages a SQLite database connection and provides methods
    to execute queries and fetch results.

    Attributes:
        conn (sqlite3.Connection): The SQLite database connection.
        cursor (sqlite3.Cursor): The database cursor.
    """

    def __init__(self, db_name):
        """
        Initialise a DatabaseManager instance.

        Establishes a connection to the specified SQLite database.

        :param db_name: The name or path of the SQLite database file.
        :type db_name: str
        :raises sqlite3.Error: If the connection cannot be established.
        """
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")

    def execute_query(self, query, params=()):
        """
        Execute a SQL query that modifies the database.

        Executes the provided query with the given parameters and 
        commits the changes.

        :param query: The SQL query to execute.
        :type query: str
        :param params: Parameters to substitute into the query.
        :type params: tuple
        :raises sqlite3.Error: If an error occurs during query execution
        """
        try:
            self.cursor.execute(query, params)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error during execute_query: {e}")

    def fetch_all(self, query, params=()):
        """
        Execute a SQL query and fetch all results.

        :param query: The SQL query to execute.
        :type query: str
        :param params: Parameters to substitute into the query.
        :type params: tuple
        :return: A list of rows resulting from the query.
        :rtype: list
        :raises sqlite3.Error: If an error occurs during query execution
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database error during fetch_all: {e}")
            return []

    def close_connection(self):
        """
        Close the database connection.

        :raises sqlite3.Error: If an error occurs while closing the 
        connection.
        """
        try:
            self.conn.close()
        except sqlite3.Error as e:
            print(f"Error closing database connection: {e}")


class ExpenseManager:
    """
    Handles operations related to expenses and expense categories.
    """

    def __init__(self, db_manager):
        """
        Initialise the ExpenseManager.

        :param db_manager: An instance of DatabaseManager.
        :type db_manager: DatabaseManager
        """
        self.db_manager = db_manager

    def get_expense_categories(self):
        """
        Fetch all expense categories from the database.

        :return: A list of tuples containing category IDs and names.
        :rtype: list
        """
        query = "SELECT id, name FROM expense_categories"
        return self.db_manager.fetch_all(query)

    def add_expense_category(self):
        """
        Add a new expense category to the database.

        Prompts the user for the category name.
        """
        category_name = input("Enter new expense category name: ").strip()
        if not category_name:
            print("Category name cannot be empty.")
            return
        query = "INSERT INTO expense_categories (name) VALUES (?)"
        self.db_manager.execute_query(query, (category_name,))
        print(f"Expense category '{category_name}' added successfully.")

    def delete_expense_category(self):
        """
        Delete an expense category if it is not used by any expenses.

        Prompts the user to select a category ID.
        """
        categories = self.get_expense_categories()
        if not categories:
            print("No expense categories available.")
            return
        print("Expense Categories:")
        for cat in categories:
            print(f"{cat[0]} - {cat[1]}")
        try:
            cat_id = int(input("Enter the ID of the category to delete: "))
        except ValueError:
            print("Invalid input. Enter a valid number.")
            return

        cat_query = ("SELECT COUNT(*) FROM expenses WHERE category = "
                     "(SELECT name FROM expense_categories WHERE id = ?)")
        result = self.db_manager.fetch_all(cat_query, (cat_id,))
        if result and result[0][0] > 0:
            print("Cannot delete category: Expenses use this category.")
            return
        del_query = "DELETE FROM expense_categories WHERE id = ?"
        self.db_manager.execute_query(del_query, (cat_id,))
        print("Expense category deleted successfully.")

    def add_expense(self, amount):
        """
        Add a new expense record to the database.

        Prompts the user for a valid date and an expense category, then
        inserts the expense.

        :param amount: The expense amount.
        :type amount: float
        """
        while True:
            date = input("Enter the date (YYYY-MM-DD): ")
            try:
                datetime.strptime(date, '%Y-%m-%d')
                break
            except ValueError:
                print("Incorrect date format. Please try again.")

        categories = self.get_expense_categories()
        if not categories:
            print("No expense categories found. Please add one first.")
            self.add_expense_category()
            categories = self.get_expense_categories()
            if not categories:
                print("Unable to add expense without a category.")
                return

        print("Select an expense category:")
        for cat in categories:
            print(f"{cat[0]} - {cat[1]}")
        try:
            cat_choice = int(input("Enter the category ID: "))
        except ValueError:
            print("Invalid input. Enter a valid number.")
            return

        category = None
        for cat in categories:
            if cat[0] == cat_choice:
                category = cat[1]
                break
        if not category:
            print("Invalid category selection.")
            return

        query = ("INSERT INTO expenses (category, amount, timestamp) "
                 "VALUES (?, ?, ?)")
        self.db_manager.execute_query(query, (category, amount, date))
        print("Expense added successfully.")

    def view_expense(self, month, year, category=None):
        """
        Display expenses for the specified month and year, optionally
        filtered by category.

        :param month: The month for which to view expenses.
        :type month: int
        :param year: The year for which to view expenses.
        :type year: int
        :param category: Optional; filter expenses by category.
        :type category: str or None
        :return: True if expenses exist, False otherwise.
        :rtype: bool
        """
        if category:
            query = ("SELECT * FROM expenses WHERE category = ? AND "
                     "strftime('%m', timestamp) = ? AND "
                     "strftime('%Y', timestamp) = ?")
            params = (category, f"{month:02d}", str(year))
        else:
            query = (
                "SELECT * FROM expenses WHERE strftime('%m', timestamp) = ? "
                "AND strftime('%Y', timestamp) = ?"
            )
            params = (f"{month:02d}", str(year))
        expenses = self.db_manager.fetch_all(query, params)
        if not expenses:
            msg = (f"No expenses found for {month}/{year}" if not category
                   else f"No expenses for '{category}' in {month}/{year}.")
            print(msg)
            return False
        print("Expenses:")
        for expense in expenses:
            print(f"ID: {expense[0]}, Category: {expense[1]}, "
                  f"Amount: £{expense[2]:.2f}, Date: {expense[3]}")
        return True

    def view_expenses_by_category(self, month, year):
        """
        Display expenses filtered by a chosen category for the given 
        period.

        :param month: The month for filtering.
        :type month: int
        :param year: The year for filtering.
        :type year: int
        """
        categories = self.get_expense_categories()
        if not categories:
            print("No expense categories available.")
            return
        print("Available Expense Categories:")
        for cat in categories:
            print(f"{cat[0]} - {cat[1]}")
        try:
            cat_id = int(input("Enter the category ID to filter by: "))
        except ValueError:
            print("Invalid input. Enter a valid number.")
            return
        category = None
        for cat in categories:
            if cat[0] == cat_id:
                category = cat[1]
                break
        if not category:
            print("Invalid category selection.")
            return
        self.view_expense(month, year, category)

    def update_expense_amount(self):
        """
        Update an expense record for a specified month and year.

        Displays expenses for the period, verifies the chosen record ID,
        and updates the expense amount.
        """
        try:
            month = int(input("Enter the month (1-12) to update: "))
            if not 1 <= month <= 12:
                print("Month must be between 1 and 12.")
                return
            year = int(input("Enter the year (e.g., 2025): "))
            if year <= 0:
                print("Year must be positive.")
                return
        except ValueError:
            print("Invalid input for month/year.")
            return

        query = (
            "SELECT id, category, amount, timestamp FROM expenses WHERE "
            "strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?"
        )
        expenses = self.db_manager.fetch_all(
                    query, (f"{month:02d}", str(year))
        )
        if not expenses:
            print("No expenses available to update for this period.")
            return
        print("Expenses:")
        for expense in expenses:
            print(f"ID: {expense[0]}, Category: {expense[1]}, "
                  f"Amount: £{expense[2]:.2f}, Date: {expense[3]}")
        try:
            expense_id = int(input("Enter the ID of the expense to update: "))
            new_amount = float(input("Enter the new expense amount: "))
        except ValueError:
            print("Invalid input. Enter valid numbers.")
            return

        valid_ids = [exp[0] for exp in expenses]
        if expense_id not in valid_ids:
            print("Invalid expense ID selected.")
            return

        update_query = "UPDATE expenses SET amount = ? WHERE id = ?"
        self.db_manager.execute_query(update_query, (new_amount, expense_id))
        print("Expense updated successfully.")


class IncomeManager:
    """
    Handles operations related to income and income categories.
    """

    def __init__(self, db_manager):
        """
        Initialise the IncomeManager.

        :param db_manager: An instance of DatabaseManager.
        :type db_manager: DatabaseManager
        """
        self.db_manager = db_manager

    def get_income_categories(self):
        """
        Fetch all income categories from the database.

        :return: A list of tuples containing category IDs and names.
        :rtype: list
        """
        query = "SELECT id, name FROM income_categories"
        return self.db_manager.fetch_all(query)

    def add_income_category(self):
        """
        Add a new income category to the database.

        Prompts the user for the category name.
        """
        category_name = input("Enter new income category name: ").strip()
        if not category_name:
            print("Category name cannot be empty.")
            return
        query = "INSERT INTO income_categories (name) VALUES (?)"
        self.db_manager.execute_query(query, (category_name,))
        print(f"Income category '{category_name}' added successfully.")

    def delete_income_category(self):
        """
        Delete an income category if it is not used by any records.

        Prompts the user to select a category ID.
        """
        categories = self.get_income_categories()
        if not categories:
            print("No income categories available.")
            return
        print("Income Categories:")
        for cat in categories:
            print(f"{cat[0]} - {cat[1]}")
        try:
            cat_id = int(input("Enter the ID of the category to delete: "))
        except ValueError:
            print("Invalid input. Enter a valid number.")
            return

        cat_query = ("SELECT COUNT(*) FROM income WHERE category = "
                     "(SELECT name FROM income_categories WHERE id = ?)")
        result = self.db_manager.fetch_all(cat_query, (cat_id,))
        if result and result[0][0] > 0:
            print("Cannot delete category: Income records use this category.")
            return

        del_query = "DELETE FROM income_categories WHERE id = ?"
        self.db_manager.execute_query(del_query, (cat_id,))
        print("Income category deleted successfully.")

    def add_income(self, amount):
        """
        Add a new income record to the database.

        Prompts the user for a valid date and an income category, then
        inserts the record.

        :param amount: The income amount.
        :type amount: float
        """
        while True:
            date = input("Enter the date (YYYY-MM-DD): ")
            try:
                datetime.strptime(date, '%Y-%m-%d')
                break
            except ValueError:
                print("Incorrect date format. Please try again.")

        categories = self.get_income_categories()
        if not categories:
            print("No income categories found. Please add one first.")
            self.add_income_category()
            categories = self.get_income_categories()
            if not categories:
                print("Unable to add income without a category.")
                return

        print("Select an income category:")
        for cat in categories:
            print(f"{cat[0]} - {cat[1]}")
        try:
            cat_choice = int(input("Enter the category ID: "))
        except ValueError:
            print("Invalid input. Enter a valid number.")
            return

        category = None
        for cat in categories:
            if cat[0] == cat_choice:
                category = cat[1]
                break
        if not category:
            print("Invalid category selection.")
            return

        query = ("INSERT INTO income (category, amount, timestamp) "
                 "VALUES (?, ?, ?)")
        self.db_manager.execute_query(query, (category, amount, date))
        print("Income added successfully.")

    def view_income(self, month, year, category=None):
        """
        Display income records for a specified month and year,
        optionally filtered by category.

        :param month: The month for which to view income.
        :type month: int
        :param year: The year for which to view income.
        :type year: int
        :param category: Optional; filter income by category.
        :type category: str or None
        :return: True if income records exist, False otherwise.
        :rtype: bool
        """
        if category:
            query = ("SELECT * FROM income WHERE category = ? AND "
                     "strftime('%m', timestamp) = ? AND "
                     "strftime('%Y', timestamp) = ?")
            params = (category, f"{month:02d}", str(year))
        else:
            query = (
                "SELECT * FROM income WHERE strftime('%m', timestamp) = ? "
                "AND strftime('%Y', timestamp) = ?"
            )
            params = (f"{month:02d}", str(year))
        incomes = self.db_manager.fetch_all(query, params)
        if not incomes:
            msg = (
                f"No income records found for {month}/{year}" if not category
                else f"No income for '{category}' in {month}/{year}."
            )
            print(msg)
            return False
        print("Income Records:")
        for income in incomes:
            print(f"ID: {income[0]}, Category: {income[1]}, "
                  f"Amount: £{income[2]:.2f}, Date: {income[3]}")
        return True

    def view_income_by_category(self, month, year):
        """
        Display income records filtered by a chosen category for the 
        given period.

        :param month: The month for filtering.
        :type month: int
        :param year: The year for filtering.
        :type year: int
        """
        categories = self.get_income_categories()
        if not categories:
            print("No income categories available.")
            return
        print("Available Income Categories:")
        for cat in categories:
            print(f"{cat[0]} - {cat[1]}")
        try:
            cat_id = int(input("Enter the category ID to filter by: "))
        except ValueError:
            print("Invalid input. Enter a valid number.")
            return
        category = None
        for cat in categories:
            if cat[0] == cat_id:
                category = cat[1]
                break
        if not category:
            print("Invalid category selection.")
            return
        self.view_income(month, year, category)

    def update_income_record(self):
        """
        Update an income record for a specified month and year.

        Displays income records for the period, verifies the chosen 
        record ID, and updates the income amount.
        """
        try:
            month = int(input("Enter the month (1-12) to update income: "))
            if not 1 <= month <= 12:
                print("Month must be between 1 and 12.")
                return
            year = int(input("Enter the year (e.g., 2025): "))
            if year <= 0:
                print("Year must be positive.")
                return
        except ValueError:
            print("Invalid input for month/year.")
            return

        query = (
            "SELECT id, category, amount, timestamp FROM income WHERE "
            "strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?"
        )
        incomes = self.db_manager.fetch_all(query, (f"{month:02d}", str(year)))
        if not incomes:
            print("No income records available to update for this period.")
            return
        print("Income Records:")
        for income in incomes:
            print(f"ID: {income[0]}, Category: {income[1]}, "
                  f"Amount: £{income[2]:.2f}, Date: {income[3]}")
        try:
            income_id = int(input("Enter the ID of the record to update: "))
            new_amount = float(input("Enter the new income amount: "))
        except ValueError:
            print("Invalid input. Enter valid numbers.")
            return

        valid_ids = [inc[0] for inc in incomes]
        if income_id not in valid_ids:
            print("Invalid income record ID selected.")
            return

        update_query = "UPDATE income SET amount = ? WHERE id = ?"
        self.db_manager.execute_query(update_query, (new_amount, income_id))
        print("Income record updated successfully.")


class BudgetManager:
    """
    Handles operations related to budgets.
    """

    def __init__(self, db_manager):
        """
        Initialise the BudgetManager.

        :param db_manager: An instance of DatabaseManager.
        :type db_manager: DatabaseManager
        """
        self.db_manager = db_manager

    def set_budget(self, category, budget_amount, month, year):
        """
        Set or update a budget for a specific category and period.

        :param category: The expense category.
        :type category: str
        :param budget_amount: The budget amount.
        :type budget_amount: float
        :param month: The month for the budget.
        :type month: int
        :param year: The year for the budget.
        :type year: int
        """
        query = (
            "INSERT INTO budget (category, budget_amount, month, year) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(category, month, year) "
            "DO UPDATE SET budget_amount = excluded.budget_amount"
        )
        self.db_manager.execute_query(query, (category, budget_amount,
                                                month, year))
        print(f"Budget of £{budget_amount:.2f} set for '{category}' "
              f"for {month}/{year}.")

    def view_budget_for_category(self, category, month, year):
        """
        Display the budget and total expenses for a given category and 
        period.

        :param category: The expense category.
        :type category: str
        :param month: The month for which to view the budget.
        :type month: int
        :param year: The year for which to view the budget.
        :type year: int
        """
        budget_query = (
            "SELECT budget_amount FROM budget WHERE category = ? "
            "AND month = ? AND year = ?"
        )
        budget_result = self.db_manager.fetch_all(budget_query,
                                                  (category, month, year))
        if not budget_result:
            print(f"No budget set for '{category}' for {month}/{year}.")
            return
        budget_amount = budget_result[0][0]
        expense_query = (
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE category = ? "
            "AND SUBSTR(timestamp, 6, 2) = ? AND SUBSTR(timestamp, 1, 4) = ?"
        )
        expense_result = self.db_manager.fetch_all(expense_query,
                                                   (category,
                                                    f"{month:02d}",
                                                    str(year)))
        total_expenses = expense_result[0][0]
        print(f"Category: {category} for {month}/{year}")
        print(f"Budgeted Amount: £{budget_amount:.2f}")
        print(f"Total Expenses: £{total_expenses:.2f}")
        if total_expenses > budget_amount:
            print(f"Over budget by: £{total_expenses - budget_amount:.2f}")
        else:
            print(f"Under budget by: £{budget_amount - total_expenses:.2f}")

    def view_all_budgets(self):
        """
        Display all budgets sorted by year, month, and category.
        """
        query = ("SELECT * FROM budget ORDER BY year, month, category")
        budgets = self.db_manager.fetch_all(query)
        if not budgets:
            print("No budgets set.")
            return
        print("Budgets:")
        for b in budgets:
            print(f"ID: {b[0]}, Category: {b[1]}, Budget: £{b[2]:.2f}, "
                  f"Month: {b[3]}, Year: {b[4]}")

    def calculate_overall_budget(self, month, year):
        """
        Calculate the overall budget (total income minus total expenses)
        for a given period.

        :param month: The month for calculation.
        :type month: int
        :param year: The year for calculation.
        :type year: int
        """
        income_query = (
            "SELECT COALESCE(SUM(amount), 0) FROM income WHERE "
            "strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?"
        )
        expense_query = (
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE "
            "strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?"
        )
        total_income = self.db_manager.fetch_all(income_query,
                         (f"{month:02d}", str(year)))[0][0]
        total_expenses = self.db_manager.fetch_all(expense_query,
                           (f"{month:02d}", str(year)))[0][0]
        net_budget = total_income - total_expenses
        print(f"\nOverall budget for {month}/{year}:")
        print(f"Total Income: £{total_income:.2f}")
        print(f"Total Expenses: £{total_expenses:.2f}")
        print(f"Net Budget: £{net_budget:.2f}")


class GoalManager:
    """
    Handles financial goals, including creating, updating and tracking.
    """

    def __init__(self, db_manager):
        """
        Initialise the GoalManager.

        :param db_manager: An instance of DatabaseManager.
        :type db_manager: DatabaseManager
        """
        self.db_manager = db_manager

    def display_goal_menu(self):
        """
        Display the financial goals submenu options and process input.
        """
        while True:
            print("\nFinancial Goals Menu:")
            print("1 - Create a new savings goal")
            print("2 - Change the target amount for a goal")
            print("3 - Add excess income to savings goals")
            print("4 - Remove or move savings from a goal")
            print("5 - Return to main menu")
            try:
                option = int(input("Select an option: "))
                if option == 1:
                    self.create_goal()
                elif option == 2:
                    self.change_goal_amount()
                elif option == 3:
                    self.add_excess_income()
                elif option == 4:
                    self.remove_or_move_savings()
                elif option == 5:
                    break
                else:
                    print("Invalid option. Try again.")
            except ValueError:
                print("Invalid input. Enter a number.")

    def create_goal(self):
        """
        Create a new savings goal.

        Prompts the user for the goal name, target amount and target 
        date.
        """
        goal_name = input("Enter the name of the savings goal: ")
        try:
            target_amount = float(input("Enter the target amount to save: "))
        except ValueError:
            print("Invalid target amount. Enter a number.")
            return
        target_date = input("Enter the target date (YYYY-MM-DD): ")
        try:
            datetime.strptime(target_date, '%Y-%m-%d')
        except ValueError:
            print("Incorrect date format. Use YYYY-MM-DD.")
            return
        query = ("INSERT INTO savings_goals (goal_name, target_amount, "
                 "target_date) VALUES (?, ?, ?)")
        self.db_manager.execute_query(query, (goal_name, target_amount,
                                              target_date))
        print(f"Savings goal '{goal_name}' created successfully!")

    def change_goal_amount(self):
        """
        Change the target amount of an existing savings goal.

        Prompts the user to select a goal and enter the new target 
        amount.
        """
        goals = self.db_manager.fetch_all(
            "SELECT id, goal_name, target_amount FROM savings_goals"
        )
        if not goals:
            print("No savings goals found.")
            return
        print("\nExisting Savings Goals:")
        for goal in goals:
            print(f"{goal[0]} - {goal[1]} (Target: £{goal[2]:.2f})")
        try:
            goal_id = int(input("Enter the goal ID to modify: "))
            new_amount = float(input("Enter the new target amount: "))
        except ValueError:
            print("Invalid input. Enter valid numbers.")
            return
        query = "UPDATE savings_goals SET target_amount = ? WHERE id = ?"
        self.db_manager.execute_query(query, (new_amount, goal_id))
        print("Goal updated successfully!")

    def add_excess_income(self):
        """
        Calculate available excess income and allocate it among goals.

        Excess income is the total income minus expenses and already
        allocated savings. The user is prompted to distribute the 
        amount.
        """
        try:
            month = int(input("Enter the month (1-12) for calculation: "))
            if not 1 <= month <= 12:
                print("Month must be between 1 and 12.")
                return
            year = int(input("Enter the year (e.g., 2025): "))
            if year <= 0:
                print("Year must be positive.")
                return
        except ValueError:
            print("Invalid input. Enter valid numbers for month and year.")
            return

        income_query = (
            "SELECT COALESCE(SUM(amount), 0) FROM income WHERE "
            "strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?"
        )
        expense_query = (
            "SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE "
            "strftime('%m', timestamp) = ? AND strftime('%Y', timestamp) = ?"
        )
        total_income = self.db_manager.fetch_all(income_query,
                         (f"{month:02d}", str(year)))[0][0]
        total_expenses = self.db_manager.fetch_all(expense_query,
                           (f"{month:02d}", str(year)))[0][0]
        allocated_result = self.db_manager.fetch_all(
            "SELECT COALESCE(SUM(current_saved), 0) FROM savings_goals"
        )
        allocated_excess = allocated_result[0][0] if allocated_result else 0
        available_excess = total_income - total_expenses - allocated_excess
        if available_excess <= 0:
            print("No excess income available for savings.")
            return
        print(
            f"\nYou have £{available_excess:.2f} in available excess income."
        )
        goals = self.db_manager.fetch_all(
            "SELECT id, goal_name FROM savings_goals"
        )
        if not goals:
            print("No savings goals found. Create one first.")
            return
        print("\nYour savings goals:")
        allocations = {}
        for goal in goals:
            while True:
                try:
                    amt = float(input(
                        f"Enter amount to add to '{goal[1]}' (0 to skip): "))
                    if amt < 0:
                        print("Amount cannot be negative.")
                    elif amt > available_excess:
                        print("Cannot allocate more than available excess.")
                    else:
                        if amt > 0:
                            allocations[goal[0]] = amt
                            available_excess -= amt
                        break
                except ValueError:
                    print("Invalid input. Enter a number.")
        for goal_id, amt in allocations.items():
            update_query = ("UPDATE savings_goals SET current_saved = "
                            "current_saved + ? WHERE id = ?")
            self.db_manager.execute_query(update_query, (amt, goal_id))
        print("Savings updated successfully!")

    def remove_or_move_savings(self):
        """
        Remove or transfer savings from a selected goal.

        The user can choose to remove savings or transfer them to 
        another goal.
        """
        goals = self.db_manager.fetch_all(
            "SELECT id, goal_name, current_saved FROM savings_goals"
        )
        if not goals:
            print("No savings goals found.")
            return
        print("\nYour savings goals:")
        for goal in goals:
            print(f"{goal[0]} - {goal[1]} (Saved: £{goal[2]:.2f})")
        try:
            goal_id = int(input("Enter the goal ID to modify: "))
            amt = float(input("Enter the amount to remove or transfer: "))
        except ValueError:
            print("Invalid input. Enter valid numbers.")
            return
        current_saved_result = self.db_manager.fetch_all(
            "SELECT current_saved FROM savings_goals WHERE id = ?",
            (goal_id,)
        )
        if not current_saved_result:
            print("Goal not found.")
            return
        current_saved = current_saved_result[0][0]
        if amt > current_saved:
            print("Cannot remove more than the saved amount.")
            return
        action = input(
            "Do you want to (1) remove or (2) transfer this amount? "
            "Enter 1 or 2: "
        )
        if action == "1":
            update_query = ("UPDATE savings_goals SET current_saved = "
                            "current_saved - ? WHERE id = ?")
            self.db_manager.execute_query(update_query, (amt, goal_id))
            print("Amount removed successfully.")
        elif action == "2":
            print("\nSelect a goal to transfer savings to:")
            for goal in goals:
                if goal[0] != goal_id:
                    print(f"{goal[0]} - {goal[1]}")
            try:
                new_goal_id = int(input("Enter the new goal ID: "))
            except ValueError:
                print("Invalid input. Enter a valid goal ID.")
                return
            transfer_query = ("UPDATE savings_goals SET current_saved = "
                              "current_saved + ? WHERE id = ?")
            self.db_manager.execute_query(transfer_query, (amt, new_goal_id))
            update_query = ("UPDATE savings_goals SET current_saved = "
                            "current_saved - ? WHERE id = ?")
            self.db_manager.execute_query(update_query, (amt, goal_id))
            print("Amount transferred successfully.")
        else:
            print("Invalid option.")

    def view_goal_progress(self):
        """
        Display the progress for all savings goals.

        Shows the saved amount and target amount for each goal.
        """
        goals = self.db_manager.fetch_all(
            "SELECT goal_name, target_amount, current_saved, target_date "
            "FROM savings_goals"
        )
        if not goals:
            print("No savings goals set.")
            return
        print("\nSavings Goal Progress:")
        for goal in goals:
            name, target, saved, date = goal
            progress = (saved / target) * 100 if target > 0 else 0
            print(f"{name}: £{saved:.2f}/£{target:.2f} saved "
                  f"({progress:.2f}%) - Target Date: {date}")


class MainMenu:
    """
    Handles the main user interface and menu navigation.

    Provides submenus for managing and viewing expenses, income, 
    budgets, and financial goals.
    """

    def __init__(self, expense_manager, income_manager, budget_manager,
                 goal_manager):
        """
        Initialise the MainMenu.

        :param expense_manager: An instance of ExpenseManager.
        :type expense_manager: ExpenseManager
        :param income_manager: An instance of IncomeManager.
        :type income_manager: IncomeManager
        :param budget_manager: An instance of BudgetManager.
        :type budget_manager: BudgetManager
        :param goal_manager: An instance of GoalManager.
        :type goal_manager: GoalManager
        """
        self.expense_manager = expense_manager
        self.income_manager = income_manager
        self.budget_manager = budget_manager
        self.goal_manager = goal_manager

    def display_main_menu(self):
        """
        Display the main menu options.
        """
        print("\nMain Menu:")
        print("1 - Manage expenses")
        print("2 - View expenses")
        print("3 - Manage income")
        print("4 - View income")
        print("5 - Manage budgets")
        print("6 - View budgets")
        print("7 - Manage financial goals")
        print("8 - View progress towards financial goals")
        print("9 - Quit")

    def manage_expenses_menu(self):
        """
        Display and process the Manage Expenses submenu.
        """
        while True:
            print("\nManage Expenses:")
            print("1 - Add expense")
            print("2 - Update an expense record")
            print("3 - Manage expense categories")
            print("4 - Return to main menu")
            choice = input("Select an option: ")
            if choice == "1":
                try:
                    amt = float(input("Enter the expense amount: "))
                except ValueError:
                    print("Invalid amount.")
                    continue
                self.expense_manager.add_expense(amt)
            elif choice == "2":
                self.expense_manager.update_expense_amount()
            elif choice == "3":
                while True:
                    print("\nExpense Category Management:")
                    print("1 - Add new expense category")
                    print("2 - Delete an expense category")
                    print("3 - Return to Manage Expenses menu")
                    cat_choice = input("Select an option: ")
                    if cat_choice == "1":
                        self.expense_manager.add_expense_category()
                    elif cat_choice == "2":
                        self.expense_manager.delete_expense_category()
                    elif cat_choice == "3":
                        break
                    else:
                        print("Invalid option.")
            elif choice == "4":
                break
            else:
                print("Invalid option.")

    def view_expenses_menu(self):
        """
        Display and process the View Expenses submenu.
        """
        while True:
            print("\nView Expenses:")
            print("1 - View all expenses")
            print("2 - View expenses by category")
            print("3 - Return to main menu")
            choice = input("Select an option: ")
            if choice == "1":
                try:
                    month = int(input("Enter month (1-12): "))
                    if not 1 <= month <= 12:
                        print("Month must be between 1 and 12.")
                        continue
                    year = int(input("Enter year (e.g., 2025): "))
                    if year <= 0:
                        print("Year must be positive.")
                        continue
                except ValueError:
                    print("Invalid input.")
                    continue
                self.expense_manager.view_expense(month, year)
            elif choice == "2":
                try:
                    month = int(input("Enter month (1-12): "))
                    if not 1 <= month <= 12:
                        print("Month must be between 1 and 12.")
                        continue
                    year = int(input("Enter year (e.g., 2025): "))
                    if year <= 0:
                        print("Year must be positive.")
                        continue
                except ValueError:
                    print("Invalid input.")
                    continue
                self.expense_manager.view_expenses_by_category(month, year)
            elif choice == "3":
                break
            else:
                print("Invalid option.")

    def manage_income_menu(self):
        """
        Display and process the Manage Income submenu.
        """
        while True:
            print("\nManage Income:")
            print("1 - Add income")
            print("2 - Update an income record")
            print("3 - Manage income categories")
            print("4 - Return to main menu")
            choice = input("Select an option: ")
            if choice == "1":
                try:
                    amt = float(input("Enter the income amount: "))
                except ValueError:
                    print("Invalid amount.")
                    continue
                self.income_manager.add_income(amt)
            elif choice == "2":
                self.income_manager.update_income_record()
            elif choice == "3":
                while True:
                    print("\nIncome Category Management:")
                    print("1 - Add new income category")
                    print("2 - Delete an income category")
                    print("3 - Return to Manage Income menu")
                    cat_choice = input("Select an option: ")
                    if cat_choice == "1":
                        self.income_manager.add_income_category()
                    elif cat_choice == "2":
                        self.income_manager.delete_income_category()
                    elif cat_choice == "3":
                        break
                    else:
                        print("Invalid option.")
            elif choice == "4":
                break
            else:
                print("Invalid option.")

    def view_income_menu(self):
        """
        Display and process the View Income submenu.
        """
        while True:
            print("\nView Income:")
            print("1 - View all income")
            print("2 - View income by category")
            print("3 - Return to main menu")
            choice = input("Select an option: ")
            if choice == "1":
                try:
                    month = int(input("Enter month (1-12): "))
                    if not 1 <= month <= 12:
                        print("Month must be between 1 and 12.")
                        continue
                    year = int(input("Enter year (e.g., 2025): "))
                    if year <= 0:
                        print("Year must be positive.")
                        continue
                except ValueError:
                    print("Invalid input.")
                    continue
                self.income_manager.view_income(month, year)
            elif choice == "2":
                try:
                    month = int(input("Enter month (1-12): "))
                    if not 1 <= month <= 12:
                        print("Month must be between 1 and 12.")
                        continue
                    year = int(input("Enter year (e.g., 2025): "))
                    if year <= 0:
                        print("Year must be positive.")
                        continue
                except ValueError:
                    print("Invalid input.")
                    continue
                self.income_manager.view_income_by_category(month, year)
            elif choice == "3":
                break
            else:
                print("Invalid option.")

    def manage_budgets_menu(self):
        """
        Display and process the Manage Budgets submenu.
        """
        while True:
            print("\nManage Budgets:")
            print("1 - Set/Update a budget for a category")
            print("2 - Return to main menu")
            choice = input("Select an option: ")
            if choice == "1":
                categories = self.expense_manager.get_expense_categories()
                if not categories:
                    print(
                        "No expense categories available. Please add one "
                        "first."
                    )
                    continue
                print("Available Expense Categories:")
                for cat in categories:
                    print(f"{cat[0]} - {cat[1]}")
                try:
                    cat_id = int(input("Select a category ID: "))
                except ValueError:
                    print("Invalid input.")
                    continue
                selected_category = None
                for cat in categories:
                    if cat[0] == cat_id:
                        selected_category = cat[1]
                        break
                if not selected_category:
                    print("Invalid category selected.")
                    continue
                try:
                    budget_amt = float(input("Enter the budget amount: "))
                    month = int(input("Enter month (1-12): "))
                    if not 1 <= month <= 12:
                        print("Month must be between 1 and 12.")
                        continue
                    year = int(input("Enter year (e.g., 2025): "))
                    if year <= 0:
                        print("Year must be positive.")
                        continue
                except ValueError:
                    print("Invalid input for budget, month, or year.")
                    continue
                self.budget_manager.set_budget(selected_category, budget_amt,
                                               month, year)
            elif choice == "2":
                break
            else:
                print("Invalid option.")

    def view_budgets_menu(self):
        """
        Display and process the View Budgets submenu.
        """
        while True:
            print("\nView Budgets:")
            print("1 - View all budgets")
            print("2 - View budget by category")
            print("3 - Calculate overall budget")
            print("4 - Return to main menu")
            choice = input("Select an option: ")
            if choice == "1":
                self.budget_manager.view_all_budgets()
            elif choice == "2":
                categories = self.expense_manager.get_expense_categories()
                if not categories:
                    print(
                        "No expense categories available. "
                        "Please add one first."
                    )
                    continue
                print("Available Expense Categories:")
                for cat in categories:
                    print(f"{cat[0]} - {cat[1]}")
                try:
                    cat_id = int(input("Select a category ID: "))
                except ValueError:
                    print("Invalid input.")
                    continue
                selected_category = None
                for cat in categories:
                    if cat[0] == cat_id:
                        selected_category = cat[1]
                        break
                if not selected_category:
                    print("Invalid category selected.")
                    continue
                try:
                    month = int(input("Enter month (1-12): "))
                    if not 1 <= month <= 12:
                        print("Month must be between 1 and 12.")
                        continue
                    year = int(input("Enter year (e.g., 2025): "))
                    if year <= 0:
                        print("Year must be positive.")
                        continue
                except ValueError:
                    print("Invalid month or year.")
                    continue
                self.budget_manager.view_budget_for_category(selected_category,
                                                             month, year)
            elif choice == "3":
                try:
                    month = int(input("Enter month (1-12): "))
                    if not 1 <= month <= 12:
                        print("Month must be between 1 and 12.")
                        continue
                    year = int(input("Enter year (e.g., 2025): "))
                    if year <= 0:
                        print("Year must be positive.")
                        continue
                except ValueError:
                    print("Invalid input for month or year.")
                    continue
                self.budget_manager.calculate_overall_budget(month, year)
            elif choice == "4":
                break
            else:
                print("Invalid option.")

    def run_menu(self):
        """
        Run the main menu loop.

        Processes user input and routes to the appropriate submenu.
        """
        while True:
            self.display_main_menu()
            choice = input("Select an option: ")
            try:
                option = int(choice)
            except ValueError:
                print("Please enter a valid number.")
                continue
            if option == 1:
                self.manage_expenses_menu()
            elif option == 2:
                self.view_expenses_menu()
            elif option == 3:
                self.manage_income_menu()
            elif option == 4:
                self.view_income_menu()
            elif option == 5:
                self.manage_budgets_menu()
            elif option == 6:
                self.view_budgets_menu()
            elif option == 7:
                self.goal_manager.display_goal_menu()
            elif option == 8:
                self.goal_manager.view_goal_progress()
            elif option == 9:
                print("Goodbye!")
                break
            else:
                print("Invalid option.")


# Database setup
db_manager = DatabaseManager("expense_and_budget.db")

# Create table for expenses
db_manager.execute_query('''
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp TEXT NOT NULL
    )
''')

# Create table for expense categories
db_manager.execute_query('''
    CREATE TABLE IF NOT EXISTS expense_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
''')

# Create table for income
db_manager.execute_query('''
    CREATE TABLE IF NOT EXISTS income (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        timestamp TEXT NOT NULL
    )
''')

# Create table for income categories
db_manager.execute_query('''
    CREATE TABLE IF NOT EXISTS income_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL
    )
''')

# Create table for budgets
db_manager.execute_query('''
    CREATE TABLE IF NOT EXISTS budget (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        budget_amount REAL NOT NULL,
        month INTEGER NOT NULL,
        year INTEGER NOT NULL,
        UNIQUE(category, month, year)
    )
''')

# Create table for savings goals
db_manager.execute_query('''
    CREATE TABLE IF NOT EXISTS savings_goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_name TEXT NOT NULL,
        target_amount REAL NOT NULL,
        current_saved REAL DEFAULT 0,
        target_date TEXT NOT NULL
    )
''')

expense_manager = ExpenseManager(db_manager)
income_manager = IncomeManager(db_manager)
budget_manager = BudgetManager(db_manager)
goal_manager = GoalManager(db_manager)
main_menu = MainMenu(expense_manager, income_manager, budget_manager, 
                     goal_manager)

main_menu.run_menu()
db_manager.close_connection()
