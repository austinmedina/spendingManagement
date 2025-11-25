"""
Analytics Service for Enhanced Dashboard
Provides insights, trends, and predictions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict
from models import TransactionModel, BudgetModel, RecurringModel
import math

class AnalyticsService:
    """Service for dashboard analytics and insights"""
    
    def __init__(self):
        self.transaction_model = TransactionModel()
        self.budget_model = BudgetModel()
        self.recurring_model = RecurringModel()
    
    def get_enhanced_dashboard_data(self, person: str, 
                                   group_id: str = '') -> Dict:
        """Get comprehensive dashboard data with insights"""
        
        # Get transactions
        if group_id:
            transactions = [t for t in self.transaction_model.read_all() 
                          if t.get('group_id') == group_id]
        else:
            transactions = self.transaction_model.filter({'person': person})
        
        # Time ranges
        now = datetime.now()
        current_month = now.strftime('%Y-%m')
        last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        
        # Basic statistics
        basic_stats = self._calculate_basic_stats(transactions, current_month)
        
        # Trends
        trends = self._calculate_trends(transactions)
        
        # Top categories
        top_categories = self._get_top_categories(transactions, current_month)
        
        # Top stores
        top_stores = self._get_top_stores(transactions, current_month)
        
        # Spending patterns
        patterns = self._analyze_spending_patterns(transactions)
        
        # Budget performance
        budget_performance = self._calculate_budget_performance(person, transactions, current_month)
        
        # Predictions
        predictions = self._predict_month_end(transactions, current_month)
        
        # Insights
        insights = self._generate_insights(
            transactions, basic_stats, trends, 
            budget_performance, patterns
        )
        
        # Recurring impact
        recurring_impact = self._calculate_recurring_impact(person)
        
        return {
            'basic_stats': basic_stats,
            'trends': trends,
            'top_categories': top_categories,
            'top_stores': top_stores,
            'patterns': patterns,
            'budget_performance': budget_performance,
            'predictions': predictions,
            'insights': insights,
            'recurring_impact': recurring_impact
        }
    
    def _calculate_basic_stats(self, transactions: List[Dict], 
                              current_month: str) -> Dict:
        """Calculate basic statistics"""
        total_income = 0
        total_expenses = 0
        current_month_income = 0
        current_month_expenses = 0
        
        for t in transactions:
            price = float(t.get('price', 0))
            is_income = t.get('type') == 'income'
            
            if is_income:
                total_income += price
                if t['date'].startswith(current_month):
                    current_month_income += price
            else:
                total_expenses += price
                if t['date'].startswith(current_month):
                    current_month_expenses += price
        
        return {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'current_month_income': current_month_income,
            'current_month_expenses': current_month_expenses,
            'balance': total_income - total_expenses,
            'current_month_balance': current_month_income - current_month_expenses
        }
    
    def _calculate_trends(self, transactions: List[Dict]) -> Dict:
        """Calculate spending trends"""
        # Group by month
        monthly_data = defaultdict(lambda: {'income': 0, 'expenses': 0})
        
        for t in transactions:
            month = t['date'][:7]
            price = float(t.get('price', 0))
            
            if t.get('type') == 'income':
                monthly_data[month]['income'] += price
            else:
                monthly_data[month]['expenses'] += price
        
        # Get last 6 months
        months = sorted(monthly_data.keys())[-6:]
        
        # Calculate month-over-month changes
        if len(months) >= 2:
            current = months[-1]
            previous = months[-2]
            
            expense_change = ((monthly_data[current]['expenses'] - monthly_data[previous]['expenses']) 
                            / monthly_data[previous]['expenses'] * 100) if monthly_data[previous]['expenses'] > 0 else 0
            
            income_change = ((monthly_data[current]['income'] - monthly_data[previous]['income']) 
                           / monthly_data[previous]['income'] * 100) if monthly_data[previous]['income'] > 0 else 0
        else:
            expense_change = 0
            income_change = 0
        
        return {
            'monthly_labels': months,
            'monthly_expenses': [monthly_data[m]['expenses'] for m in months],
            'monthly_income': [monthly_data[m]['income'] for m in months],
            'expense_change_pct': round(expense_change, 1),
            'income_change_pct': round(income_change, 1),
            'trend_direction': 'up' if expense_change > 5 else 'down' if expense_change < -5 else 'stable'
        }
    
    def _get_top_categories(self, transactions: List[Dict], 
                           current_month: str, limit: int = 5) -> List[Dict]:
        """Get top spending categories"""
        category_totals = defaultdict(float)
        
        for t in transactions:
            if t['date'].startswith(current_month) and t.get('type') != 'income':
                category_totals[t.get('category', 'Other')] += float(t.get('price', 0))
        
        # Sort and get top N
        sorted_categories = sorted(category_totals.items(), 
                                  key=lambda x: x[1], reverse=True)[:limit]
        
        return [{'category': cat, 'amount': amt} for cat, amt in sorted_categories]
    
    def _get_top_stores(self, transactions: List[Dict], 
                       current_month: str, limit: int = 5) -> List[Dict]:
        """Get top stores by spending"""
        store_totals = defaultdict(float)
        
        for t in transactions:
            if t['date'].startswith(current_month) and t.get('type') != 'income':
                store = t.get('store', 'Unknown')
                if store:
                    store_totals[store] += float(t.get('price', 0))
        
        sorted_stores = sorted(store_totals.items(), 
                             key=lambda x: x[1], reverse=True)[:limit]
        
        return [{'store': store, 'amount': amt} for store, amt in sorted_stores]
    
    def _analyze_spending_patterns(self, transactions: List[Dict]) -> Dict:
        """Analyze spending patterns"""
        day_of_week = defaultdict(float)
        time_of_day = defaultdict(float)
        
        for t in transactions:
            if t.get('type') != 'income':
                # Day of week analysis
                date = datetime.strptime(t['date'], '%Y-%m-%d')
                day_name = date.strftime('%A')
                day_of_week[day_name] += float(t.get('price', 0))
        
        # Get average spending per day
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        avg_by_day = [day_of_week.get(day, 0) for day in days]
        
        # Find highest spending day
        if avg_by_day:
            max_day_index = avg_by_day.index(max(avg_by_day))
            highest_day = days[max_day_index]
        else:
            highest_day = 'N/A'
        
        return {
            'spending_by_day': dict(zip(days, avg_by_day)),
            'highest_spending_day': highest_day,
            'weekend_vs_weekday': self._compare_weekend_weekday(day_of_week)
        }
    
    def _compare_weekend_weekday(self, day_of_week: Dict) -> Dict:
        """Compare weekend vs weekday spending"""
        weekday_total = sum(day_of_week.get(day, 0) 
                           for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'])
        weekend_total = sum(day_of_week.get(day, 0) 
                           for day in ['Saturday', 'Sunday'])
        
        weekday_avg = weekday_total / 5 if weekday_total > 0 else 0
        weekend_avg = weekend_total / 2 if weekend_total > 0 else 0
        
        return {
            'weekday_avg': round(weekday_avg, 2),
            'weekend_avg': round(weekend_avg, 2),
            'difference': round(weekend_avg - weekday_avg, 2)
        }
    
    def _calculate_budget_performance(self, person: str, 
                                     transactions: List[Dict], 
                                     current_month: str) -> Dict:
        """Calculate budget performance"""
        budgets = self.budget_model.get_by_person(person)
        performance = {
            'categories': [],
            'overall_status': 'good',
            'categories_over': 0,
            'categories_under': 0
        }
        
        for budget in budgets:
            category = budget['category']
            limit = float(budget['amount'])
            
            # Calculate spending
            category_transactions = [t for t in transactions 
                                   if t['date'].startswith(current_month) 
                                   and t.get('category') == category
                                   and t.get('type') != 'income']
            
            spent = sum(float(t.get('price', 0)) for t in category_transactions)
            percentage = (spent / limit * 100) if limit > 0 else 0
            
            status = 'good' if percentage < 75 else 'warning' if percentage < 90 else 'critical'
            
            if percentage >= 100:
                performance['categories_over'] += 1
            else:
                performance['categories_under'] += 1
            
            performance['categories'].append({
                'category': category,
                'spent': spent,
                'limit': limit,
                'percentage': round(percentage, 1),
                'status': status
            })
        
        # Overall status
        if performance['categories_over'] > 0:
            performance['overall_status'] = 'critical'
        elif any(c['status'] == 'warning' for c in performance['categories']):
            performance['overall_status'] = 'warning'
        
        return performance
    
    def _predict_month_end(self, transactions: List[Dict], 
                          current_month: str) -> Dict:
        """Predict end-of-month spending"""
        now = datetime.now()
        days_elapsed = now.day
        days_in_month = (now.replace(month=now.month % 12 + 1, day=1) - timedelta(days=1)).day
        
        # Current month spending
        current_spending = sum(float(t.get('price', 0)) 
                             for t in transactions 
                             if t['date'].startswith(current_month) 
                             and t.get('type') != 'income')
        
        # Daily average
        daily_avg = current_spending / days_elapsed if days_elapsed > 0 else 0
        
        # Projected total
        projected_total = daily_avg * days_in_month
        
        # Get last month for comparison
        last_month = (now.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
        last_month_total = sum(float(t.get('price', 0)) 
                              for t in transactions 
                              if t['date'].startswith(last_month) 
                              and t.get('type') != 'income')
        
        return {
            'current_spending': round(current_spending, 2),
            'daily_average': round(daily_avg, 2),
            'projected_month_end': round(projected_total, 2),
            'last_month_total': round(last_month_total, 2),
            'vs_last_month': round(projected_total - last_month_total, 2),
            'days_remaining': days_in_month - days_elapsed
        }
    
    def _generate_insights(self, transactions: List[Dict], 
                          basic_stats: Dict, trends: Dict, 
                          budget_performance: Dict, 
                          patterns: Dict) -> List[Dict]:
        """Generate actionable insights"""
        insights = []
        
        # Spending trend insight
        if trends['trend_direction'] == 'up' and abs(trends['expense_change_pct']) > 10:
            insights.append({
                'type': 'warning',
                'icon': '📈',
                'title': 'Spending Increase Detected',
                'message': f'Your spending is up {abs(trends["expense_change_pct"]):.1f}% from last month',
                'action': 'Review your recent expenses to identify areas to cut back'
            })
        elif trends['trend_direction'] == 'down' and abs(trends['expense_change_pct']) > 10:
            insights.append({
                'type': 'success',
                'icon': '📉',
                'title': 'Great Job!',
                'message': f'You\'ve reduced spending by {abs(trends["expense_change_pct"]):.1f}% from last month',
                'action': 'Keep up the good work!'
            })
        
        # Budget insight
        if budget_performance['categories_over'] > 0:
            insights.append({
                'type': 'critical',
                'icon': '🚨',
                'title': 'Budget Exceeded',
                'message': f'{budget_performance["categories_over"]} categor{"y" if budget_performance["categories_over"] == 1 else "ies"} over budget',
                'action': 'Consider adjusting your budget or reducing spending'
            })
        
        # Spending pattern insight
        weekend_vs_weekday = patterns['weekend_vs_weekday']
        if weekend_vs_weekday['weekend_avg'] > weekend_vs_weekday['weekday_avg'] * 1.5:
            insights.append({
                'type': 'info',
                'icon': '🎉',
                'title': 'Weekend Spending Pattern',
                'message': f'You spend ${weekend_vs_weekday["difference"]:.2f} more on weekends',
                'action': 'Consider planning weekend activities with a budget'
            })
        
        # High spending day
        if patterns['highest_spending_day'] != 'N/A':
            insights.append({
                'type': 'info',
                'icon': '📅',
                'title': f'{patterns["highest_spending_day"]} is Your Highest Spending Day',
                'message': 'Be mindful of spending on this day',
                'action': 'Set daily spending limits for high-spending days'
            })
        
        return insights
    
    def _calculate_recurring_impact(self, person: str) -> Dict:
        """Calculate impact of recurring transactions"""
        recurring_items = [r for r in self.recurring_model.get_active() 
                          if r['person'] == person]
        
        monthly_recurring = 0
        
        for item in recurring_items:
            amount = float(item['price'])
            frequency = item['frequency']
            
            # Convert to monthly
            if frequency == 'daily':
                monthly_recurring += amount * 30
            elif frequency == 'weekly':
                monthly_recurring += amount * 4
            elif frequency == 'biweekly':
                monthly_recurring += amount * 2
            elif frequency == 'monthly':
                monthly_recurring += amount
            elif frequency == 'yearly':
                monthly_recurring += amount / 12
        
        return {
            'monthly_total': round(monthly_recurring, 2),
            'count': len(recurring_items),
            'annual_total': round(monthly_recurring * 12, 2)
        }
    
    def get_category_trends(self, person: str, category: str, 
                           months: int = 6) -> Dict:
        """Get trends for a specific category"""
        transactions = self.transaction_model.filter({
            'person': person,
            'category': category,
            'type': 'expense'
        })
        
        # Group by month
        monthly_data = defaultdict(float)
        for t in transactions:
            month = t['date'][:7]
            monthly_data[month] += float(t.get('price', 0))
        
        # Get last N months
        all_months = sorted(monthly_data.keys())[-months:]
        amounts = [monthly_data.get(m, 0) for m in all_months]
        
        # Calculate trend
        if len(amounts) >= 2:
            avg = sum(amounts) / len(amounts)
            trend = 'increasing' if amounts[-1] > avg else 'decreasing'
        else:
            avg = amounts[0] if amounts else 0
            trend = 'stable'
        
        return {
            'months': all_months,
            'amounts': amounts,
            'average': round(avg, 2),
            'trend': trend
        }


# Singleton instance
analytics_service = AnalyticsService()