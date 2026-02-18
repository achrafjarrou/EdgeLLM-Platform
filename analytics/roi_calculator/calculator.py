# -*- coding: utf-8 -*-
"""
EdgeLLM ROI Calculator
Calculate total cost of ownership vs cloud alternatives
"""
from dataclasses import dataclass
from typing import Dict
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class EdgeLLMCosts:
    """On-premise deployment costs"""
    hardware_cost: float  # One-time
    electricity_monthly: float
    maintenance_monthly: float
    
    def annual_recurring(self) -> float:
        return (self.electricity_monthly + self.maintenance_monthly) * 12
    
    def first_year_total(self) -> float:
        return self.hardware_cost + self.annual_recurring()


@dataclass
class CloudAPICosts:
    """Cloud API costs"""
    cost_per_1k_tokens: float
    monthly_tokens: int
    
    def monthly_cost(self) -> float:
        return (self.monthly_tokens / 1000) * self.cost_per_1k_tokens
    
    def annual_cost(self) -> float:
        return self.monthly_cost() * 12


def calculate_roi(
    edgellm: EdgeLLMCosts,
    cloud: CloudAPICosts,
    years: int = 5
) -> Dict:
    """
    Calculate ROI over time period
    
    Returns:
        Dict with year-by-year comparison
    """
    results = {}
    
    for year in range(1, years + 1):
        if year == 1:
            edgellm_cost = edgellm.first_year_total()
        else:
            edgellm_cost = edgellm.annual_recurring()
        
        cloud_cost = cloud.annual_cost()
        
        savings = cloud_cost - edgellm_cost
        cumulative_savings = sum(
            cloud.annual_cost() - (edgellm.first_year_total() if y == 1 else edgellm.annual_recurring())
            for y in range(1, year + 1)
        )
        
        results[year] = {
            'edgellm_cost': edgellm_cost,
            'cloud_cost': cloud_cost,
            'annual_savings': savings,
            'cumulative_savings': cumulative_savings,
            'roi_percent': (cumulative_savings / edgellm.hardware_cost * 100) if year == 1 else None
        }
    
    return results


def display_roi_analysis(results: Dict):
    """Display ROI analysis"""
    table = Table(title="5-Year Total Cost of Ownership (TCO) Analysis")
    
    table.add_column("Year", style="cyan")
    table.add_column("EdgeLLM Cost", justify="right")
    table.add_column("Cloud API Cost", justify="right")
    table.add_column("Annual Savings", justify="right", style="green")
    table.add_column("Cumulative Savings", justify="right", style="bold green")
    
    for year, data in results.items():
        table.add_row(
            f"Year {year}",
            f"�{data['edgellm_cost']:,.0f}",
            f"�{data['cloud_cost']:,.0f}",
            f"�{data['annual_savings']:,.0f}",
            f"�{data['cumulative_savings']:,.0f}"
        )
    
    console.print("\n")
    console.print(table)
    
    # Summary
    final_year = max(results.keys())
    total_savings = results[final_year]['cumulative_savings']
    
    console.print(f"\n[bold green]5-Year Total Savings: �{total_savings:,.0f}[/bold green]")
    console.print(f"[dim]Equivalent to {(total_savings / results[1]['cloud_cost'] * 100):.0f}% of Year 1 cloud costs[/dim]\n")


if __name__ == "__main__":
    console.print("[bold cyan]EdgeLLM ROI Calculator[/bold cyan]\n")
    
    # Example: Mid-size company
    console.print("[bold]Scenario: Mid-size Healthcare Provider[/bold]")
    console.print("� 500 staff")
    console.print("� 5M tokens/month (moderate usage)")
    console.print("� HIPAA compliance required\n")
    
    edgellm = EdgeLLMCosts(
        hardware_cost=2500,      # Mid-range server
        electricity_monthly=20,
        maintenance_monthly=50
    )
    
    cloud = CloudAPICosts(
        cost_per_1k_tokens=0.05,  # Conservative average (input+output)
        monthly_tokens=5_000_000
    )
    
    results = calculate_roi(edgellm, cloud, years=5)
    display_roi_analysis(results)
    
    # Payback period
    for year, data in results.items():
        if data['cumulative_savings'] >= edgellm.hardware_cost:
            console.print(f"[yellow]Payback Period: {year} year(s)[/yellow]\n")
            break
