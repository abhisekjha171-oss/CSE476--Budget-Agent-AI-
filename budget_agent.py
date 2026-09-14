"""
Personal Budget Assistant Agent (Topic T1)
CSE476 - Agentic AI and Intelligent Automation, CA1 Project 1
"""

import re
from dataclasses import dataclass, field
from datetime import datetime


# ========== MEMORY ==========
@dataclass
class Expense:
    item: str
    amount: float
    category: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class BudgetMemory:
    def __init__(self, monthly_budget=10000.0):
        self.expenses = []
        self.turns = []
        self.monthly_budget = monthly_budget
    
    def add_expense(self, expense):
        self.expenses.append(expense)
    
    def get_total_spent(self, category=None):
        if category:
            return sum(e.amount for e in self.expenses if e.category == category)
        return sum(e.amount for e in self.expenses)
    
    def get_summary_text(self):
        if not self.expenses:
            return "No expenses recorded yet."
        total = self.get_total_spent()
        lines = [f"Total spent: ₹{total:.2f} / ₹{self.monthly_budget:.2f}"]
        cats = {}
        for e in self.expenses:
            cats[e.category] = cats.get(e.category, 0) + e.amount
        for c, a in sorted(cats.items(), key=lambda x: -x[1]):
            lines.append(f"  • {c}: ₹{a:.2f}")
        return "\n".join(lines)
    
    def add_turn(self, role, content, tool_calls=None, observations=None):
        self.turns.append({
            "role": role,
            "content": content,
            "tool_calls": tool_calls or [],
            "observations": observations or [],
            "time": datetime.now().isoformat()
        })


# ========== TOOLS ==========
class BudgetTools:
    def __init__(self, memory):
        self.memory = memory
    
    def add_expense(self, item, amount, category="general"):
        self.memory.add_expense(Expense(item, amount, category))
        return f"OK, recorded '{item}' = ₹{amount:.2f} under [{category}]."
    
    def get_summary(self, category=None):
        if category:
            tot = self.memory.get_total_spent(category)
            cnt = sum(1 for e in self.memory.expenses if e.category == category)
            return f"[{category}] ₹{tot:.2f} across {cnt} item(s)."
        return self.memory.get_summary_text()


# ========== PLANNER ==========
class Planner:
    def __init__(self, memory):
        self.memory = memory
    
    def plan(self, goal):
        g = goal.lower()
        steps = []
        nums = re.findall(r'[₹$]?\s*(\d+(?:\.\d+)?)', goal)
        
        is_spend = any(k in g for k in ["spent", "bought", "paid", "purchase", "cost me", "add", "buy"])
        is_ask = any(k in g for k in ["summary", "spent", "balance", "how much", "total", "budget"])
        is_afford = "afford" in g
        
        if is_spend and nums:
            steps.append({"tool": "add_expense", "params": {"item": goal.strip(), "amount": float(nums[0])}})
        if is_ask or is_afford or is_spend:
            steps.append({"tool": "get_summary", "params": {}})
        if is_afford and nums:
            steps.append({"tool": "_decide", "params": {"ask": float(nums[-1])}})
        if not steps:
            steps.append({"tool": "get_summary", "params": {}})
        return steps


# ========== AGENT ==========
class BudgetAgent:
    def __init__(self, monthly_budget=10000.0):
        self.memory = BudgetMemory(monthly_budget)
        self.tools = BudgetTools(self.memory)
        self.planner = Planner(self.memory)
        self.registry = {
            "add_expense": self.tools.add_expense,
            "get_summary": self.tools.get_summary,
        }
    
    def run(self, goal):
        print(f"\n{'='*65}")
        print(f"GOAL: {goal}")
        print(f"{'='*65}")
        
        print("\n[PLAN]")
        steps = self.planner.plan(goal)
        for i, s in enumerate(steps, 1):
            print(f"  Step {i}: {s['tool']}({s.get('params', {})})")
        
        print("\n[ACT]")
        observations = []
        tool_log = []
        
        for i, step in enumerate(steps, 1):
            name = step["tool"]
            params = step.get("params", {})
            print(f"  Step {i}: {name}(...) -> ", end="")
            
            if name == "_decide":
                obs = self._decide_affordability(params["ask"])
            elif name in self.registry:
                try:
                    obs = self.registry[name](**params)
                except Exception as e:
                    obs = f"Error: {e}"
            else:
                obs = f"Unknown tool '{name}'"
            
            print(obs)
            observations.append(obs)
            tool_log.append({"name": name, "params": params})
        
        self.memory.add_turn("user", goal, tool_calls=tool_log, observations=observations)
        
        answer = self._compose_answer(goal, observations)
        self.memory.add_turn("assistant", answer)
        print(f"\n[ANSWER] {answer}")
        return answer
    
    def _decide_affordability(self, amount):
        spent = self.memory.get_total_spent()
        left = self.memory.monthly_budget - spent
        if left >= amount:
            return f"DECISION: YES. You have ₹{left:.2f} left; after this you'd have ₹{left - amount:.2f}."
        return f"DECISION: NO. You only have ₹{left:.2f} left. You need ₹{amount - left:.2f} more."
    
    def _compose_answer(self, goal, observations):
        if len(self.memory.turns) > 2:
            return f"Keeping your past spending in mind: {' | '.join(observations)}"
        return " | ".join(observations)


def demo():
    print("="*65)
    print("DEMO: Personal Budget Assistant (Topic T1)")
    print("="*65)
    
    agent = BudgetAgent(monthly_budget=8000)
    agent.run("I spent ₹500 on groceries today")
    agent.run("Can I afford a ₹2000 trip this weekend?")
    agent.run("I bought a textbook for ₹1200. Can I still afford that ₹2000 trip?")
    
    print("\n" + "="*65)
    print("MEMORY PROOF (last 3 turns):")
    print("="*65)
    for t in agent.memory.turns[-3:]:
        print(f"\n{t['role'].upper()}: {t['content']}")
        print(f"  Observations: {t['observations']}")


if __name__ == "__main__":
    demo()