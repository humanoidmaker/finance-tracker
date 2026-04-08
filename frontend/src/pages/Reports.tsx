import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line, AreaChart, Area,
} from 'recharts';
import { BarChart3, Loader2, TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight } from 'lucide-react';
import api from '@/lib/api';
import { formatCurrency, formatDate } from '@/lib/utils';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16'];

export default function Reports() {
  const [loading, setLoading] = useState(true);
  const [transactions, setTransactions] = useState<any[]>([]);
  const [categories, setCategories] = useState<any[]>([]);
  const [budgets, setBudgets] = useState<any[]>([]);
  const [accounts, setAccounts] = useState<any[]>([]);
  const [dateRange, setDateRange] = useState('30');

  useEffect(() => {
    Promise.all([
      api.get('/transactions').then(r => r.data.transactions || []).catch(() => []),
      api.get('/categories').then(r => r.data.categories || []).catch(() => []),
      api.get('/budgets').then(r => r.data.budgets || []).catch(() => []),
      api.get('/accounts').then(r => r.data.accounts || []).catch(() => []),
    ]).then(([t, c, b, a]) => {
      setTransactions(t);
      setCategories(c);
      setBudgets(b);
      setAccounts(a);
    }).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex justify-center py-12"><Loader2 className="h-8 w-8 animate-spin text-accent" /></div>;

  const daysBack = parseInt(dateRange);
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - daysBack);
  const filtered = transactions.filter(t => new Date(t.date || t.created_at) >= cutoff);

  // Income vs Expense totals
  const totalIncome = filtered.filter(t => t.type === 'income').reduce((s, t) => s + (t.amount || 0), 0);
  const totalExpense = filtered.filter(t => t.type === 'expense').reduce((s, t) => s + (t.amount || 0), 0);
  const netSavings = totalIncome - totalExpense;

  // Income vs Expense by day
  const dailyMap: Record<string, { income: number; expense: number }> = {};
  const today = new Date();
  for (let i = daysBack - 1; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    dailyMap[d.toISOString().slice(0, 10)] = { income: 0, expense: 0 };
  }
  filtered.forEach(t => {
    const day = (t.date || t.created_at || '').slice(0, 10);
    if (dailyMap[day]) {
      if (t.type === 'income') dailyMap[day].income += t.amount || 0;
      else dailyMap[day].expense += t.amount || 0;
    }
  });
  const trendData = Object.entries(dailyMap).map(([date, vals]) => ({
    date: date.slice(5),
    Income: vals.income,
    Expense: vals.expense,
  }));

  // Expense by category
  const expByCat: Record<string, number> = {};
  filtered.filter(t => t.type === 'expense').forEach(t => {
    const cat = t.category_name || t.category || 'Uncategorized';
    expByCat[cat] = (expByCat[cat] || 0) + (t.amount || 0);
  });
  const categoryExpenseData = Object.entries(expByCat)
    .map(([name, value]) => ({ name, value: Math.round(value) }))
    .sort((a, b) => b.value - a.value);

  // Budget vs Actual
  const budgetData = budgets.map(b => {
    const spent = filtered.filter(t => t.type === 'expense' && (t.category_id === b.category_id || t.category === b.category_name))
      .reduce((s, t) => s + (t.amount || 0), 0);
    return {
      name: b.category_name || b.name || 'Unknown',
      budget: b.amount || b.limit || 0,
      spent: Math.round(spent),
    };
  }).filter(b => b.budget > 0);

  // Account balances
  const accountData = accounts.map(a => ({
    name: a.name || 'Account',
    balance: a.balance || 0,
  }));

  // Top expenses
  const topExpenses = filtered
    .filter(t => t.type === 'expense')
    .sort((a, b) => (b.amount || 0) - (a.amount || 0))
    .slice(0, 8);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <BarChart3 className="h-6 w-6 text-accent" /> Reports
        </h2>
        <select value={dateRange} onChange={e => setDateRange(e.target.value)}
          className="px-3 py-2 border rounded-lg text-sm outline-none focus:ring-2 focus:ring-accent/30">
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
          <option value="365">Last year</option>
        </select>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2">
            <ArrowUpRight className="h-4 w-4 text-emerald-500" />
            <span className="text-sm text-gray-500">Income</span>
          </div>
          <p className="text-2xl font-bold text-emerald-600 mt-1">{formatCurrency(totalIncome)}</p>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <div className="flex items-center gap-2">
            <ArrowDownRight className="h-4 w-4 text-red-500" />
            <span className="text-sm text-gray-500">Expense</span>
          </div>
          <p className="text-2xl font-bold text-red-600 mt-1">{formatCurrency(totalExpense)}</p>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <span className="text-sm text-gray-500">Net Savings</span>
          <p className={`text-2xl font-bold mt-1 ${netSavings >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
            {formatCurrency(netSavings)}
          </p>
        </div>
        <div className="bg-white rounded-xl border p-4">
          <span className="text-sm text-gray-500">Transactions</span>
          <p className="text-2xl font-bold text-gray-900 mt-1">{filtered.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Income vs Expense Trend */}
        <div className="bg-white rounded-xl border p-5 lg:col-span-2">
          <h3 className="font-semibold text-gray-900 mb-4">Income vs Expense Trend</h3>
          <ResponsiveContainer width="100%" height={280}>
            <AreaChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" fontSize={11} />
              <YAxis fontSize={11} tickFormatter={(v: number) => `${(v / 1000).toFixed(0)}k`} />
              <Tooltip formatter={(val: number) => formatCurrency(val)} />
              <Legend />
              <Area type="monotone" dataKey="Income" stroke="#10b981" fill="#10b981" fillOpacity={0.1} strokeWidth={2} />
              <Area type="monotone" dataKey="Expense" stroke="#ef4444" fill="#ef4444" fillOpacity={0.1} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Expense by Category Pie */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Expense by Category</h3>
          {categoryExpenseData.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No expense data.</p>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={categoryExpenseData} cx="50%" cy="50%" outerRadius={90} dataKey="value"
                  label={({ name, percent }) => `${name.length > 10 ? name.slice(0, 10) + '..' : name} ${(percent * 100).toFixed(0)}%`}>
                  {categoryExpenseData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip formatter={(val: number) => formatCurrency(val)} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Budget vs Actual */}
        <div className="bg-white rounded-xl border p-5">
          <h3 className="font-semibold text-gray-900 mb-4">Budget vs Actual</h3>
          {budgetData.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-8">No budgets set up.</p>
          ) : (
            <div className="space-y-3">
              {budgetData.map((b, i) => {
                const pct = b.budget > 0 ? Math.round((b.spent / b.budget) * 100) : 0;
                const over = pct > 100;
                return (
                  <div key={i}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-700">{b.name}</span>
                      <span className={`text-xs font-medium ${over ? 'text-red-600' : 'text-gray-500'}`}>
                        {formatCurrency(b.spent)} / {formatCurrency(b.budget)} ({pct}%)
                      </span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${over ? 'bg-red-500' : pct > 80 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                        style={{ width: `${Math.min(pct, 100)}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Top Expenses */}
        <div className="bg-white rounded-xl border p-5 lg:col-span-2">
          <h3 className="font-semibold text-gray-900 mb-4">Top Expenses</h3>
          {topExpenses.length === 0 ? (
            <p className="text-sm text-gray-400 text-center py-6">No expenses recorded.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-gray-500">
                    <th className="pb-2 font-medium">Date</th>
                    <th className="pb-2 font-medium">Description</th>
                    <th className="pb-2 font-medium">Category</th>
                    <th className="pb-2 font-medium">Account</th>
                    <th className="pb-2 font-medium text-right">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {topExpenses.map((t, i) => (
                    <tr key={t.id || i} className="border-b last:border-0">
                      <td className="py-2 text-gray-500">{formatDate(t.date || t.created_at)}</td>
                      <td className="py-2 font-medium">{t.description || t.note || '-'}</td>
                      <td className="py-2">
                        <span className="px-2 py-0.5 bg-gray-100 text-gray-600 rounded text-xs">
                          {t.category_name || t.category || '-'}
                        </span>
                      </td>
                      <td className="py-2 text-gray-500">{t.account_name || '-'}</td>
                      <td className="py-2 text-right font-medium text-red-600">{formatCurrency(t.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
